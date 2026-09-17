from __future__ import annotations

import weakref

from pathlib import Path

from PySide6.QtCore import Slot, Qt, QUrl
from PySide6.QtGui import QAction, QActionGroup, QCursor, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import QComboBox, QFileDialog, QLineEdit, QMessageBox, QPlainTextEdit, QSlider, QToolTip
from ...metadata import APP_VERSION
from ...core import CRASH_REPORT_FILE, DEFAULT_OUTPUT, resolve_executable
from ...i18n import tr
from ...logging_utils import ERROR_LOG_FILE, tail_error_log
from ...diagnostics import create_support_bundle
from ..accessibility import announce, configure_accessible, focus_table_row
from ..help_center import QtHelpCenter
from ..localized_context_menu import install_localized_text_context_menu

class AccessibilityUiMixin:
    """Accessibility Ui behavior for :class:`AudioKnigiQtWindow`."""

    def _install_localized_text_context_menus(self) -> None:
        window_ref = weakref.ref(self)

        def language_getter() -> str:
            window = window_ref()
            return str(getattr(window, "language", "ru") or "ru") if window is not None else "ru"

        for widget_type in (QLineEdit, QPlainTextEdit):
            for widget in self.findChildren(widget_type):
                install_localized_text_context_menu(widget, language_getter)

    def _current_help_topic(self) -> str:
        if self.current_ui_mode() == "easy":
            return "start"
        topics = {
            self.TAB_BOOK: "book",
            self.TAB_SEARCH: "search",
            self.TAB_QUEUE: "queue",
            self.TAB_HISTORY: "history",
            self.TAB_SETTINGS: "settings",
            self.TAB_PLAYER: "player",
        }
        return topics.get(self.tabs.currentIndex(), "start")

    def show_context_help(self, _checked=False, *, topic: str | None = None):
        dialog = QtHelpCenter(self, language=self.language, topic=topic or self._current_help_topic(), copy_report_callback=self.copy_last_crash_report)
        dialog.exec()

    def copy_last_crash_report(self) -> str:
        crash_text = ""
        try:
            if CRASH_REPORT_FILE.is_file():
                crash_text = CRASH_REPORT_FILE.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            crash_text = ""
        errors_text = tail_error_log(200).strip()
        parts = []
        if crash_text:
            parts.append("=== last_crash_report.txt ===\n" + crash_text)
        if errors_text:
            parts.append("=== errors.log (last 200 lines) ===\n" + errors_text)
        if not parts:
            parts.append(self._rt("Последний отчёт об ошибке отсутствует."))
        text = "\n\n".join(parts)
        self._set_clipboard_text(text)
        self.set_status("Отчёт об ошибке скопирован в буфер обмена.")
        return text

    def open_error_log(self) -> None:
        try:
            ERROR_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            ERROR_LOG_FILE.touch(exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(ERROR_LOG_FILE)))
        except Exception as exc:
            self.set_status("Ошибка: " + str(exc), assertive=True)

    def _dependency_status_text(self) -> str:
        ffmpeg = resolve_executable("ffmpeg")
        ffprobe = resolve_executable("ffprobe")
        try:
            import mutagen  # noqa: F401
            id3 = "OK"
        except Exception:
            id3 = "нет"
        try:
            import playwright  # noqa: F401
            pw = "OK"
        except Exception:
            pw = "нет"
        missing = self._l("нет")
        unavailable = self._l("недоступен")
        return "\n".join((
            f"FFmpeg: {'OK — ' + str(ffmpeg) if ffmpeg else missing}",
            f"FFprobe: {'OK — ' + str(ffprobe) if ffprobe else missing}",
            f"Playwright: {pw if pw == 'OK' else missing}",
            f"Mutagen/ID3: {id3 if id3 == 'OK' else missing}",
            self._l("Плеер: Qt Multimedia"),
            self._l("Обложки: Qt image codecs"),
            self._l("Системный трей: {state}", state=("OK" if self._tray_available() else unavailable)),
            self._l("Перетаскивание: Qt native"),
        ))

    def show_dependency_status(self):
        self._show_message(QMessageBox.Icon.Information, "Зависимости", self._dependency_status_text())

    def screen_reader_self_test(self):
        from ..accessibility_audit import audit_accessibility_window
        result = audit_accessibility_window(self)
        self._show_message(QMessageBox.Icon.Information if result.ok else QMessageBox.Icon.Warning, "Проверка доступности", result.report())

    def open_last_completed_folder(self):
        folder = Path(self.last_completed_folder).expanduser() if self.last_completed_folder else None
        if not folder or not folder.exists():
            self.set_status("Нет последней завершённой книги.", assertive=True)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def listen_last_completed_book(self):
        folder = Path(self.last_completed_folder).expanduser() if self.last_completed_folder else None
        if not folder or not folder.exists():
            self.set_status("Нет последней завершённой книги.", assertive=True)
            return
        self.tabs.setCurrentIndex(self.TAB_PLAYER)
        self.set_ui_mode("advanced", persist=False)
        self.load_book_folder(folder, autoplay=True)

    def _wire_live_accessibility_feedback(self) -> None:
        """Add screen-reader feedback without custom focus interception.

        Qt exposes the widgets natively.  These signal-only announcements fill the
        gaps observed with NVDA on Windows: popup combo navigation, table row
        summaries and numeric player controls.  No custom focus-interception layer is
        installed, so the Phase 8 recursion/focus guarantees remain intact.
        """
        for combo in self.findChildren(QComboBox):
            combo_ref = weakref.ref(combo)

            def announce_highlighted(text, ref=combo_ref):
                current = ref()
                if current is not None:
                    try:
                        self._announce_combo_value(current, text, selected=False)
                    except RuntimeError:
                        pass

            def announce_activated(text, ref=combo_ref):
                current = ref()
                if current is not None:
                    try:
                        self._announce_combo_value(current, text, selected=True)
                    except RuntimeError:
                        pass

            combo.textHighlighted.connect(announce_highlighted)
            combo.textActivated.connect(announce_activated)
        self.player_volume_slider.valueChanged.connect(self._announce_player_volume)
        self.player_seek_slider.valueChanged.connect(self._announce_player_seek_value)

    def _announce_combo_value(self, combo: QComboBox, text: str, *, selected: bool) -> None:
        if not combo.isVisible() or not combo.isEnabled():
            return
        label = str(combo.accessibleName() or self._l("Список")).strip()
        value = str(text or combo.currentText() or "").strip()
        if not value:
            return
        prefix = self._l("Выбрано") if selected else label
        announce(combo, self._l("{prefix}: {value}", prefix=prefix, value=value))
        combo.setAccessibleDescription(self._l("Текущее значение: {value}", value=value))

    @Slot(int)
    def _announce_player_volume(self, value: int) -> None:
        percent = max(0, min(100, int(value)))
        description = self._l("Текущая громкость: {value}%", value=percent)
        self.player_volume_slider.setAccessibleDescription(description)
        self.player_volume_slider.setToolTip(description)
        if hasattr(self, "player_volume_value_label"):
            self.player_volume_value_label.setText(f"{percent}%")
            self.player_volume_value_label.setAccessibleDescription(description)
        if self.player_volume_slider.hasFocus():
            announce(self.player_volume_slider, description)

    def _show_volume_tooltip(self, slider: QSlider, value: int) -> None:
        percent = max(0, min(100, int(value)))
        text = self._l("Текущая громкость: {value}%", value=percent)
        slider.setToolTip(text)
        QToolTip.showText(QCursor.pos(), text, slider)

    @Slot(int)
    def _event_sound_volume_changed(self, value: int) -> None:
        percent = max(0, min(100, int(value)))
        description = self._l("Текущая громкость: {value}%", value=percent)
        self.event_sound_volume_slider.setAccessibleDescription(description)
        self.event_sound_volume_slider.setToolTip(description)
        if hasattr(self, "event_sound_volume_value_label"):
            self.event_sound_volume_value_label.setText(f"{percent}%")
            self.event_sound_volume_value_label.setAccessibleDescription(description)
        if self.event_sound_manager is not None:
            self.event_sound_manager.configure(volume=percent / 100.0)

    @Slot(int)
    def _announce_player_seek_value(self, value: int) -> None:
        seconds = max(0, int(value))
        self.player_seek_slider.setAccessibleDescription(
            self._l(
                "Текущая позиция {seconds} секунд. Диапазон до {maximum} секунд",
                seconds=seconds, maximum=max(0, self.player_seek_slider.maximum()),
            )
        )
        if self.player_seek_slider.hasFocus() and not self._player_seek_active:
            announce(self.player_seek_slider, self._l("Позиция {seconds} секунд", seconds=seconds))

    def _show_message(self, icon: QMessageBox.Icon, title: str, text: str) -> QMessageBox.StandardButton:
        title = self._rt(str(title or ""))
        text = self._rt(str(text or ""))
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setDefaultButton(QMessageBox.StandardButton.Ok)
        box.setEscapeButton(QMessageBox.StandardButton.Ok)
        box.setWindowModality(Qt.WindowModality.ApplicationModal)
        box.setModal(True)
        configure_accessible(box, name=title, description=text, identifier="modal_message")
        ok_button = box.button(QMessageBox.StandardButton.Ok)
        if ok_button is not None:
            configure_accessible(ok_button, name=self._l("Закрыть сообщение"), identifier="modal_ok")
        box.exec()
        return box.standardButton(box.clickedButton())

    def _ask_yes_no(self, title: str, text: str, *, default_yes: bool = False) -> QMessageBox.StandardButton:
        title = self._rt(str(title or ""))
        text = self._rt(str(text or ""))
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        default = QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No
        box.setDefaultButton(default)
        box.setEscapeButton(QMessageBox.StandardButton.No)
        box.setWindowModality(Qt.WindowModality.ApplicationModal)
        box.setModal(True)
        configure_accessible(box, name=title, description=text, identifier="modal_question")
        yes_button = box.button(QMessageBox.StandardButton.Yes)
        no_button = box.button(QMessageBox.StandardButton.No)
        if yes_button is not None:
            configure_accessible(yes_button, name=self._l("Да"), identifier="modal_yes")
        if no_button is not None:
            configure_accessible(no_button, name=self._l("Нет, безопасное действие"), identifier="modal_no")
        box.exec()
        return box.standardButton(box.clickedButton())

    @Slot(bool)
    def _toggle_session_log(self, visible: bool):
        self.session_log_group.setVisible(bool(visible))
        self.log_toggle_button.setText(self._l("Скрыть технический журнал ▴" if visible else "Показать технический журнал ▾"))

    @Slot()
    def create_diagnostic_bundle(self):
        default_name = f"AudioKnigi_Diagnostics_{APP_VERSION}.zip"
        start = str(Path.home() / default_name)
        path, _selected = QFileDialog.getSaveFileName(
            self, self._l("Создать диагностический пакет…"), start, "ZIP (*.zip)"
        )
        if not path:
            return
        try:
            created = create_support_bundle(path, settings=self.settings)
            self.set_status(self._l("Диагностический пакет создан."))
            self._show_message(
                QMessageBox.Icon.Information,
                self._l("Диагностика"),
                str(created),
            )
        except Exception as exc:
            self.set_status(self._l("Не удалось создать диагностический пакет."), assertive=True)
            self._show_message(QMessageBox.Icon.Warning, self._l("Диагностика"), str(exc))

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&" + self._l("Файл"))
        open_book_action = QAction(self._l("Открыть папку с книгой…"), self)
        open_book_action.setShortcut(QKeySequence.StandardKey.Open)
        open_book_action.triggered.connect(self.open_book_folder_dialog)
        file_menu.addAction(open_book_action)
        open_audio_action = QAction(self._l("Открыть отдельный файл…"), self)
        open_audio_action.triggered.connect(self.open_audio_file)
        file_menu.addAction(open_audio_action)
        open_output_action = QAction(self._l("Открыть папку загрузок"), self)
        open_output_action.triggered.connect(self.open_output_folder)
        file_menu.addAction(open_output_action)
        file_menu.addSeparator()
        backup_action = QAction(self._l("Создать резервную копию…"), self)
        backup_action.triggered.connect(self.create_backup)
        restore_action = QAction(self._l("Восстановить резервную копию…"), self)
        restore_action.triggered.connect(self.restore_backup)
        file_menu.addAction(backup_action)
        file_menu.addAction(restore_action)
        file_menu.addSeparator()
        hide_to_tray_action = QAction(self._l("Скрыть в системный трей"), self)
        hide_to_tray_action.setEnabled(self.tray_controller.available)
        hide_to_tray_action.triggered.connect(self.hide_to_tray)
        file_menu.addAction(hide_to_tray_action)
        file_menu.addSeparator()
        exit_action = QAction(self._l("Выход"), self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.request_exit)
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("&" + self._l("Вид"))
        self.view_mode_group = QActionGroup(self)
        self.view_mode_group.setExclusive(True)
        self.view_easy_action = QAction(tr(self.language, "simple"), self)
        self.view_advanced_action = QAction(tr(self.language, "advanced"), self)
        for action in (self.view_easy_action, self.view_advanced_action):
            action.setCheckable(True)
            self.view_mode_group.addAction(action)
        self.view_easy_action.triggered.connect(lambda: self.set_ui_mode("easy"))
        self.view_advanced_action.triggered.connect(lambda: self.set_ui_mode("advanced"))
        view_menu.addAction(self.view_easy_action)
        view_menu.addAction(self.view_advanced_action)

        help_menu = self.menuBar().addMenu("&" + self._l("Справка"))
        help_action = QAction(self._l("Справочный центр"), self)
        help_action.setShortcut(QKeySequence("Shift+F1"))
        help_action.triggered.connect(self.show_context_help)
        help_menu.addAction(help_action)
        shortcuts_action = QAction(self._l("Горячие клавиши"), self)
        shortcuts_action.setShortcut(QKeySequence("F1"))
        shortcuts_action.triggered.connect(lambda: self.show_context_help(topic="shortcuts"))
        help_menu.addAction(shortcuts_action)
        help_menu.addSeparator()

        diagnostics_menu = help_menu.addMenu(self._l("Диагностика"))
        screen_reader = QAction(self._l("Проверить доступность"), self)
        screen_reader.setShortcut(QKeySequence("Ctrl+Shift+F12"))
        screen_reader.triggered.connect(self.screen_reader_self_test)
        diagnostics_menu.addAction(screen_reader)
        dependencies = QAction(self._l("Статус зависимостей"), self)
        dependencies.triggered.connect(self.show_dependency_status)
        diagnostics_menu.addAction(dependencies)
        diagnostics_menu.addSeparator()
        crash = QAction(self._l("Скопировать отчёт об ошибке"), self)
        crash.triggered.connect(self.copy_last_crash_report)
        diagnostics_menu.addAction(crash)
        open_errors = QAction(self._l("Открыть файл ошибок"), self)
        open_errors.triggered.connect(self.open_error_log)
        diagnostics_menu.addAction(open_errors)
        support_bundle = QAction(self._l("Создать диагностический пакет…"), self)
        support_bundle.triggered.connect(self.create_diagnostic_bundle)
        diagnostics_menu.addAction(support_bundle)

        help_menu.addSeparator()
        about = QAction(self._l("О программе"), self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _install_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._focus_book_url)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._focus_search)
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self.start_download_all)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=lambda: self._activate_tab(self.TAB_QUEUE))
        QShortcut(QKeySequence("Ctrl+H"), self, activated=lambda: self._activate_tab(self.TAB_HISTORY))
        QShortcut(QKeySequence("Escape"), self, activated=self.cancel_current_operation)
        # QTabWidget already implements Ctrl+Tab / Ctrl+Shift+Tab for its pages.
        # Registering the same sequences on the window can double-dispatch them.
        QShortcut(QKeySequence("Ctrl+Alt+1"), self, activated=lambda: self._set_quality_shortcut("standard"))
        QShortcut(QKeySequence("Ctrl+Alt+2"), self, activated=lambda: self._set_quality_shortcut("phone"))
        QShortcut(QKeySequence("Ctrl+Alt+3"), self, activated=lambda: self._set_quality_shortcut("normalize"))
        track_space = QShortcut(QKeySequence("Space"), self.track_table, activated=self._toggle_current_track_from_keyboard)
        track_space.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        search_return = QShortcut(QKeySequence("Return"), self.search_table, activated=self.use_selected_result)
        search_return.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        search_enter = QShortcut(QKeySequence("Enter"), self.search_table, activated=self.use_selected_result)
        search_enter.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        easy_search_return = QShortcut(QKeySequence("Return"), self.easy_search_table, activated=self.use_selected_result)
        easy_search_return.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        easy_search_enter = QShortcut(QKeySequence("Enter"), self.easy_search_table, activated=self.use_selected_result)
        easy_search_enter.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        for table in (self.search_table, self.easy_search_table):
            menu_shortcut = QShortcut(QKeySequence("Shift+F10"), table, activated=lambda t=table: self._show_search_context_menu(t, None))
            menu_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        track_menu = QShortcut(QKeySequence("Shift+F10"), self.track_table, activated=lambda: self._show_track_context_menu(None))
        track_menu.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        history_menu = QShortcut(QKeySequence("Shift+F10"), self.history_table, activated=lambda: self._show_history_context_menu(None))
        history_menu.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        queue_menu = QShortcut(QKeySequence("Shift+F10"), self.queue_table, activated=lambda: self._show_queue_context_menu(None))
        queue_menu.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        for number, tab_index in enumerate([self.TAB_BOOK, self.TAB_SEARCH, self.TAB_QUEUE, self.TAB_HISTORY, self.TAB_SETTINGS, self.TAB_PLAYER], start=1):
            QShortcut(QKeySequence(f"Alt+{number}"), self, activated=lambda i=tab_index: self._activate_tab(i))
        for number, tab_index in enumerate([self.TAB_BOOK, self.TAB_SEARCH, self.TAB_QUEUE, self.TAB_HISTORY, self.TAB_SETTINGS, self.TAB_PLAYER], start=1):
            QShortcut(QKeySequence(f"Ctrl+{number}"), self, activated=lambda i=tab_index: self._activate_tab(i))

    def _activate_tab(self, index: int):
        self.set_ui_mode("advanced", persist=False)
        self.tabs.setCurrentIndex(index)
        self.tabs.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _cycle_tab(self, delta: int):
        self._activate_tab((self.tabs.currentIndex() + int(delta)) % self.tabs.count())

    def _set_quality_shortcut(self, preset: str):
        self._set_combo_data(self.quality_combo, preset)
        self._set_combo_data(self.easy_quality_combo, preset)
        self._quality_preset_changed(self.quality_combo.currentIndex())
        self.set_status(f"Качество: {self.quality_combo.currentText()}.", assertive=True)

    @Slot()
    def cancel_current_operation(self):
        if self._search_thread is not None and self._search_thread.isRunning():
            if self._search_cancel is not None:
                self._search_cancel.set()
            self.set_status("Запрошена отмена поиска…", assertive=True)
            return
        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            self.cancel_analysis()
            return
        if self._download_thread is not None and self._download_thread.isRunning():
            if self._active_queue_task_id is not None:
                self.stop_queue()
            else:
                self.cancel_download()
            return
        self.set_status("Нет активной операции для отмены.")

    @Slot()
    def open_output_folder(self):
        folder = Path(self.output_edit.text().strip() or str(DEFAULT_OUTPUT)).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.set_status(f"Не удалось открыть папку загрузок: {exc}", assertive=True)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _focus_book_url(self):
        if self.current_ui_mode() == "easy":
            self.easy_input.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self.easy_input.selectAll()
        else:
            self.tabs.setCurrentIndex(self.TAB_BOOK)
            self.book_url_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self.book_url_edit.selectAll()

    def _toggle_current_track_from_keyboard(self):
        if not self.track_table.isEnabled() or self.current_book is None:
            return
        current = self.track_table.currentIndex()
        if not current.isValid():
            if not focus_table_row(self.track_table, 0, column=0, focus=False):
                return
            current = self.track_table.currentIndex()
        check_index = self.track_model.index(current.row(), 0)
        state = self.track_model.data(check_index, Qt.ItemDataRole.CheckStateRole)
        new_state = Qt.CheckState.Unchecked if state == Qt.CheckState.Checked else Qt.CheckState.Checked
        self.track_model.setData(check_index, new_state, Qt.ItemDataRole.CheckStateRole)
        self.track_table.setCurrentIndex(check_index)

    def _show_accessibility_help(self):
        text = "\n".join((
            self._l("Клавиатурная навигация Qt-версии:"),
            "",
            self._l("Ctrl+1…Ctrl+6 — открыть раздел; Ctrl+L — ссылка на книгу; Ctrl+F — поиск; Ctrl+D — скачать выбранное; Ctrl+Q — очередь; Ctrl+H — история; F1 — эта справка."),
            self._l("В таблице частей: стрелки — перемещение, Пробел — выбрать или снять текущую часть."),
            self._l("В результатах поиска: стрелки — выбрать строку, Enter — использовать книгу."),
            self._l("Tab и Shift+Tab используют штатный порядок фокуса Qt; Escape отменяет текущий анализ/скачивание; модальные окна блокируют основной интерфейс до ответа."),
            self._l("Плеер: стрелки на позиции меняют время, Page Up/Page Down — крупный шаг; громкость читается в процентах."),
            "",
            self._l("Интерфейс использует нативные Qt accessibility roles/values и не устанавливает собственные перехватчики событий фокуса."),
        ))
        self._show_message(QMessageBox.Icon.Information, self._l("Доступность и горячие клавиши"), text)


__all__ = ["AccessibilityUiMixin"]
