from __future__ import annotations

import weakref

from PySide6.QtCore import QObject, Slot

from ..logging_utils import app_logger


class WorkerUiRelay(QObject):
    """QObject receiver that guarantees worker callbacks enter the GUI thread.

    Several UI handlers live on Python mixins rather than directly on a QObject
    subclass. PySide can treat those bound callables as generic Python callables,
    so an explicit QueuedConnection alone is not a reliable receiver-context
    boundary. This relay is a real QObject created on the main thread; its slots
    forward to the window only after Qt has delivered the signal in that thread.
    """

    def __init__(self, owner) -> None:
        super().__init__(owner)
        self._owner_ref = weakref.ref(owner)

    def _owner(self):
        return self._owner_ref()

    @Slot(int, str)
    def search_progress(self, percent: int, message: str) -> None:
        owner = self._owner()
        if owner is not None:
            owner._search_progress_changed(percent, message)

    @Slot(object)
    def search_finished(self, outcome) -> None:
        owner = self._owner()
        if owner is not None:
            app_logger.info("WORKER UI RELAY | event=search_finished_dispatch")
            owner._search_finished(outcome)

    @Slot()
    def search_thread_finished(self) -> None:
        owner = self._owner()
        if owner is not None:
            owner._clear_search_thread()

    @Slot(str)
    def analysis_progress(self, message: str) -> None:
        owner = self._owner()
        if owner is not None:
            owner._analysis_progress_message(message)

    @Slot(object)
    def analysis_finished(self, result) -> None:
        owner = self._owner()
        if owner is not None:
            owner._analysis_finished(result)

    @Slot()
    def analysis_thread_finished(self) -> None:
        owner = self._owner()
        if owner is not None:
            owner._clear_analysis_thread()

    @Slot(str)
    def download_status(self, message: str) -> None:
        owner = self._owner()
        if owner is not None:
            owner._download_status(message)

    @Slot(str)
    def download_log(self, message: str) -> None:
        owner = self._owner()
        if owner is not None:
            owner._append_log(message)

    @Slot(int, str)
    def download_stage(self, number: int, text: str) -> None:
        owner = self._owner()
        if owner is not None:
            owner._download_stage(number, text)

    @Slot(float)
    def download_progress(self, value: float) -> None:
        owner = self._owner()
        if owner is not None:
            owner._download_progress_changed(value)

    @Slot(float, int)
    def download_transfer(self, bytes_per_second: float, active_segments: int) -> None:
        owner = self._owner()
        if owner is not None:
            owner._download_transfer(bytes_per_second, active_segments)

    @Slot(object)
    def download_missing_media(self, prompt) -> None:
        owner = self._owner()
        if owner is not None:
            owner._resolve_missing_media(prompt)

    @Slot()
    def download_history_changed(self) -> None:
        owner = self._owner()
        if owner is not None:
            owner._load_history()

    @Slot(object)
    def download_request_changed(self, request) -> None:
        owner = self._owner()
        if owner is not None:
            owner._download_request_changed(request)

    @Slot(object)
    def download_finished(self, result) -> None:
        owner = self._owner()
        if owner is not None:
            owner._download_finished(result)

    @Slot()
    def download_thread_finished(self) -> None:
        owner = self._owner()
        if owner is not None:
            owner._clear_download_thread()

    @Slot(object)
    def audiobookshelf_finished(self, result) -> None:
        owner = self._owner()
        if owner is not None:
            owner._audiobookshelf_finished(result)

    @Slot()
    def audiobookshelf_thread_finished(self) -> None:
        owner = self._owner()
        if owner is not None:
            owner._clear_abs_thread()


__all__ = ["WorkerUiRelay"]
