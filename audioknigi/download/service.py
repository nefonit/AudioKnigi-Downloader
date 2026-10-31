"""Public headless download orchestration entrypoint.

The execution engine is loaded lazily so original monkeypatch and extension
points on ``audioknigi.download_engine`` continue to work.
"""
from __future__ import annotations
from collections.abc import Mapping
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

    def delete_existing_outputs(self, request: DownloadRequest, *, full_mp3: bool = False) -> int:
        from ..download_engine import _DownloadEngine
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.delete_existing_outputs(full_mp3=full_mp3)


