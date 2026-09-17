from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Slot, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
from ...core import DEFAULT_OUTPUT, valid_site_url
from ...models import TRACK_STATUS_MISSING
from ...sources import normalize_supported_url
from ...services.library_service import scan_unfinished
from ..menu_utils import transient_menu

class ClipboardUiMixin:
    """Clipboard behavior for :class:`AudioKnigiQtWindow`."""

    @staticmethod
    def _normalize_drop_values(values) -> list[str]:
        out: list[str] = []
        for raw in values or []:
            for value in str(raw or "").splitlines():
                value = value.strip()
                if not value:
                    continue
                path = Path(value)
                if path.suffix.lower() == ".url":
                    try:
                        if not path.is_file():
                            raise FileNotFoundError
                        payload = path.read_bytes()
                        if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
                            content = payload.decode("utf-16")
                        elif payload.startswith(b"\xef\xbb\xbf"):
                            content = payload.decode("utf-8-sig")
                        else:
                            try:
                                content = payload.decode("utf-8")
                            except UnicodeDecodeError:
                                try:
                                    content = payload.decode("cp1251")
                                except UnicodeDecodeError:
                                    content = payload.decode("cp1252", errors="replace")
                        match = re.search(r"(?im)^URL=(.+)$", content)
                        if match:
                            shortcut_url = match.group(1).strip()
                            if valid_site_url(shortcut_url):
                                value = shortcut_url
                    except (OSError, ValueError):
                        pass
                if value and value not in out:
                    out.append(value)
        return out

    def _extract_drop_values(self, mime) -> list[str]:
        values: list[str] = []
        if mime.hasUrls():
            for url in mime.urls():
                values.append(url.toLocalFile() if url.isLocalFile() else url.toString())
        if mime.hasText():
            values.append(str(mime.text() or ""))
        return self._normalize_drop_values(values)

    def dragEnterEvent(self, event):
        if self._extract_drop_values(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        values = self._extract_drop_values(event.mimeData())
        if values:
            self._handle_dropped_values(values)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def _handle_dropped_values(self, values):
        urls = [v for v in values if valid_site_url(v)]
        if not urls:
            self.set_status("В перетаскиваемых данных нет поддерживаемых ссылок.", assertive=True)
            return
        if len(urls) == 1:
            if self.current_ui_mode() == "easy":
                self.easy_input.setText(urls[0])
                self.easy_universal_action()
            else:
                self.book_url_edit.setText(urls[0])
                self.start_analysis()
        else:
            self._queue_urls_dropped(urls)

    def _book_url_changed(self, text: str):
        running = self._analysis_thread is not None and self._analysis_thread.isRunning()
        if not running:
            self._set_analysis_button_state(False)
        incoming_url = normalize_supported_url(str(text or "").strip())
        current_url = normalize_supported_url(str(getattr(self.current_book, "url", "") or "").strip()) if self.current_book is not None else ""
        stale = bool(self.current_book is not None and incoming_url != current_url)
        narration_switch = bool(getattr(self, "_pending_narration_switch", False))
        self._book_url_is_stale = stale
        if self.current_book is None:
            return

        enabled = bool(self.current_book.tracks) and not stale
        selected = self.track_model.selected_count() > 0
        self.select_all_tracks_button.setEnabled(enabled)
        self.clear_tracks_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled and selected)
        self.full_mp3_button.setEnabled(enabled and self._book_supports_full_mp3(self.current_book))
        self.add_queue_button.setEnabled(enabled and selected)
        self.easy_download_button.setEnabled(enabled)
        if stale:
            self.play_selected_track_button.setEnabled(False)
            if narration_switch:
                # _narration_selected schedules analysis immediately; do not
                # announce the misleading manual-action warning in between.
                self.book_summary.setAccessibleDescription("")
            else:
                self.book_summary.setAccessibleDescription(self._l("Ссылка изменена. Выполните анализ книги заново."))
        else:
            self.book_summary.setAccessibleDescription("")
        self._update_download_primary_button()

    @Slot()
    def paste_book_url(self):
        text = QApplication.clipboard().text().strip()
        if not text:
            self.set_status("Буфер обмена пуст.", assertive=True)
            return
        if not valid_site_url(text):
            self.set_status("В буфере нет поддерживаемой ссылки аудиокниги.", assertive=True)
            return
        self.book_url_edit.setText(text)
        self._play_event_sound("link_pasted")
        self.book_url_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        self.set_status("Ссылка вставлена из буфера обмена.")

    def _set_clipboard_text(self, text: str) -> None:
        value = str(text or "")
        # Do not offer to paste a URL that the application itself just copied.
        # ``QClipboard.dataChanged`` can be emitted synchronously on Windows, so
        # the suppression marker must be set before ``setText``.
        self._suppress_clipboard_prompt_text = value.strip()
        QApplication.clipboard().setText(value)

    def _clipboard_auto_enabled(self) -> bool:
        check = getattr(self, "clipboard_auto_check", None)
        if check is not None:
            return bool(check.isChecked())
        return bool(self.settings.get("clipboard_auto", True))

    @Slot()
    def _clipboard_data_changed(self):
        self._schedule_clipboard_prompt_check()

    def _schedule_clipboard_prompt_check(self):
        if self._clipboard_prompt_scheduled:
            return
        self._clipboard_prompt_scheduled = True

        def run_check():
            self._clipboard_prompt_scheduled = False
            self._check_clipboard_for_book_link()

        QTimer.singleShot(0, run_check)

    def _insert_clipboard_book_link(self, text: str) -> None:
        value = str(text or "").strip()
        if not value:
            return
        # Keep both mode-specific input fields in sync.  Previously the startup
        # prompt wrote only to the advanced field, which made a successful
        # "Yes" look like it had done nothing when Easy mode was visible.
        self.book_url_edit.setText(value)
        self.easy_input.setText(value)
        if self.current_ui_mode() == "easy":
            self.easy_input.setFocus(Qt.FocusReason.OtherFocusReason)
        else:
            self.tabs.setCurrentIndex(self.TAB_BOOK)
            self.book_url_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        self.set_status("Ссылка вставлена из буфера обмена.")

    def _check_clipboard_for_book_link(self) -> None:
        if not self._clipboard_auto_enabled():
            return
        app = QApplication.instance()
        if app is not None and app.applicationState() != Qt.ApplicationState.ApplicationActive:
            return
        text = QApplication.clipboard().text().strip()
        suppress = str(self._suppress_clipboard_prompt_text or "").strip()
        if suppress:
            same_clipboard_url = text == suppress
            if not same_clipboard_url and valid_site_url(text) and valid_site_url(suppress):
                same_clipboard_url = (
                    normalize_supported_url(text) == normalize_supported_url(suppress)
                )
            if same_clipboard_url:
                return
            self._suppress_clipboard_prompt_text = ""
        if text != self._last_clipboard_prompt:
            # Changing the clipboard re-arms a previously declined URL.
            self._last_clipboard_prompt = ""
        if not text or not valid_site_url(text) or text == self._last_clipboard_prompt:
            return
        current_values = {
            self.book_url_edit.text().strip(),
            self.easy_input.text().strip() if hasattr(self, "easy_input") else "",
        }
        if text in current_values:
            return
        self._last_clipboard_prompt = text
        answer = self._ask_yes_no(
            "Ссылка в буфере обмена",
            "В буфере найдена поддерживаемая ссылка аудиокниги. Вставить её в поле книги?",
            default_yes=True,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._insert_clipboard_book_link(text)

    @Slot(object)
    def _application_state_changed(self, state):
        if state == Qt.ApplicationState.ApplicationActive:
            self._schedule_clipboard_prompt_check()

    def _refresh_unfinished(self):
        output = self.output_edit.text().strip() if hasattr(self, "output_edit") else str(DEFAULT_OUTPUT)
        self._unfinished_records = scan_unfinished(output)
        count = len(self._unfinished_records)
        if hasattr(self, "unfinished_label"):
            self.unfinished_label.setText(self._l("Незавершённых загрузок: {count}", count=count))
        if hasattr(self, "recovery_panel"):
            self.recovery_panel.setVisible(count > 0)
        if hasattr(self, "recovery_button"):
            self.recovery_button.setEnabled(count > 0 and not self._long_operation_active())

    @Slot()
    def continue_unfinished(self):
        self._refresh_unfinished()
        records = list(self._unfinished_records)
        if not records:
            self._show_message(QMessageBox.Icon.Information, "Восстановление", "Незавершённых загрузок с resume.json не найдено.")
            return
        record = records[0]
        if len(records) > 1:
            labels = [f"{item.title} — {item.updated_at or item.folder}" for item in records]
            chosen, ok = QInputDialog.getItem(self, self._l("Продолжить загрузку"), self._l("Выберите книгу:"), labels, 0, False)
            if not ok:
                return
            try:
                record = records[labels.index(chosen)]
            except (ValueError, IndexError):
                return
        self._resume_selected_indices = None if record.selected_indices is None else set(record.selected_indices)
        self._full_mp3_after_analysis = str(getattr(record, "download_mode", "parts") or "parts") == "full_mp3"
        self._download_after_analysis = not self._full_mp3_after_analysis
        self._queue_after_analysis = False
        self.settings.update({
            "naming_mode": record.naming_mode,
            "audio_preset": record.audio_preset,
            "normalization_mode": record.normalization_mode,
            "use_templates": record.use_templates,
            "folder_template": record.folder_template,
            "track_template": record.track_template,
        })
        self._apply_settings_to_qt_controls()
        self.book_url_edit.setText(record.url)
        self.tabs.setCurrentIndex(self.TAB_BOOK)
        self.set_status(f"Восстанавливаю загрузку: {record.title}", assertive=True)
        self._play_event_sound("recovery_started")
        self.start_analysis()

    def _show_track_context_menu(self, pos):
        if pos is not None and (index := self.track_table.indexAt(pos)).isValid():
            self.track_table.setCurrentIndex(index)
            self.track_table.selectRow(index.row())
        track = self._selected_track()
        if track is None:
            return
        menu = transient_menu(self.track_table)
        play = menu.addAction(self._l("Воспроизвести локальный файл"))
        open_file = menu.addAction(self._l("Открыть локальный файл"))
        open_folder = menu.addAction(self._l("Открыть папку книги"))
        menu.addSeparator()
        download = menu.addAction(self._l("Скачать только эту часть"))
        redownload = menu.addAction(self._l("Скачать эту часть заново"))
        copy_url = menu.addAction(self._l("Копировать URL аудиофайла"))
        local_path = Path(str(getattr(track, "local_path", "") or "")).expanduser()
        play.setEnabled(local_path.is_file())
        open_file.setEnabled(local_path.is_file())
        open_folder.setEnabled(local_path.is_file() or self.current_book is not None)
        if pos is None:
            current = self.track_table.currentIndex()
            rect = self.track_table.visualRect(current) if current.isValid() else self.track_table.rect()
            global_pos = self.track_table.viewport().mapToGlobal(rect.center())
        else:
            global_pos = self.track_table.viewport().mapToGlobal(pos)
        action = menu.exec(global_pos)
        if action is play:
            self.play_selected_track()
        elif action is open_file:
            self.open_selected_track_file()
        elif action is open_folder:
            self.open_current_book_folder()
        elif action is redownload:
            path_text = str(getattr(track, "local_path", "") or "").strip()
            if path_text:
                try:
                    Path(path_text).expanduser().unlink(missing_ok=True)
                except Exception as exc:
                    self._append_log(f"Не удалось удалить старый файл части: {exc}")
            track.local_status = TRACK_STATUS_MISSING
            track.actual_duration = None
            track.local_path = ""
            self.download_selected_track_only()
        elif action is download:
            self.download_selected_track_only()
        elif action is copy_url:
            self.copy_selected_track_url()

    def open_selected_track_file(self):
        track = self._selected_track()
        path = Path(str(getattr(track, "local_path", "") or "")).expanduser() if track else None
        if not path or not path.is_file():
            self.set_status("Локальный файл выбранной части не найден.", assertive=True)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_current_book_folder(self):
        track = self._selected_track()
        path = Path(str(getattr(track, "local_path", "") or "")).expanduser() if track else None
        folder = path.parent if path and path.is_file() else None
        if folder is None and self.current_book is not None:
            for item in self.current_book.tracks:
                candidate = Path(str(getattr(item, "local_path", "") or "")).expanduser()
                if candidate.is_file():
                    folder = candidate.parent
                    break
        if folder is None or not folder.exists():
            self.set_status("Папка готовой книги пока не найдена.", assertive=True)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def copy_selected_track_url(self):
        track = self._selected_track()
        url = str(getattr(track, "file", "") or "").strip() if track else ""
        if not url:
            self.set_status("У выбранной части нет URL.", assertive=True)
            return
        self._set_clipboard_text(url)
        self.set_status("URL выбранной части скопирован.")

    def download_selected_track_only(self):
        track = self._selected_track()
        if track is None:
            self.set_status("Сначала выберите часть книги.", assertive=True)
            return
        self.track_model.set_all_selected(False)
        index = self.track_model.index(self.track_table.currentIndex().row(), 0)
        self.track_model.setData(index, Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole)
        self.start_download()


__all__ = ["ClipboardUiMixin"]
