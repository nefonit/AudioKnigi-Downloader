"""Public headless download orchestration entrypoint.

The execution engine is loaded lazily so original monkeypatch and extension
points on ``audioknigi.download_engine`` continue to work.
"""
from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
import threading
from ..config.settings import normalize_settings
from ..services.download_request import DownloadRequest
from .contracts import DownloadCallbacks, DownloadResult, DuplicatePreflight

class DownloadService:
    """Public GUI-neutral façade for one book download."""

    def __init__(
        self,
        *,
        settings: Mapping[str, object] | None = None,
        cancel_event: threading.Event | None = None,
        callbacks: DownloadCallbacks | None = None,
    ) -> None:
        self.settings = normalize_settings(settings)
        self.cancel_event = cancel_event or threading.Event()
        self.callbacks = callbacks or DownloadCallbacks()

    def download(self, request: DownloadRequest) -> DownloadResult:
        from ..download_engine import _DownloadEngine
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.run()

    def download_full_mp3(self, request: DownloadRequest) -> DownloadResult:
        from ..download_engine import _DownloadEngine
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.run_full_mp3()

    def duplicate_preflight(
        self, request: DownloadRequest, *, full_mp3: bool = False, probe_durations: bool = True
    ) -> DuplicatePreflight:
        from ..download_engine import _DownloadEngine
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.duplicate_preflight(full_mp3=full_mp3, probe_durations=probe_durations)

    def recover_completed_download(
        self, request: DownloadRequest, *, full_mp3: bool = False
    ) -> DownloadResult | None:
        """Reconcile a crash-interrupted queue task without repeating complete work.

        Verify existing audio and matching metadata before repairing history.
        Partial chapter selections are left to the normal resumable downloader.
        This is deliberately called in the worker thread, never in the Qt UI.
        """
        from ..download_engine import _DownloadEngine
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        engine._check_cancel()
        preflight = engine.duplicate_preflight(full_mp3=full_mp3, probe_durations=True)
        if not preflight.exact_duplicate:
            return None

        folder = Path(preflight.folder)
        count = 1 if full_mp3 else len(list(getattr(request.book, "tracks", []) or []))
        engine._check_cancel()
        engine._add_history(request.book, folder, count)
        if not engine._history_metadata_matches_book(request.book, folder, expected_parts=count):
            # A history write may fail, in which case don't claim the queue
            # transaction finished. The ordinary resumable path is still safe.
            return None
        engine._remove_resume_manifest(request.book)
        return DownloadResult(
            folder=folder,
            selected_indices=list(request.resolved_selected_indices()),
            skipped_indices=[],
            target_file=engine._full_mp3_target(request.book, folder) if full_mp3 else None,
            book=request.book,
        )

    def delete_existing_outputs(self, request: DownloadRequest, *, full_mp3: bool = False) -> int:
        from ..download_engine import _DownloadEngine
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.delete_existing_outputs(full_mp3=full_mp3)


