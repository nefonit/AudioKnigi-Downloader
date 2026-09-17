from __future__ import annotations

from abc import ABC, abstractmethod
import threading
from typing import Iterable

from ..models import Book, SearchResult


class SourceProvider(ABC):
    """Stable contract implemented by every audiobook source adapter."""

    key: str
    display_name: str

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def canonicalize_url(self, url: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_book(self, url: str, *, cancel_event: threading.Event | None = None) -> Book:
        raise NotImplementedError

    def search(self, query: str, *, cancel_event: threading.Event | None = None) -> list[SearchResult]:
        return []

    def enrich_search_results(
        self,
        results: Iterable[SearchResult],
        *,
        cancel_event: threading.Event | None = None,
    ) -> list[SearchResult]:
        return list(results)
