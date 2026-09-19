from __future__ import annotations

import copy
import threading
import time

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QAbstractItemView, QTableWidget

from ..core import Cancelled
from ..download_engine import DownloadCallbacks, DownloadService
from ..integrations import audiobookshelf_get_libraries
from ..logging_utils import app_logger
from ..models import normalize_cover_cache
from ..services.book_analysis_service import AnalysisOptions, BookAnalysisService
from ..services.search_service import SearchOutcome, search_all_sources


class SearchWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)

    def __init__(self, query: str, cancel_event: threading.Event, *, sources=None, only_available: bool = False):
        super().__init__()
        self.query = query
        self.cancel_event = cancel_event
        self.sources = None if sources is None else tuple(sources)
        self.only_available = bool(only_available)

    @Slot()
    def run(self):
        app_logger.info("SEARCH WORKER | event=run_start | query=%r", self.query)
        try:
            outcome = search_all_sources(
                self.query,
                cancel_event=self.cancel_event,
                progress=self.progress.emit,
                sources=self.sources,
            )
            app_logger.info(
                "SEARCH WORKER | event=service_return | query=%r | results=%d | errors=%d",
                self.query, len(outcome.results), len(outcome.errors),
            )
            if self.only_available:
                outcome.results = [
                    item for item in outcome.results
                    if str(getattr(item, "availability", "") or "").casefold() == "available"
                ]
            if self.cancel_event.is_set():
                outcome = SearchOutcome(self.query, [], [])
            app_logger.info("SEARCH WORKER | event=finished_emit | query=%r", self.query)
            self.finished.emit(outcome)
            app_logger.info("SEARCH WORKER | event=finished_emit_return | query=%r", self.query)
        except Exception as exc:
            if self.cancel_event.is_set():
                self.finished.emit(SearchOutcome(self.query, [], []))
            else:
                app_logger.exception("Qt search worker failed")
                self.finished.emit(SearchOutcome(self.query, [], [str(exc)]))


class AudiobookshelfWorker(QObject):
    finished = Signal(object)

    def __init__(self, url: str, api_key: str):
        super().__init__()
        self.url = str(url or "")
        self.api_key = str(api_key or "")

    @Slot()
    def run(self):
        try:
            libraries = audiobookshelf_get_libraries(self.url, self.api_key)
            self.finished.emit(("ok", libraries))
        except Exception as exc:
            app_logger.exception("Qt Audiobookshelf worker failed")
            self.finished.emit(("error", str(exc)))


class AnalysisWorker(QObject):
    progress = Signal(str)
    finished = Signal(object)

    def __init__(self, url: str, cancel_event: threading.Event, options: AnalysisOptions):
        super().__init__()
        self.url = url
        self.cancel_event = cancel_event
        self.options = options

    @Slot()
    def run(self):
        try:
            service = BookAnalysisService(
                cancel_event=self.cancel_event,
                progress=self.progress.emit,
                options=self.options,
            )
            self.finished.emit(("ok", service.analyze(self.url)))
        except Cancelled:
            self.finished.emit(("cancelled", None))
        except Exception as exc:
            app_logger.exception("Qt analysis worker failed")
            self.finished.emit(("error", str(exc)))


class MissingMediaDecision:
    def __init__(self, indices: list[int], detail: str, allow_skip: bool):
        self.indices = list(indices)
        self.detail = str(detail or "")
        self.allow_skip = bool(allow_skip)
        self.event = threading.Event()
        self.value = "stop"

    def resolve(self, value: str):
        self.value = "skip" if str(value).lower() == "skip" else "stop"
        self.event.set()


class DownloadWorker(QObject):
    MISSING_MEDIA_DECISION_TIMEOUT_SECONDS = 30 * 60
    status = Signal(str)
    log = Signal(str)
    stage = Signal(int, str)
    progress = Signal(float)
    transfer = Signal(float, int)
    missing_media = Signal(object)
    history_changed = Signal()
    request_changed = Signal(object)
    finished = Signal(object)

    def __init__(self, request, settings: dict, cancel_event: threading.Event, mode: str = "selected"):
        super().__init__()
        # The engine may replace the book/selection when a media source is
        # refreshed or a cross-provider fallback is accepted.  Keep that
        # worker-side mutation isolated from the GUI/queue object; updates are
        # handed back explicitly through request_changed/result signals.  Native
        # Qt image objects are not deepcopy-safe, so normalize/clear cover_cache
        # at this boundary even when a caller forgot to prepare a snapshot.
        snapshot = request
        book = getattr(request, "book", None)
        if book is not None:
            raw_cover = getattr(book, "cover_cache", None)
            normalized_cover = normalize_cover_cache(raw_cover)
            if raw_cover is not None and normalized_cover is None:
                snapshot = copy.copy(request)
                snapshot.book = copy.copy(book)
                snapshot.book.cover_cache = None
            elif normalized_cover is not None and raw_cover is not normalized_cover:
                snapshot = copy.copy(request)
                snapshot.book = copy.copy(book)
                snapshot.book.cover_cache = normalized_cover
        self.request = copy.deepcopy(snapshot)
        self.settings = dict(settings or {})
        self.cancel_event = cancel_event
        self.mode = str(mode or "selected")

    def _missing_media(self, indices: list[int], detail: str, allow_skip: bool) -> str:
        prompt = MissingMediaDecision(indices, detail, allow_skip)
        self.missing_media.emit(prompt)
        deadline = time.monotonic() + self.MISSING_MEDIA_DECISION_TIMEOUT_SECONDS
        while not prompt.event.wait(0.1):
            if self.cancel_event.is_set():
                prompt.resolve("stop")
                return "stop"
            if time.monotonic() >= deadline:
                app_logger.error(
                    "Missing-media decision timed out after %ss; stopping download safely",
                    self.MISSING_MEDIA_DECISION_TIMEOUT_SECONDS,
                )
                prompt.resolve("stop")
                return "stop"
        return prompt.value

    @Slot()
    def run(self):
        callbacks = DownloadCallbacks(
            status=self.status.emit,
            log=self.log.emit,
            stage=self.stage.emit,
            progress=self.progress.emit,
            transfer=self.transfer.emit,
            missing_media=self._missing_media,
            history_changed=self.history_changed.emit,
            request_changed=lambda request: self.request_changed.emit(copy.deepcopy(request)),
        )
        try:
            service = DownloadService(
                settings=self.settings,
                cancel_event=self.cancel_event,
                callbacks=callbacks,
            )
            result = (
                service.download_full_mp3(self.request)
                if self.mode == "full_mp3"
                else service.download(self.request)
            )
            self.finished.emit(("ok", result))
        except Cancelled:
            self.finished.emit(("cancelled", None))
        except Exception as exc:
            app_logger.exception("Qt download worker failed")
            self.finished.emit(("error", str(exc)))


class QueueTableWidget(QTableWidget):
    """Queue table supporting accessible controls and mouse drag reorder."""

    rowsReordered = Signal(int, int)
    externalUrlsDropped = Signal(object)

    def __init__(self, rows: int, columns: int, parent=None):
        super().__init__(rows, columns, parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if event.source() is self or mime.hasUrls() or mime.hasText():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() is self or event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.source() is self:
            source_row = self.currentRow()
            target_row = self.rowAt(int(event.position().y()))
            if target_row < 0:
                target_row = max(0, self.rowCount() - 1)
            if source_row >= 0 and target_row >= 0 and source_row != target_row:
                self.rowsReordered.emit(source_row, target_row)
            event.acceptProposedAction()
            return
        values = []
        mime = event.mimeData()
        for url in mime.urls() if mime.hasUrls() else []:
            values.append(url.toLocalFile() if url.isLocalFile() else url.toString())
        if not values and mime.hasText():
            values.extend(str(mime.text() or "").splitlines())
        values = list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))
        if values:
            self.externalUrlsDropped.emit(values)
            event.acceptProposedAction()
            return
        super().dropEvent(event)


__all__ = [
    "SearchWorker", "AudiobookshelfWorker", "AnalysisWorker",
    "MissingMediaDecision", "DownloadWorker", "QueueTableWidget",
]
