from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Slot, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMenu, QMessageBox, QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from ...core import valid_site_url
from ...logging_utils import app_logger
from ...config.settings import load_app_settings
from ...services.library_service import clear_history, create_backup, export_history, load_history_records, restore_backup, save_history_records
from ..accessibility import configure_accessible, focus_table_row
from ..menu_utils import transient_menu

class HistoryUiMixin:
    """History behavior for :class:`AudioKnigiQtWindow`."""

    def _history_row_summary(self, row: int) -> str:
        if not (0 <= row < len(self._history_rows)):
            return ""
        item = self._history_rows[row]
        title = str(item.get("title", "") or self._l("без названия"))
        author = str(item.get("author", "") or self._l("нет данных"))
        narrator = str(item.get("narrator", "") or self._l("нет данных"))
        parts = item.get("parts", 0)
        folder = str(item.get("folder", "") or self._l("нет данных"))
        date = str(item.get("date", "") or self._l("нет данных"))
        return self._l(
            "Название: {title}. Автор: {author}. Чтец: {narrator}. Частей: {parts}. Дата: {date}. Папка: {folder}.",
            title=title, author=author, narrator=narrator, parts=parts, date=date, folder=folder,
        )

    @Slot(int, int, int, int)
    def _history_current_cell_changed(self, current_row: int, _current_col: int, previous_row: int, _previous_col: int) -> None:
        self._update_history_action_states()
        # Each current cell already exposes the complete row summary through
        # AccessibleDescriptionRole. Avoid a second explicit announcement of the
        # same text, which causes duplicate speech in NVDA/JAWS.

    def _update_history_action_states(self) -> None:
        buttons = getattr(self, "_history_action_buttons", {})
        has_selection = self._selected_history()[1] is not None if hasattr(self, "history_table") else False
        for ident in ("history_open_folder",):
            button = buttons.get(ident)
            if button is not None:
                button.setEnabled(has_selection)
        has_rows = bool(self._history_rows)
        if hasattr(self, "history_export_button"):
            self.history_export_button.setEnabled(has_rows)
            self.history_export_json_action.setEnabled(has_rows)
            self.history_export_csv_action.setEnabled(has_rows)
            self.history_clear_action.setEnabled(has_rows)

    def _build_history_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.history_table = QTableWidget(0, 7)
        self.history_table.setHorizontalHeaderLabels([self._l(x) for x in ("Обложка", "Дата", "Название", "Автор", "Чтец", "Частей", "Папка")])
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setShowGrid(False)
        self.history_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        history_header = self.history_table.horizontalHeader()
        history_header.setResizeContentsPrecision(60)
        for column in (0, 1, 5):
            history_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        history_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        history_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        history_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.history_table.setColumnWidth(2, 320)
        self.history_table.setColumnWidth(3, 220)
        self.history_table.setColumnWidth(4, 220)
        history_header.setStretchLastSection(False)
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self._show_history_context_menu)
        configure_accessible(self.history_table, name=self._l("История"), identifier="history_table")
        self.history_table.doubleClicked.connect(lambda _index: self.history_open_folder())
        self.history_table.currentCellChanged.connect(self._history_current_cell_changed)
        self.history_results_stack = QStackedWidget(page)
        self.history_empty_state = QLabel(self._l("Скачанные книги появятся здесь"))
        self.history_empty_state.setObjectName("emptyState")
        self.history_empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history_empty_state.setWordWrap(True)
        configure_accessible(self.history_empty_state, name=self._l("Скачанные книги появятся здесь"), identifier="history_empty_state")
        self.history_results_stack.addWidget(self.history_empty_state)
        self.history_results_stack.addWidget(self.history_table)
        self.history_results_stack.setCurrentIndex(0)
        layout.addWidget(self.history_results_stack, 1)

        row = QHBoxLayout()
        self._history_action_buttons: dict[str, QPushButton] = {}
        for text, name, ident, callback in (
            (self._l("Открыть папку"), self._l("Открыть папку"), "history_open_folder", self.history_open_folder),
            (self._l("Обновить"), self._l("Обновить"), "refresh_history", self._load_history),
        ):
            button = QPushButton(text)
            configure_accessible(button, name=name, identifier=ident)
            button.clicked.connect(callback)
            row.addWidget(button)
            self._history_action_buttons[ident] = button

        self.history_export_button = QPushButton(self._l("Экспорт библиотеки ▾"))
        configure_accessible(self.history_export_button, name="Экспорт библиотеки", identifier="history_export")
        export_menu = QMenu(self.history_export_button)
        self.history_export_json_action = export_menu.addAction(self._l("В JSON…"))
        self.history_export_csv_action = export_menu.addAction(self._l("В CSV…"))
        export_menu.addSeparator()
        self.history_clear_action = export_menu.addAction(self._l("Очистить историю"))
        self.history_export_json_action.setObjectName("history_export_json")
        self.history_export_csv_action.setObjectName("history_export_csv")
        self.history_clear_action.setObjectName("history_clear")
        self.history_export_json_action.triggered.connect(lambda: self.export_library("json"))
        self.history_export_csv_action.triggered.connect(lambda: self.export_library("csv"))
        self.history_clear_action.triggered.connect(self.history_clear)
        self.history_export_button.setMenu(export_menu)
        row.addWidget(self.history_export_button)
        row.addStretch(1)
        layout.addLayout(row)
        return page

    def _show_history_context_menu(self, pos):
        if pos is None:
            current = self.history_table.currentIndex()
            pos = self.history_table.visualRect(current).center() if current.isValid() else self.history_table.viewport().rect().center()
        index = self.history_table.indexAt(pos)
        if index.isValid():
            self.history_table.setCurrentCell(index.row(), max(0, index.column()))
            self.history_table.selectRow(index.row())
        row, item = self._selected_history()
        if item is None:
            return
        menu = transient_menu(self.history_table)
        listen_action = menu.addAction(self._l("Слушать книгу"))
        open_action = menu.addAction(self._l("Открыть папку"))
        redownload_action = menu.addAction(self._l("Скачать заново"))
        redownload_action.setObjectName("history_redownload")
        menu.addSeparator()
        delete_action = menu.addAction(self._l("Удалить запись"))
        delete_action.setObjectName("history_delete")
        chosen = menu.exec(self.history_table.viewport().mapToGlobal(pos))
        if chosen is listen_action:
            self.history_listen()
        elif chosen is open_action:
            self.history_open_folder()
        elif chosen is redownload_action:
            self.history_redownload()
        elif chosen is delete_action:
            self.history_delete()

    @Slot()
    def _load_history(self):
        rows = load_history_records()
        self._history_rows = rows
        history_blocker = QSignalBlocker(self.history_table)
        self.history_table.setUpdatesEnabled(False)
        self.history_table.setRowCount(len(rows))
        headers = ["Обложка", "Дата", "Название", "Автор", "Чтец", "Частей", "Папка"]
        localized_headers = [self._l(value) for value in headers]
        for row, item in enumerate(rows):
            values = [
                "", item.get("date", ""), item.get("title", ""), item.get("author", ""),
                item.get("narrator", ""), item.get("parts", 0), item.get("folder", ""),
            ]
            row_summary = self._history_row_summary(row)
            for col, value in enumerate(values):
                shown = "" if value is None else str(value)
                cell = QTableWidgetItem(shown)
                accessible_text = f"{localized_headers[col]}: {shown or self._l('нет данных')}"
                cell.setData(Qt.ItemDataRole.AccessibleTextRole, accessible_text)
                cell.setData(Qt.ItemDataRole.AccessibleDescriptionRole, row_summary)
                self.history_table.setItem(row, col, cell)
            cover_file = Path(str(item.get("cover_file", "") or "")).expanduser()
            if cover_file.is_file():
                self.history_table.item(row, 0).setIcon(QIcon(str(cover_file)))
        self.history_table.resizeColumnsToContents()
        self.history_table.setUpdatesEnabled(True)
        del history_blocker
        if hasattr(self, "history_results_stack"):
            self.history_results_stack.setCurrentIndex(1 if rows else 0)
        if rows and self.history_table.currentRow() < 0:
            focus_table_row(self.history_table, 0, column=2, focus=False)
        self._update_history_action_states()
        if hasattr(self, "status"):
            self.set_status(f"История обновлена: {len(rows)} записей.")

    def _selected_history(self):
        row = self.history_table.currentRow()
        if row < 0:
            selected = self.history_table.selectionModel().selectedRows()
            row = selected[0].row() if selected else -1
        if 0 <= row < len(self._history_rows):
            return row, dict(self._history_rows[row])
        return None, None

    @Slot()
    def history_listen(self):
        _row, item = self._selected_history()
        if not item:
            self.set_status("Сначала выберите книгу в истории.", assertive=True)
            return
        folder = Path(str(item.get("folder", "") or "")).expanduser()
        if not folder.is_dir():
            self.set_status("Папка выбранной книги не найдена.", assertive=True)
            return
        self.set_ui_mode("advanced", persist=False)
        self.tabs.setCurrentIndex(self.TAB_PLAYER)
        self.load_book_folder(folder, autoplay=True)

    @Slot()
    def history_open_folder(self):
        _row, item = self._selected_history()
        if not item:
            self.set_status("Сначала выберите книгу в истории.", assertive=True)
            return
        folder = Path(str(item.get("folder", "") or "")).expanduser()
        if not folder.exists():
            self.set_status("Папка выбранной книги не найдена.", assertive=True)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    @Slot()
    def history_redownload(self):
        _row, item = self._selected_history()
        if not item:
            self.set_status("Сначала выберите книгу в истории.", assertive=True)
            return
        url = str(item.get("url", "") or "").strip()
        if not valid_site_url(url):
            self.set_status("В истории нет поддерживаемой ссылки для этой книги.", assertive=True)
            return
        self._download_after_analysis = True
        self._history_redownload_confirmed = True
        self._queue_after_analysis = False
        self.book_url_edit.setText(url)
        self.set_ui_mode("advanced", persist=False)
        self.tabs.setCurrentIndex(self.TAB_BOOK)
        self.start_analysis()

    @Slot()
    def history_delete(self):
        row, item = self._selected_history()
        if row is None or not item:
            self.set_status("Сначала выберите запись истории.", assertive=True)
            return
        removed = self._history_rows.pop(row)
        if not save_history_records(self._history_rows):
            self._history_rows.insert(row, removed)
            self.set_status("Не удалось удалить запись истории.", assertive=True)
            return
        table_had_focus = self.history_table.hasFocus()
        self._load_history()
        if self._history_rows:
            next_row = min(row, len(self._history_rows) - 1)
            focus_table_row(self.history_table, next_row, column=2, focus=table_had_focus)
        self._update_history_action_states()
        self.set_status("Запись истории удалена.", assertive=True)

    def export_library(self, format_name: str):
        fmt = str(format_name or "json").lower()
        suffix = ".json" if fmt == "json" else ".csv"
        selected_filter = "JSON (*.json)" if fmt == "json" else "CSV (*.csv)"
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._l("Экспорт библиотеки"),
            f"audioknigi_library{suffix}",
            selected_filter,
        )
        if not path:
            return
        try:
            result = export_history(self._history_rows, Path(path), fmt)
        except Exception as exc:
            self._show_message(QMessageBox.Icon.Critical, "Ошибка экспорта", str(exc))
            return
        self.set_status(f"Библиотека экспортирована: {result}", assertive=True)

    @Slot()
    def history_clear(self):
        if not self._history_rows:
            return
        answer = self._ask_yes_no(
            "Очистить историю",
            "Очистить всю историю загрузок? Аудиофайлы на диске останутся.",
            default_yes=False,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if clear_history():
            self._load_history()
            self.set_status("История очищена.", assertive=True)
        else:
            self.set_status("Не удалось очистить историю.", assertive=True)

    @Slot()
    def create_backup(self):
        self._save_settings(silent=True)
        default_name = f"AudioKnigi_backup_{time.strftime('%Y-%m-%d')}.zip"
        path, _ = QFileDialog.getSaveFileName(self, self._l("Создать резервную копию"), default_name, "ZIP (*.zip)")
        if not path:
            return
        try:
            result = create_backup(Path(path))
        except Exception as exc:
            self._show_message(QMessageBox.Icon.Critical, "Ошибка резервной копии", str(exc))
            return
        self._show_message(QMessageBox.Icon.Information, "Резервная копия", f"Резервная копия создана:\n{result}")

    @Slot()
    def restore_backup(self):
        if self._long_operation_active():
            self.set_status("Сначала завершите текущую загрузку или очередь.", assertive=True)
            return
        path, _ = QFileDialog.getOpenFileName(self, self._l("Восстановить резервную копию"), "", "ZIP (*.zip)")
        if not path:
            return
        answer = self._ask_yes_no(
            "Восстановить резервную копию",
            "Настройки, история, позиции плеера и сохранённая очередь из ZIP заменят текущие данные. Продолжить?",
            default_yes=False,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        controller = getattr(self, "player_controller", None)
        if controller is not None:
            try:
                controller.suspend_position_persistence()
            except Exception:
                app_logger.debug("Could not suspend player position persistence", exc_info=True)
        try:
            restored = restore_backup(Path(path))
            if controller is not None:
                controller.reload_position_store()
        except Exception as exc:
            self._show_message(QMessageBox.Icon.Critical, "Ошибка восстановления", str(exc))
            return
        finally:
            if controller is not None:
                try:
                    controller.resume_position_persistence()
                except Exception:
                    app_logger.debug("Could not resume player position persistence", exc_info=True)
        self.settings = load_app_settings()
        self._apply_settings_to_qt_controls()
        self._load_history()
        self._load_queue()
        self._refresh_unfinished()
        self._apply_saved_theme()
        self._show_message(
            QMessageBox.Icon.Information,
            "Восстановление завершено",
            "Восстановлено: " + ", ".join(restored) + ".\nДля масштаба и позиции уже открытого плеера рекомендуется перезапустить Qt-интерфейс.",
        )


__all__ = ["HistoryUiMixin"]
