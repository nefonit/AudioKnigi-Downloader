from __future__ import annotations

import json
from pathlib import Path

from audioknigi.models import SearchResult
from audioknigi.services.search_service import downloadable_search_results, search_result_sort_key

ROOT = Path(__file__).resolve().parents[2]


def _result(title: str, *, author: str = "", narrator: str = "", availability: str = "") -> SearchResult:
    return SearchResult(
        title=title,
        author=author,
        narrator=narrator,
        availability=availability,
        url=f"https://example.invalid/{title}",
        source="demo",
    )


def test_restricted_and_unavailable_results_are_filtered_but_unknown_is_preserved():
    rows = [
        _result("Available", availability="available"),
        _result("Restricted", availability="restricted"),
        _result("Unavailable", availability="unavailable"),
        _result("Unknown", availability=""),
    ]
    kept = downloadable_search_results(rows)
    assert [item.title for item in kept] == ["Available", "Unknown"]


def test_title_sort_puts_exact_query_first_then_shorter_titles_alphabetically():
    rows = [
        _result("Двойник запада"),
        _result("Двойник дурака"),
        _result("Двойник Декстера"),
        _result("Двойник"),
        _result("Двойник старого короля"),
    ]
    ordered = sorted(rows, key=lambda item: search_result_sort_key(item, "title", query="двойник"))
    assert [item.title for item in ordered] == [
        "Двойник",
        "Двойник Декстера",
        "Двойник дурака",
        "Двойник запада",
        "Двойник старого короля",
    ]


def test_author_and_narrator_sort_alphabetically_with_missing_values_last():
    rows = [
        _result("C", author="", narrator=""),
        _result("B", author="Толстой", narrator="Петров"),
        _result("A", author="Булгаков", narrator="Алексеев"),
    ]
    by_author = sorted(rows, key=lambda item: search_result_sort_key(item, "author"))
    by_narrator = sorted(rows, key=lambda item: search_result_sort_key(item, "narrator"))
    assert [item.author for item in by_author] == ["Булгаков", "Толстой", ""]
    assert [item.narrator for item in by_narrator] == ["Алексеев", "Петров", ""]


def test_search_ui_has_no_status_column_and_has_accessible_sort_controls():
    model = (ROOT / "audioknigi/qt/search_model.py").read_text(encoding="utf-8")
    search = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    easy = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert '("Статус", "availability")' not in model
    assert "search_only_available_action" not in search
    assert 'identifier="search_sort"' in search
    assert 'sort_title.triggered.connect(lambda: self._sort_search_results("title"))' in search
    assert "search_header.sectionClicked.connect(self._sort_search_results_by_column)" in search
    assert "easy_header.sectionClicked.connect(self._sort_search_results_by_column)" in easy


def test_book_download_layout_reserves_graph_and_description_geometry():
    pages = (ROOT / "audioknigi/qt/main_window_pages.py").read_text(encoding="utf-8")
    graph = (ROOT / "audioknigi/qt/speed_graph.py").read_text(encoding="utf-8")
    assert "self.download_activity_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)" in pages
    assert "self.book_details_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)" in pages
    assert "self.book_description.setMaximumHeight(72)" in pages
    assert "self.book_description.setMinimumHeight(52)" in pages
    assert "self._expanded_height = 56" in graph


def test_search_sort_strings_exist_for_all_supported_languages():
    messages = json.loads((ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8"))
    keys = {
        "search_sort_button",
        "search_sort_title",
        "search_sort_author",
        "search_sort_narrator",
        "search_sort_accessible",
        "search_sort_description",
        "search_sorted",
    }
    for language in ("ru", "uk", "de", "en"):
        assert keys <= set(messages[language])
        assert all(str(messages[language][key]).strip() for key in keys)
