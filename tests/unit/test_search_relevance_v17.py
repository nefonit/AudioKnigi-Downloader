"""Regression coverage for visible search relevance (V17)."""
from __future__ import annotations

from types import SimpleNamespace
import threading

import pytest

from audioknigi.models import SearchResult
from audioknigi.services import search_service
from audioknigi.services.search_relevance import search_relevance_rank


def book(title, *, source="akniga.org", author="", narrator=""):
    slug = str(abs(hash((title, source))))
    return SearchResult(title=title, author=author, narrator=narrator,
                        url="https://akniga.org/book-" + slug, source=source)


@pytest.mark.parametrize("title,expected", [
    ("Шерлок Холмс: Собака Баскервилей", 1),
    ("The Adventures of Sherlock Holmes", 1),
    ("Шерлок Холмс", 0),
    ("Арсен Люпен", 4),
    ("Театр у микрофона 18", 4),
    ("Тайна доктора Авроры", 4),
])
def test_sherlock_holmes_filters_unrelated_catalogue_titles(title, expected):
    assert search_relevance_rank("Sherlock Holmes", book(title)) == expected


def test_author_query_and_mixed_query_are_kept():
    assert search_relevance_rank("Артур Конан Дойл", book("Пестрая лента", author="Артур Конан Дойл")) == 2
    assert search_relevance_rank("Дойл Холмс", book("Шерлок Холмс", author="Конан Дойл")) == 3
    assert search_relevance_rank("The House", book("The House on the Borderland")) == 1


def test_bilingual_variants_are_matched_but_arbitrary_fuzzy_words_are_not():
    assert search_relevance_rank("Sherlock Holmes", book("Шерлок Холмс")) == 0
    assert search_relevance_rank("Шерлок Холмс", book("Sherlock Holmes")) == 0
    assert search_relevance_rank("Harry Potter", book("Гарри Поттер")) == 0
    assert search_relevance_rank("Sherlock Holmes", book("Холмс странный", author="Шерлоков")) == 4


def test_search_splits_verified_hits_from_possible_matches_without_losing_data(monkeypatch):
    class Fake:
        key = "akniga"
        display_name = "akniga.org"
        def search(self, query, *, cancel_event=None):
            return [book("Арсен Люпен"), book("Шерлок Холмс"), book("Театр у микрофона 18"),
                    book("The Adventures of Sherlock Holmes")]
        def enrich_search_results(self, rows, *, cancel_event=None):
            return rows
    monkeypatch.setattr(search_service, "registered_providers", lambda: (Fake(),))
    outcome = search_service.search_all_sources("Sherlock Holmes")
    assert [item.title for item in outcome.results] == ["Шерлок Холмс", "The Adventures of Sherlock Holmes"]
    assert [item.title for item in outcome.related_results] == ["Арсен Люпен", "Театр у микрофона 18"]
    assert outcome.source_count == 1
    assert not outcome.errors


def test_cancellation_not_swallowed_after_search(monkeypatch):
    from audioknigi.core import Cancelled
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(Cancelled):
        search_service.search_all_sources("Sherlock Holmes", cancel_event=cancelled)


def test_collection_short_circuit_bypasses_relevance_filter(monkeypatch):
    from audioknigi.providers import extra_sources
    url = "https://akniga.org/collection/example/"
    monkeypatch.setattr(extra_sources, "fetch_akniga_collection", lambda *_args, **_kw: [book("Арсен Люпен")])
    result = search_service.search_all_sources(url)
    assert len(result.results) == 1
    assert result.related_results == []


def test_ui_offers_explicit_toggle_for_related_matches():
    from pathlib import Path
    code = (Path(__file__).resolve().parents[2] / "audioknigi/qt/mixins/search.py").read_text(encoding="utf8")
    assert "self._show_related_search_action.setChecked(False)" in code
    assert "self._show_related_search_action.toggled.connect(self._toggle_related_search_results)" in code
    assert "visible.extend(outcome.related_results)" in code
