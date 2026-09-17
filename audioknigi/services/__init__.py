"""GUI-independent application services used by the Qt desktop frontend and tests."""

from .book_analysis_service import AnalysisOptions, BookAnalysisService, analyze_book
from .download_request import DownloadRequest, build_download_request
from .search_service import SearchOutcome, search_all_sources

__all__ = [
    "AnalysisOptions",
    "BookAnalysisService",
    "DownloadRequest",
    "SearchOutcome",
    "analyze_book",
    "build_download_request",
    "search_all_sources",
]
