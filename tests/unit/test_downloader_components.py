import threading

from audioknigi.downloader import BandwidthLimiter, DownloaderMixin
from audioknigi.download import BookFlowMixin, MediaProcessingMixin, NetworkDownloadMixin, ProbeMixin, SourceAnalysisMixin


def test_downloader_facade_is_composed_from_focused_mixins():
    for base in (ProbeMixin, SourceAnalysisMixin, NetworkDownloadMixin, MediaProcessingMixin, BookFlowMixin):
        assert issubclass(DownloaderMixin, base)


def test_facade_keeps_public_methods_after_split():
    for name in ("_download_single", "_download_segmented", "_measure_loudnorm", "_process_book_once", "_analyze_book"):
        assert hasattr(DownloaderMixin, name)


def test_bandwidth_limiter_accepts_none_cancel_event():
    limiter = BandwidthLimiter(10_000_000)
    limiter.consume(1, None)


def test_bandwidth_limiter_honors_cancel_event():
    limiter = BandwidthLimiter(1)
    limiter.tokens = 0.0
    event = threading.Event(); event.set()
    from audioknigi.core import Cancelled
    try:
        limiter.consume(1, event)
    except Cancelled:
        pass
    else:
        raise AssertionError("cancelled limiter should raise Cancelled")
