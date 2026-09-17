"""Compatibility facade for the GUI-neutral downloader core.

Implementation is split under :mod:`audioknigi.download`; existing imports of
``audioknigi.downloader.DownloaderMixin`` and the public helper classes remain
supported.
"""
from __future__ import annotations

from .core import DEFAULT_OUTPUT, Cancelled
from .download import (
    AdaptiveRangeController,
    BandwidthLimiter,
    BookFlowMixin,
    MediaProcessingMixin,
    MissingMediaSourceError,
    MissingSelectedTracksError,
    NetworkDownloadMixin,
    ProbeMixin,
    RangeUnsupported,
    SharedSourceTimelineError,
    SlidingSpeedMeter,
    SourceAnalysisMixin,
)


class DownloaderMixin(
    ProbeMixin,
    SourceAnalysisMixin,
    NetworkDownloadMixin,
    MediaProcessingMixin,
    BookFlowMixin,
):
    """Downloader facade with safe defaults for headless/focused hosts."""

    cancel_event = None
    runtime_output_dir = DEFAULT_OUTPUT
    runtime_naming_mode = "number"
    runtime_embed_tags = True
    runtime_delete_source = True

    def _check_cancel(self):
        cancel_event = getattr(self, "cancel_event", None)
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Операция отменена пользователем.")

    def log(self, _text):
        return None

    def set_status(self, _text):
        return None

    def set_progress(self, _value):
        return None

    def set_stage(self, _stage, _text):
        return None

    def record_transfer_metrics(self, _speed_bytes_per_sec, _active_segments=1):
        return None

    def ui(self, callback):
        return callback() if callable(callback) else None

    def _write_resume_manifest(self, _book, _selected_indices, **_kwargs):
        return None

    def _remove_resume_manifest(self, _book):
        return None

    def _add_history(self, _book, _folder, _parts):
        return None


__all__ = [
    "DownloaderMixin",
    "MissingMediaSourceError",
    "MissingSelectedTracksError",
    "SharedSourceTimelineError",
    "RangeUnsupported",
    "BandwidthLimiter",
    "AdaptiveRangeController",
    "SlidingSpeedMeter",
]
