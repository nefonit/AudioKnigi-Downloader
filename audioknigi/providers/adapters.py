from __future__ import annotations

import threading
from collections.abc import Iterable

from .base import SourceProvider
from ..models import Book, SearchResult
from ..sources import AUDIOKNIGI_HOST, KNIGAVUHE_HOST, POLEKNIG_HOST, normalize_supported_url, source_key


class KnigavuheProvider(SourceProvider):
    key = "knigavuhe"
    display_name = KNIGAVUHE_HOST

    def supports_url(self, url: str) -> bool:
        return source_key(url) == self.key

    def canonicalize_url(self, url: str) -> str:
        return normalize_supported_url(url)

    def fetch_book(self, url: str, *, cancel_event: threading.Event | None = None) -> Book:
        from ..services.book_analysis_service import BookAnalysisService
        return BookAnalysisService(cancel_event=cancel_event).analyze(self.canonicalize_url(url))

    def search(self, query: str, *, cancel_event: threading.Event | None = None) -> list[SearchResult]:
        from ..knigavuhe import search
        return list(search(query, cancel_event=cancel_event) or [])

    def enrich_search_results(
        self,
        results: Iterable[SearchResult],
        *,
        cancel_event: threading.Event | None = None,
    ) -> list[SearchResult]:
        from ..knigavuhe import enrich_search_variants
        return list(enrich_search_variants(list(results), cancel_event=cancel_event) or [])


class PoleKnigProvider(SourceProvider):
    key = "poleknig"
    display_name = POLEKNIG_HOST

    def supports_url(self, url: str) -> bool:
        return source_key(url) == self.key

    def canonicalize_url(self, url: str) -> str:
        return normalize_supported_url(url)

    def fetch_book(self, url: str, *, cancel_event: threading.Event | None = None) -> Book:
        from ..services.book_analysis_service import BookAnalysisService
        return BookAnalysisService(cancel_event=cancel_event).analyze(self.canonicalize_url(url))

    def search(self, query: str, *, cancel_event: threading.Event | None = None) -> list[SearchResult]:
        from ..poleknig import search
        return list(search(query, cancel_event=cancel_event) or [])


class AudioknigiProvider(SourceProvider):
    """Provider contract for audioknigi.com.ua.

    Search lives in the provider layer; book analysis remains delegated to the
    GUI-independent analysis service until the shared PlayerJS analyzer is fully
    extracted from both download and analysis orchestration.
    """

    key = "audioknigi"
    display_name = AUDIOKNIGI_HOST

    def supports_url(self, url: str) -> bool:
        return source_key(url) == self.key

    def canonicalize_url(self, url: str) -> str:
        return normalize_supported_url(url)

    def fetch_book(self, url: str, *, cancel_event: threading.Event | None = None) -> Book:
        # The generic provider intentionally delegates to the headless analysis
        # service so callers do not need to know the site's PlayerJS details.
        from ..services.book_analysis_service import BookAnalysisService
        return BookAnalysisService(cancel_event=cancel_event).analyze(self.canonicalize_url(url))

    def search(self, query: str, *, cancel_event: threading.Event | None = None) -> list[SearchResult]:
        from .audioknigi_search import search_audioknigi
        return list(search_audioknigi(query, cancel_event=cancel_event) or [])
