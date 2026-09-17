"""Focused, GUI-neutral downloader subsystems."""

from .book_flow import BookFlowMixin
from .errors import MissingMediaSourceError, MissingSelectedTracksError, RangeUnsupported, SharedSourceTimelineError
from .media import MediaProcessingMixin
from .network import AdaptiveRangeController, BandwidthLimiter, NetworkDownloadMixin, SlidingSpeedMeter
from .probe import ProbeMixin


def __getattr__(name):
    """Lazily expose imports that would otherwise create package cycles.

    ``book_analysis_service`` imports ``audioknigi.download.common``.  Python
    initializes this package before loading that submodule, so eagerly importing
    ``SourceAnalysisMixin`` here used to recurse back into
    ``book_analysis_service`` and fail with a partially initialized module.
    Keeping this one facade export lazy preserves the public API while allowing
    leaf download helpers to be imported independently.
    """
    if name == "SourceAnalysisMixin":
        from .source_analysis import SourceAnalysisMixin

        return SourceAnalysisMixin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | {"SourceAnalysisMixin"})


__all__ = [
    "MissingMediaSourceError",
    "MissingSelectedTracksError",
    "SharedSourceTimelineError",
    "RangeUnsupported",
    "BandwidthLimiter",
    "AdaptiveRangeController",
    "SlidingSpeedMeter",
    "NetworkDownloadMixin",
    "ProbeMixin",
    "SourceAnalysisMixin",
    "MediaProcessingMixin",
    "BookFlowMixin",
]
