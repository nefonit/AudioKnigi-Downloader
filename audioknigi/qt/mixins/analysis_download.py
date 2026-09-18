from __future__ import annotations

import copy
import threading

from PySide6.QtCore import QThread, Slot, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QMessageBox
from ...core import effective_track_duration, fmt_time, valid_site_url
from ...models import Book, cover_cache_bytes, normalize_cover_cache
from ...i18n import tr
from ...services.book_analysis_service import AnalysisOptions
from ...services.download_request import build_download_request
from ...download_engine import DownloadResult, DownloadService
from ...sources import normalize_supported_url
from ..accessibility import configure_accessible, focus_table_row
from ..workers import AnalysisWorker as _AnalysisWorker, DownloadWorker as _DownloadWorker, MissingMediaDecision as _MissingMediaDecision

class AnalysisDownloadUiMixin:
    """Analysis Download behavior for :class:`AudioKnigiQtWindow`."""

    @Slot()
    def _analysis_primary_action(self):
        running = self._analysis_thread is not None and self._analysis_thread.isRunning()
        if running:
            self.cancel_analysis()
        else:
            self.start_analysis()

    def _set_analysis_button_state(self, running: bool, *, cancelling: bool = False) -> None:
        if running:
            self.analyze_button.setText(self._l("Отмена…") if cancelling else self._l("Отмена"))
            self.analyze_button.setProperty("role", "danger")
            self.analyze_button.setEnabled(not cancelling)
            self.analyze_button.setAccessibleName(self._l("Отменить анализ книги"))
        else:
            self.analyze_button.setText(self._l("Анализировать"))
            self.analyze_button.setProperty("role", "primary")
            self.analyze_button.setEnabled(bool(self.book_url_edit.text().strip()) and not self._long_operation_active())
            self.analyze_button.setAccessibleName(self._l("Анализировать книгу"))
        try:
            self.analyze_button.style().unpolish(self.analyze_button)
            self.analyze_button.style().polish(self.analyze_button)
        except Exception:
            pass

    @Slot()
    def _start_primary_download(self):
        if self.current_book is None:
            return
        selected = self.track_model.selected_count()
        total = len(self.current_book.tracks)
        if selected <= 0:
            self.set_status("Выберите хотя бы одну часть книги.", assertive=True)
            return
        if selected < total:
            self.start_download()
        else:
            self.start_download_all()

    def _update_download_primary_button(self) -> None:
        if not hasattr(self, "download_all_button"):
            return
        book = self.current_book
        total = len(book.tracks) if book is not None else 0
        selected = self.track_model.selected_count() if book is not None else 0
        downloading = self._download_thread is not None and self._download_thread.isRunning()
        stale_url = bool(getattr(self, "_book_url_is_stale", False))
        if selected > 0 and selected < total:
            text = self._l("Скачать выбранное ({count})", count=selected)
            accessible = self._l("Скачать выбранные части, {count}", count=selected)
        else:
            text = self._l("Скачать книгу")
            accessible = self._l("Скачать всю книгу")
        self.download_all_button.setText(text)
        self.download_all_button.setAccessibleName(accessible)
        can_download = bool(total and selected and not stale_url and not downloading and not self._queue_running)
        self.download_all_button.setEnabled(can_download)
        if hasattr(self, "download_menu_button"):
            self.download_menu_button.setEnabled(bool(total and not stale_url and not downloading and not self._queue_running))
        if hasattr(self, "download_full_mp3_action"):
            self.download_full_mp3_action.setEnabled(bool(total and not stale_url and self._book_supports_full_mp3(book) and not downloading and not self._queue_running))
        if hasattr(self, "download_queue_action"):
            self.download_queue_action.setEnabled(bool(total and selected and not stale_url and not downloading))
        if hasattr(self, "download_full_mp3_queue_action"):
            self.download_full_mp3_queue_action.setEnabled(
                bool(total and not stale_url and self._book_supports_full_mp3(book) and not downloading)
            )

    def _update_narration_combo(self, book: Book):
        variants = []
        seen = set()
        for item in list(getattr(book, "narration_variants", None) or []):
            url = normalize_supported_url(str(getattr(item, "url", "") or ""))
            if not url or url in seen:
                continue
            seen.add(url)
            variants.append(item)
        visible = len(variants) > 1
        self.narration_label.setVisible(visible)
        self.narration_combo.setVisible(visible)
        self.narration_combo.blockSignals(True)
        self.narration_combo.clear()
        current_url = normalize_supported_url(str(getattr(book, "url", "") or ""))
        current_index = 0
        for idx, item in enumerate(variants):
            narrator = str(getattr(item, "narrator", "") or "").strip() or self._l(
                "Озвучка {index}", index=idx + 1
            )
            available = getattr(item, "available", None)
            suffix = (
                f" — {self._l('недоступно')}"
                if available is False
                else f" — {self._l('доступно')}"
                if available is True
                else ""
            )
            url = normalize_supported_url(str(getattr(item, "url", "") or ""))
            self.narration_combo.addItem(narrator + suffix, url)
            if url == current_url:
                current_index = idx
        if variants:
            self.narration_combo.setCurrentIndex(current_index)
        self.narration_combo.blockSignals(False)
        first_available = None
        current_variant = None
        for idx, item in enumerate(variants):
            item_url = normalize_supported_url(str(getattr(item, "url", "") or ""))
            if item_url == current_url:
                current_variant = item
            if first_available is None and getattr(item, "available", None) is True and item_url != current_url:
                first_available = idx
        current_blocked = current_variant is not None and getattr(current_variant, "available", None) is False
        self.narration_available_button.setProperty("availableIndex", -1 if first_available is None else int(first_available))
        self.narration_available_button.setVisible(bool(visible and first_available is not None and (current_blocked or not getattr(book, "tracks", None))))

    @Slot(int)
    def _narration_selected(self, index: int):
        url = normalize_supported_url(str(self.narration_combo.itemData(index) or ""))
        current = normalize_supported_url(str(getattr(self.current_book, "url", "") or ""))
        if not url or url == current:
            return
        # Re-analysis creates a fresh Book/Track list. Preserve the user's
        # explicit chapter selection across a narration switch instead of
        # silently reverting to every chapter selected.
        self._pending_narration_selected_indices = list(self.track_model.selected_indices())
        self._pending_narration_switch = True
        self.book_url_edit.setText(url)
        self._pending_narration_switch = False
        self.set_status(f"Выбрана другая озвучка: {self.narration_combo.itemText(index)}")
        # Changing narration is one user action and must produce one success cue.
        # The automatic re-analysis that follows should not immediately add a
        # second book_found cue on top of narration_changed.
        self._suppress_next_book_found_sound = True
        self._play_event_sound("narration_changed")
        QTimer.singleShot(0, self.start_analysis)

    @Slot()
    def select_first_available_narration(self):
        try:
            index = int(self.narration_available_button.property("availableIndex"))
        except (TypeError, ValueError):
            index = -1
        if index < 0 or index >= self.narration_combo.count():
            self.set_status("Других доступных озвучек не найдено.", assertive=True)
            return
        self.narration_combo.setCurrentIndex(index)
        self._narration_selected(index)

    @Slot()
    def start_analysis(self):
        url = self.book_url_edit.text().strip()
        if not url:
            self.set_status("Введите название, автора или ссылку на книгу.", assertive=True)
            self.book_url_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        if not valid_site_url(url):
            if url.lower().startswith(("http://", "https://")):
                self.set_status("Неподдерживаемая ссылка.", assertive=True)
                self._show_message(QMessageBox.Icon.Warning, "Неподдерживаемая ссылка", "Поддерживаются audioknigi.com.ua, knigavuhe.org и poleknig.com.")
                return
            self.search_edit.setText(url)
            self.tabs.setCurrentIndex(self.TAB_SEARCH)
            self.set_ui_mode("advanced", persist=False)
            self.start_search()
            return
        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            self.set_status("Анализ книги уже выполняется.")
            return
        if self._download_thread is not None and self._download_thread.isRunning():
            self.set_status("Сначала завершите или отмените текущее скачивание.", assertive=True)
            return

        self._book_url_is_stale = False
        self.current_book = None
        self.track_model.set_book(None)
        self.book_empty_state.setVisible(False)
        self.book_summary.setText(self._rt("Анализирую книгу…"))
        self.cancel_analysis_button.setEnabled(True)
        self._set_analysis_button_state(True)
        self.select_all_tracks_button.setEnabled(False)
        self.clear_tracks_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.full_mp3_button.setEnabled(False)
        self.add_queue_button.setEnabled(False)
        self.analysis_progress.setRange(0, 0)
        self.set_status("Начинаю анализ книги…")
        self._show_blocking_operation(
            "analysis",
            title=tr(self.language, "status_analyzing"),
            message=self._rt("Начинаю анализ книги…"),
            cancel_callback=self.cancel_analysis,
            indeterminate=True,
        )

        cancel_event = threading.Event()
        options = AnalysisOptions(
            playwright_fallback_enabled=bool(self.playwright_check.isChecked()),
            fetch_cover=True,
            fetch_remote_size=True,
        )
        thread = QThread(self)
        worker = _AnalysisWorker(url, cancel_event, options)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._analysis_progress_message, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(self._analysis_finished, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._clear_analysis_thread, Qt.ConnectionType.QueuedConnection)
        thread.finished.connect(thread.deleteLater)
        self._analysis_cancel = cancel_event
        self._analysis_thread = thread
        self._analysis_worker = worker
        thread.start()

    @Slot(str)
    def _analysis_progress_message(self, message: str):
        if message:
            self.set_status(message)
            self._update_blocking_operation(
                "analysis", message=self._rt(message), indeterminate=True
            )

    @Slot(object)
    def _analysis_finished(self, result):
        kind, payload = result
        self._finish_blocking_operation("analysis")
        suppress_book_found_sound = bool(self._suppress_next_book_found_sound)
        self._suppress_next_book_found_sound = False
        self.analysis_progress.setRange(0, 1)
        self.analysis_progress.setValue(1 if kind == "ok" else 0)
        self.cancel_analysis_button.setEnabled(False)
        self._set_analysis_button_state(False)
        if kind == "cancelled":
            self._pending_narration_selected_indices = None
            self._queue_after_analysis = False
            self._queue_reanalyze_task_id = None
            self._download_after_analysis = False
            self._full_mp3_after_analysis = False
            self._history_redownload_confirmed = False
            self.book_summary.setText(self._rt("Анализ отменён."))
            self.book_empty_state.setVisible(True)
            self.set_status("Анализ книги отменён.")
            # Explicit Cancel means cancel the whole dropped batch, not just
            # advance immediately to the next URL and force repeated cancels.
            self._pending_queue_urls = []
            return
        if kind == "error":
            self._pending_narration_selected_indices = None
            self._queue_after_analysis = False
            self._queue_reanalyze_task_id = None
            self._download_after_analysis = False
            self._full_mp3_after_analysis = False
            self.book_summary.setText(self._rt("Не удалось проанализировать книгу."))
            self.book_empty_state.setVisible(True)
            self.set_status("Ошибка анализа: " + str(payload), assertive=True)
            self._show_message(QMessageBox.Icon.Critical, "Ошибка анализа", str(payload))
            self._play_event_sound("book_not_found")
            if getattr(self, "_pending_queue_urls", None):
                QTimer.singleShot(0, self._queue_next_dropped_url)
            return

        book = payload
        if not isinstance(book, Book):
            self._pending_narration_selected_indices = None
            self._queue_after_analysis = False
            self._queue_reanalyze_task_id = None
            self._download_after_analysis = False
            self._full_mp3_after_analysis = False
            self._history_redownload_confirmed = False
            self.book_summary.setText(self._l("Получен неизвестный результат анализа."))
            self.set_status("Некорректный результат анализа.", assertive=True)
            if getattr(self, "_pending_queue_urls", None):
                QTimer.singleShot(0, self._queue_next_dropped_url)
            return
        pending = self._pending_search_result
        pending_url = normalize_supported_url(str(getattr(pending, "url", "") or "")) if pending is not None else ""
        book_url = normalize_supported_url(str(getattr(book, "url", "") or ""))
        if pending is not None and pending_url and pending_url == book_url:
            if not getattr(book, "narration_variants", None) and getattr(pending, "narration_variants", None):
                book.narration_variants = list(pending.narration_variants)
        self._pending_search_result = None
        narration_key = (" ".join(str(getattr(book, "title", "") or "").split()).casefold(),
                         " ".join(str(getattr(book, "author", "") or "").split()).casefold())
        if getattr(book, "narration_variants", None):
            self._known_narration_variants = (narration_key, list(book.narration_variants))
        elif self._known_narration_variants and self._known_narration_variants[0] == narration_key:
            book.narration_variants = list(self._known_narration_variants[1])
        else:
            self._known_narration_variants = None
        pending_narration_selection = getattr(self, "_pending_narration_selected_indices", None)
        if self._resume_selected_indices is not None:
            wanted = set(self._resume_selected_indices)
            for track in book.tracks:
                track.selected = int(track.index) in wanted
            self._resume_selected_indices = None
        elif pending_narration_selection is not None:
            wanted = {int(value) for value in pending_narration_selection}
            for track in book.tracks:
                track.selected = int(track.index) in wanted
        self._pending_narration_selected_indices = None
        self._book_url_is_stale = False
        self.current_book = book
        self.book_empty_state.setVisible(False)
        self.track_model.set_book(book)
        self.play_selected_track_button.setEnabled(False)
        self.track_table.resizeColumnsToContents()
        parts = len(book.tracks)
        details = [book.title or self._l("Без названия")]
        if book.author:
            details.append(self._l("Автор: {value}", value=book.author))
        if book.narrator:
            details.append(self._l("Чтец: {value}", value=book.narrator))
        if book.genre:
            details.append(self._l("Жанр: {value}", value=book.genre))
        if book.year:
            details.append(self._l("Год: {value}", value=book.year))
        details.append(self._l("Частей: {count}", count=parts))
        total_duration = sum(float(effective_track_duration(t) or 0.0) for t in book.tracks)
        if total_duration > 0:
            details.append(self._l("Длительность: {time}", time=fmt_time(total_duration)))
        self.book_summary.setText(" • ".join(details))
        self.book_description.setText(str(book.description or self._l("Описание отсутствует.")))
        cover = cover_cache_bytes(getattr(book, "cover_cache", None))
        self.book_cover_label.setText(self._l("Нет обложки"))
        self.book_cover_label.setPixmap(QPixmap())
        if cover:
            pix = QPixmap()
            if pix.loadFromData(cover):
                self.book_cover_label.setPixmap(pix)
                self.book_cover_label.setText("")
        self.easy_summary.setText(" • ".join(details))
        self.easy_cover_label.setPixmap(QPixmap())
        self.easy_cover_label.setText(self._l("Нет обложки"))
        if cover:
            easy_pix = QPixmap()
            if easy_pix.loadFromData(cover):
                self.easy_cover_label.setPixmap(easy_pix)
                self.easy_cover_label.setText("")
        self.easy_empty_hint.setVisible(False)
        self.easy_book_card.setVisible(True)
        self.easy_download_button.setEnabled(bool(book.tracks))
        self._refresh_player_context(book)
        self._update_narration_combo(book)
        enabled = parts > 0
        self.select_all_tracks_button.setEnabled(enabled)
        self.clear_tracks_button.setEnabled(enabled)
        self.download_all_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled and self.track_model.selected_count() > 0)
        self.full_mp3_button.setEnabled(enabled and self._book_supports_full_mp3(book))
        self.add_queue_button.setEnabled(enabled and self.track_model.selected_count() > 0)
        self._update_download_primary_button()
        if not enabled:
            # A failed/empty analysis must never arm a later unrelated book for
            # automatic queueing/downloading. This also lets multi-URL queue
            # imports continue to the next candidate.
            self._queue_after_analysis = False
            self._download_after_analysis = False
            self._queue_reanalyze_task_id = None
            if getattr(self, "_pending_queue_urls", None):
                QTimer.singleShot(0, self._queue_next_dropped_url)
        self.set_status(f"Анализ завершён. Найдено {parts} частей; выбрано {self.track_model.selected_count()}.")
        if not suppress_book_found_sound:
            self._play_event_sound("book_found")
        if enabled:
            if self.current_ui_mode() == "easy":
                self.easy_download_button.setFocus(Qt.FocusReason.OtherFocusReason)
            else:
                focus_table_row(self.track_table, 0, column=0, focus=True)
        if self._queue_reanalyze_task_id and enabled:
            task_id = self._queue_reanalyze_task_id
            self._queue_reanalyze_task_id = None
            for task in self.queue_tasks:
                if task.id != task_id:
                    continue
                old = task.request
                valid = {int(track.index) for track in book.tracks}
                if old.selected_indices is None:
                    selected = None
                else:
                    selected = [int(value) for value in old.selected_indices if int(value) in valid]
                    if not selected:
                        selected = [int(track.index) for track in book.tracks if bool(track.selected)]
                settings = {
                    "output_dir": str(old.output_dir),
                    "naming_mode": old.naming_mode,
                    "audio_preset": old.audio_preset,
                    "normalization_mode": old.normalization_mode,
                    "use_templates": old.use_templates,
                    "folder_template": old.folder_template,
                    "track_template": old.track_template,
                }
                try:
                    task.request = build_download_request(book, settings, selected)
                except Exception as exc:
                    task.status = "Требуется повторный анализ"
                    task.status_code = "needs_analysis"
                    task.paused = True
                    task.last_error = str(exc)
                else:
                    task.title = book.title or task.title
                    task.status = "Ожидает"
                    task.status_code = "pending"
                    task.paused = False
                    task.last_error = ""
                self._persist_queue()
                self._refresh_queue()
                break
        if self._queue_after_analysis and enabled:
            self._queue_after_analysis = False
            def _add_and_continue():
                self.add_current_to_queue()
                if getattr(self, "_pending_queue_urls", None):
                    QTimer.singleShot(0, self._queue_next_dropped_url)
            QTimer.singleShot(0, _add_and_continue)
        elif self._full_mp3_after_analysis and enabled:
            self._full_mp3_after_analysis = False
            QTimer.singleShot(0, self.start_full_mp3)
        elif self._download_after_analysis and enabled:
            self._download_after_analysis = False
            QTimer.singleShot(0, self.start_download)

    @Slot()
    def _clear_analysis_thread(self):
        self._finish_blocking_operation("analysis")
        self._analysis_thread = None
        self._analysis_worker = None
        self._analysis_cancel = None
        if self._exit_requested:
            return
        self.cancel_analysis_button.setEnabled(False)
        self._set_analysis_button_state(False)

    @Slot()
    def cancel_analysis(self):
        if self._analysis_cancel is None:
            return
        self._analysis_cancel.set()
        self.cancel_analysis_button.setEnabled(False)
        self._set_analysis_button_state(True, cancelling=True)
        self.set_status("Запрошена отмена анализа…")

    def _set_all_tracks_selected(self, selected: bool):
        self.track_model.set_all_selected(selected)
        self._announce_track_selection()

    @Slot()
    def _track_selection_changed(self, *_args):
        self._announce_track_selection()

    def _announce_track_selection(self):
        if self.current_book is None:
            return
        selected = self.track_model.selected_count()
        total = len(self.current_book.tracks)
        downloading = self._download_thread is not None and self._download_thread.isRunning()
        self.download_button.setEnabled(selected > 0 and not downloading and not self._queue_running)
        self.full_mp3_button.setEnabled(self._book_supports_full_mp3(self.current_book) and not downloading and not self._queue_running)
        self.add_queue_button.setEnabled(selected > 0 and not downloading)
        self._update_download_primary_button()
        self.set_status(f"Выбрано частей: {selected} из {total}.")

    def _live_download_settings(self) -> dict:
        data = self._settings_from_ui()
        if self.current_ui_mode() == "easy":
            folder = self.easy_output_edit.text().strip()
            if folder:
                data["output_dir"] = folder
                self.output_edit.setText(folder)
                self.book_output_edit.setText(folder)
            quality = str(self.easy_quality_combo.currentData() or "standard")
            data["quality_preset"] = quality
            if quality == "phone":
                data.update({"audio_preset":"64k_mono", "normalization_mode":"off", "normalize_audio":False})
            elif quality == "normalize":
                data.update({"audio_preset":"128k_stereo", "normalization_mode":"two_pass", "normalize_audio":True})
            else:
                data.update({"audio_preset":"copy", "normalization_mode":"off", "normalize_audio":False})
        return data

    @staticmethod
    def _book_supports_full_mp3(book: Book | None) -> bool:
        if book is None or not getattr(book, "tracks", None):
            return False
        sources: list[str] = []
        for track in book.tracks:
            url = str(getattr(track, "file", "") or "").strip()
            if url and url not in sources:
                sources.append(url)
        return len(sources) == 1

    def _launch_download(self, request, settings: dict, *, from_queue: bool = False, mode: str = "selected"):
        cancel_event = threading.Event()
        # The downloader mutates Track status/duration fields. Give the worker an
        # isolated snapshot so the GUI thread never reads the same Book object
        # concurrently. The completed snapshot is merged back in _download_finished.
        # Native GUI image objects are not deepcopy-safe; only the canonical
        # byte-based cover cache crosses the worker boundary.
        snapshot_source = request
        raw_cover = getattr(getattr(request, "book", None), "cover_cache", None)
        normalized_cover = normalize_cover_cache(raw_cover)
        if raw_cover is not None and normalized_cover is None:
            snapshot_source = copy.copy(request)
            snapshot_source.book = copy.copy(request.book)
            snapshot_source.book.cover_cache = None
        elif getattr(request, "book", None) is not None and normalized_cover is not None:
            request.book.cover_cache = normalized_cover
        worker_request = copy.deepcopy(snapshot_source)
        thread = QThread(self)
        worker = _DownloadWorker(worker_request, settings, cancel_event, mode=mode)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.status.connect(self._download_status, Qt.ConnectionType.QueuedConnection)
        worker.log.connect(self._append_log, Qt.ConnectionType.QueuedConnection)
        worker.stage.connect(self._download_stage, Qt.ConnectionType.QueuedConnection)
        worker.progress.connect(self._download_progress_changed, Qt.ConnectionType.QueuedConnection)
        worker.transfer.connect(self._download_transfer, Qt.ConnectionType.QueuedConnection)
        worker.missing_media.connect(self._resolve_missing_media, Qt.ConnectionType.QueuedConnection)
        worker.history_changed.connect(self._load_history, Qt.ConnectionType.QueuedConnection)
        worker.request_changed.connect(self._download_request_changed, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(self._download_finished, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._clear_download_thread, Qt.ConnectionType.QueuedConnection)
        thread.finished.connect(thread.deleteLater)
        self._download_cancel = cancel_event
        self._download_thread = thread
        self._download_worker = worker
        self._active_download_mode = str(mode or "selected")
        self.download_progress.setValue(0)
        self.download_stage_label.setText(self._l("Скачивание: подготовка"))
        self.download_speed_label.setText(self._l("Скорость: —"))
        self.speed_graph.clear()
        self.speed_graph.setVisible(False)
        self.download_all_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.full_mp3_button.setEnabled(False)
        self.add_queue_button.setEnabled(False)
        self.cancel_download_button.setEnabled(True)
        self.cancel_download_button.setVisible(True)
        self.analyze_button.setEnabled(False)
        self.cancel_analysis_button.setEnabled(False)
        self.download_menu_button.setEnabled(False)
        self.book_url_edit.setEnabled(False)
        self.select_all_tracks_button.setEnabled(False)
        self.clear_tracks_button.setEnabled(False)
        self.track_table.setEnabled(False)
        if from_queue:
            task = self._active_queue_task()
            self.set_status(f"Очередь: начинаю {task.title if task else 'книгу'}.")
        else:
            if mode == "full_mp3":
                self.set_status("Начинаю скачивание книги одним MP3.")
            else:
                self.set_status(f"Начинаю скачивание выбранных частей: {len(request.resolved_selected_indices())}.")
            self._show_blocking_operation(
                "download",
                title=tr(self.language, "status_downloading"),
                message=self._l("Скачивание: подготовка"),
                cancel_callback=self.cancel_download,
                progress=0,
            )
        self._refresh_queue()
        self._play_event_sound("download_start")
        thread.start()

    @Slot()
    def start_download(self):
        if self._download_thread is not None and self._download_thread.isRunning():
            self.set_status("Скачивание уже выполняется.")
            return
        if self._queue_running:
            self.set_status("Сначала остановите очередь загрузок.", assertive=True)
            return
        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            self.set_status("Дождитесь завершения анализа книги.", assertive=True)
            return
        if self.current_book is None:
            self.set_status("Сначала проанализируйте книгу.", assertive=True)
            return
        selected = self.track_model.selected_indices()
        live_settings = self._live_download_settings()
        force_redownload = bool(getattr(self, "_history_redownload_confirmed", False))
        self._history_redownload_confirmed = False
        try:
            request = build_download_request(self.current_book, live_settings, selected)
        except Exception as exc:
            self.set_status(str(exc), assertive=True)
            self._show_message(QMessageBox.Icon.Warning, "Скачивание", str(exc))
            return
        service = DownloadService(settings=live_settings)
        try:
            duplicate = service.duplicate_preflight(request, probe_durations=False)
        except Exception:
            duplicate = None
        if duplicate is not None and duplicate.exact_duplicate and force_redownload:
            service.delete_existing_outputs(request)
        elif duplicate is not None and duplicate.exact_duplicate:
            box = QMessageBox(self)
            configure_accessible(box, identifier="duplicate_dialog")
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle(tr(self.language, "duplicate_title"))
            box.setText(tr(self.language, "duplicate_text"))
            open_button = box.addButton(tr(self.language, "open_folder"), QMessageBox.ButtonRole.AcceptRole)
            redownload_button = box.addButton(self._l("Скачать заново"), QMessageBox.ButtonRole.DestructiveRole)
            cancel_button = box.addButton(self._l("Отмена"), QMessageBox.ButtonRole.RejectRole)
            configure_accessible(open_button, identifier="duplicate_open_folder")
            configure_accessible(redownload_button, identifier="duplicate_redownload")
            configure_accessible(cancel_button, identifier="duplicate_cancel")
            box.setEscapeButton(cancel_button)
            box.exec()
            if box.clickedButton() is open_button:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(duplicate.folder)))
                self.last_completed_folder = str(duplicate.folder)
                self.easy_open_folder_button.setEnabled(True)
                self.easy_listen_button.setEnabled(True)
                self._play_event_sound("files_already_downloaded")
                return
            if box.clickedButton() is redownload_button:
                service.delete_existing_outputs(request)
            else:
                return
        self._active_queue_task_id = None
        self._launch_download(request, live_settings)

    @Slot()
    def start_download_all(self):
        if self.current_book is None:
            self.set_status("Сначала проанализируйте книгу.", assertive=True)
            return
        self._set_all_tracks_selected(True)
        self.start_download()

    @Slot()
    def start_full_mp3(self):
        if self._download_thread is not None and self._download_thread.isRunning():
            self.set_status("Скачивание уже выполняется.")
            return
        if self._queue_running:
            self.set_status("Сначала остановите очередь загрузок.", assertive=True)
            return
        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            self.set_status("Дождитесь завершения анализа книги.", assertive=True)
            return
        if self.current_book is None:
            self.set_status("Сначала проанализируйте книгу.", assertive=True)
            return
        if not self._book_supports_full_mp3(self.current_book):
            message = "У книги несколько исходных файлов. Используйте скачивание по частям."
            self.set_status(message, assertive=True)
            self._show_message(QMessageBox.Icon.Information, self._l("Одним MP3"), message)
            return
        live_settings = self._live_download_settings()
        try:
            request = build_download_request(self.current_book, live_settings, None)
        except Exception as exc:
            self.set_status(str(exc), assertive=True)
            self._show_message(QMessageBox.Icon.Warning, self._l("Одним MP3"), str(exc))
            return
        service = DownloadService(settings=live_settings)
        try:
            duplicate = service.duplicate_preflight(request, full_mp3=True, probe_durations=False)
        except Exception:
            duplicate = None
        if duplicate is not None and duplicate.exact_duplicate:
            box = QMessageBox(self)
            configure_accessible(box, identifier="duplicate_dialog")
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle(tr(self.language, "duplicate_title"))
            box.setText(tr(self.language, "duplicate_text"))
            open_button = box.addButton(tr(self.language, "open_folder"), QMessageBox.ButtonRole.AcceptRole)
            redownload_button = box.addButton(self._l("Скачать заново"), QMessageBox.ButtonRole.DestructiveRole)
            cancel_button = box.addButton(self._l("Отмена"), QMessageBox.ButtonRole.RejectRole)
            configure_accessible(open_button, identifier="duplicate_open_folder")
            configure_accessible(redownload_button, identifier="duplicate_redownload")
            configure_accessible(cancel_button, identifier="duplicate_cancel")
            box.setEscapeButton(cancel_button)
            box.exec()
            if box.clickedButton() is open_button:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(duplicate.folder)))
                self.last_completed_folder = str(duplicate.folder)
                self.easy_open_folder_button.setEnabled(True)
                self.easy_listen_button.setEnabled(True)
                self._play_event_sound("files_already_downloaded")
                return
            if box.clickedButton() is redownload_button:
                service.delete_existing_outputs(request, full_mp3=True)
            else:
                return
        self._active_queue_task_id = None
        self._launch_download(request, live_settings, mode="full_mp3")

    def _request_download_cancel(self) -> bool:
        cancel = self._download_cancel
        if cancel is None:
            return False
        cancel.set()
        prompt = self._active_missing_prompt
        if prompt is not None:
            prompt.resolve("stop")
        box = self._active_missing_box
        if box is not None:
            try:
                # reject() exits QMessageBox.exec(); do not force-close/delete the
                # C++ object while _resolve_missing_media still owns it.
                box.reject()
            except RuntimeError:
                pass
        return True

    @Slot()
    def cancel_download(self):
        if not self._request_download_cancel():
            return
        self.cancel_download_button.setEnabled(False)
        self.set_status("Запрошена отмена скачивания…", assertive=True)

    @Slot(str)
    def _download_status(self, message: str):
        if message:
            self.set_status(message)
            self._update_blocking_operation(
                "download", message=self._rt(message)
            )

    @Slot(int, str)
    def _download_stage(self, number: int, text: str):
        stage_prefix = self._l("Этап")
        stage_text = self._rt(str(text or ""))
        label = f"{stage_prefix} {number}/5: {stage_text}" if number else f"{stage_prefix}: {stage_text}"
        self.download_stage_label.setText(label)
        self._update_blocking_operation("download", message=label)

    @Slot(float)
    def _download_progress_changed(self, value: float):
        percent = max(0, min(100, int(round(value))))
        self.download_progress.setValue(percent)
        self._update_blocking_operation("download", progress=percent)

    @Slot(float, int)
    def _download_transfer(self, bytes_per_second: float, active_segments: int):
        mib = max(0.0, float(bytes_per_second or 0.0)) / (1024 * 1024)
        if mib > 0:
            self.speed_graph.setVisible(True)
            self.speed_graph.add_speed(mib)
            self.download_speed_label.setText(self._l("Скорость: {mib} МБ/с • Range: {segments}", mib=f"{mib:.2f}", segments=int(active_segments)))
        else:
            if self.speed_graph.isVisible():
                self.speed_graph.add_speed(0.0)
            self.download_speed_label.setText(self._l("Скорость: —"))

    @Slot(object)
    def _resolve_missing_media(self, prompt):
        if not isinstance(prompt, _MissingMediaDecision):
            return
        if prompt.event.is_set() or (self._download_cancel is not None and self._download_cancel.is_set()):
            prompt.resolve("stop")
            return
        if not self.isVisible() and self._tray_available():
            self.tray_controller.notify("Загрузка требует решения пользователя. Открываю окно программы.")
            self.restore_from_tray()
        indices = prompt.indices
        if len(indices) == 1:
            parts_text = self._l("Часть {index} недоступна на сервере.", index=indices[0])
        else:
            shown = ", ".join(str(x) for x in indices[:16])
            suffix = "…" if len(indices) > 16 else ""
            parts_text = self._l("Недоступны части: {parts}.", parts=shown + suffix)
        text = parts_text + "\n\n" + self._l("Программа уже обновила плейлист, но файл всё равно отсутствует.")
        if prompt.detail:
            text += "\n\n" + prompt.detail
        dialog_parent = (
            self._operation_dialog
            if getattr(self, "_operation_dialog_kind", "") == "download" and self._operation_dialog is not None
            else self
        )
        box = QMessageBox(dialog_parent)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self._l("Недоступная часть аудиокниги"))
        box.setText(text)
        box.setWindowModality(Qt.WindowModality.ApplicationModal)
        box.setModal(True)
        configure_accessible(box, name=self._l("Недоступная часть аудиокниги"), description=text, identifier="missing_media_dialog")
        stop_button = box.addButton(self._l("Остановить загрузку"), QMessageBox.ButtonRole.RejectRole)
        configure_accessible(stop_button, name=self._l("Остановить загрузку"), identifier="missing_media_stop")
        skip_button = None
        if prompt.allow_skip:
            skip_text = self._l("Пропустить часть и продолжить") if len(indices) == 1 else self._l("Пропустить эти части и продолжить")
            skip_button = box.addButton(skip_text, QMessageBox.ButtonRole.AcceptRole)
            configure_accessible(skip_button, name=skip_text, identifier="missing_media_skip")
        box.setDefaultButton(stop_button)
        box.setEscapeButton(stop_button)
        box.finished.connect(
            lambda _code: prompt.resolve("stop") if not prompt.event.is_set() else None
        )
        box.destroyed.connect(
            lambda *_args: prompt.resolve("stop") if not prompt.event.is_set() else None
        )

        # The worker waits for this modal decision. If cancellation is requested
        # from closing, queue pause/stop, or another controller path, close the
        # modal as well so the GUI cannot remain application-modal after the
        # worker has already chosen "stop".
        cancel_watch = QTimer(box)
        cancel_watch.setInterval(100)
        cancel_watch.timeout.connect(
            lambda: box.reject()
            if prompt.event.is_set() or (self._download_cancel is not None and self._download_cancel.is_set())
            else None
        )
        self._active_missing_prompt = prompt
        self._active_missing_box = box
        cancel_watch.start()
        clicked_button = None
        try:
            try:
                box.exec()
                clicked_button = box.clickedButton()
            except RuntimeError:
                # The dialog may already have been destroyed during application
                # shutdown. Treat that path as the safe "stop" decision.
                clicked_button = None
        finally:
            try:
                cancel_watch.stop()
            except RuntimeError:
                pass
            if self._active_missing_prompt is prompt:
                self._active_missing_prompt = None
            if self._active_missing_box is box:
                self._active_missing_box = None
        prompt.resolve("skip" if skip_button is not None and clicked_button is skip_button else "stop")

    @Slot(object)
    def _download_request_changed(self, request):
        """Persist worker-side source fallback immediately for queue recovery."""
        queue_task = self._active_queue_task()
        if queue_task is None or request is None:
            return
        try:
            queue_task.request = request
            queue_task.title = request.book.title or request.book.url
            self._persist_queue()
            self._refresh_queue()
        except Exception as exc:
            self._append_log(f"Не удалось сохранить обновлённый источник очереди: {exc}")

    @Slot(object)
    def _download_finished(self, result):
        kind, payload = result
        self._finish_blocking_operation("download")
        self.speed_graph.set_transfer_active(False)
        self.speed_graph.setVisible(False)
        self.cancel_download_button.setEnabled(False)
        queue_task = self._active_queue_task()
        if queue_task is not None:
            if kind == "cancelled":
                if self._queue_pausing:
                    queue_task.status = "На паузе"
                    queue_task.status_code = "paused"
                    queue_task.paused = True
                    self.set_status(f"На паузе: {queue_task.title}", assertive=True)
                    self._play_event_sound("download_paused")
                else:
                    queue_task.status = "Незавершено"
                    queue_task.status_code = "interrupted"
                    queue_task.paused = False
                    self.set_status(f"Очередь остановлена на книге: {queue_task.title}", assertive=True)
            elif kind == "error":
                queue_task.status = "Ошибка"
                queue_task.status_code = "error"
                queue_task.last_error = str(payload)
                queue_task.paused = False
                self.set_status(f"Ошибка в очереди: {queue_task.title}: {payload}", assertive=True)
                self._notify_tray_if_hidden(f"Ошибка в очереди: {queue_task.title}")
                self._play_event_sound("error")
            elif isinstance(payload, DownloadResult):
                queue_task.status = "Готово"
                queue_task.status_code = "completed"
                queue_task.output_folder = str(payload.folder)
                queue_task.last_error = ""
                queue_task.paused = False
                self.download_progress.setValue(100)
                self.download_stage_label.setText(self._l("Этап 5/5: Готово"))
                self.set_status(f"Готово: {queue_task.title}", assertive=True)
                self.last_completed_folder = str(payload.folder)
                if payload.book is not None:
                    queue_task.request.book = payload.book
                if (
                    self.current_book is not None
                    and normalize_supported_url(str(self.current_book.url or ""))
                    == normalize_supported_url(str(queue_task.request.book.url or ""))
                ):
                    self.current_book = queue_task.request.book
                    self.track_model.set_book(self.current_book)
                self.last_completed_book = queue_task.request.book
                self._refresh_player_context(self.last_completed_book)
                self.easy_open_folder_button.setEnabled(True)
                self.easy_listen_button.setEnabled(True)
                self._play_event_sound("download_complete")
                self._load_history()
            self._persist_queue()
            self._refresh_queue()
            self._refresh_unfinished()
            return

        if kind == "cancelled":
            self.download_stage_label.setText(self._l("Скачивание: отменено"))
            self.set_status("Скачивание отменено пользователем.", assertive=True)
            self._play_event_sound("download_cancelled")
        elif kind == "error":
            self.download_stage_label.setText(self._l("Скачивание: ошибка"))
            self.set_status("Ошибка скачивания: " + str(payload), assertive=True)
            self._notify_tray_if_hidden("Ошибка скачивания. Откройте окно программы для подробностей.")
            self._play_event_sound("error")
            if self.isVisible():
                self._show_message(QMessageBox.Icon.Critical, "Ошибка скачивания", str(payload))
        elif isinstance(payload, DownloadResult):
            self.download_progress.setValue(100)
            self.download_stage_label.setText(self._l("Этап 5/5: Готово"))
            skipped = list(payload.skipped_indices or [])
            if skipped:
                self.set_status(
                    "Скачивание завершено. Пропущены недоступные части: "
                    + ", ".join(map(str, skipped)),
                    assertive=True,
                )
            else:
                if payload.target_file is not None:
                    self.set_status(f"Полный MP3 сохранён: {payload.target_file}", assertive=True)
                else:
                    self.set_status(f"Скачивание завершено: {payload.folder}", assertive=True)
            self.last_completed_folder = str(payload.folder)
            if payload.book is not None:
                self.current_book = payload.book
            self.last_completed_book = self.current_book
            self._refresh_player_context(self.last_completed_book)
            self.easy_open_folder_button.setEnabled(True)
            self.easy_listen_button.setEnabled(True)
            self._play_event_sound("download_complete")
            self._notify_tray_if_hidden("Скачивание аудиокниги завершено.")
            self._load_history()
        self.track_model.set_book(self.current_book)
        self.play_selected_track_button.setEnabled(False)
        self._refresh_unfinished()

    @Slot()
    def _clear_download_thread(self):
        self._finish_blocking_operation("download")
        had_queue_task = self._active_queue_task_id is not None
        self._download_thread = None
        self._download_worker = None
        self._download_cancel = None
        self._active_download_mode = "selected"
        if self._exit_requested:
            self._active_queue_task_id = None
            return
        self.book_url_edit.setEnabled(True)
        has_book = self.current_book is not None and bool(getattr(self.current_book, "tracks", None))
        self.select_all_tracks_button.setEnabled(has_book)
        self.clear_tracks_button.setEnabled(has_book)
        self.track_table.setEnabled(has_book)
        self.download_all_button.setEnabled(has_book and not self._queue_running)
        self.download_button.setEnabled(has_book and self.track_model.selected_count() > 0 and not self._queue_running)
        self.full_mp3_button.setEnabled(has_book and self._book_supports_full_mp3(self.current_book) and not self._queue_running)
        self.add_queue_button.setEnabled(has_book and self.track_model.selected_count() > 0)
        self.cancel_download_button.setEnabled(False)
        self.cancel_download_button.setVisible(False)
        self._set_analysis_button_state(False)
        self._update_download_primary_button()
        self._active_queue_task_id = None
        self._refresh_queue()
        if had_queue_task:
            if self._queue_pausing:
                self._queue_pausing = False
                self._queue_running = False
                self._refresh_queue()
            elif self._queue_stop_requested:
                self._queue_stop_requested = False
                self._queue_running = False
                self._refresh_queue()
            elif self._queue_running:
                QTimer.singleShot(0, self._start_next_queue_task)


__all__ = ["AnalysisDownloadUiMixin"]
