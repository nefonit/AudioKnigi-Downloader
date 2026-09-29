from __future__ import annotations

from types import SimpleNamespace

from audioknigi import poleknig
from audioknigi.models import SearchResult


def _run_search(monkeypatch, query: str, rows: list[SearchResult], *, author_expanded=None):
    response = SimpleNamespace(text="", url="https://poleknig.com/search/")
    monkeypatch.setattr(poleknig, "_fetch_search_page", lambda *_a, **_k: response)
    monkeypatch.setattr(poleknig, "_search_last_page", lambda *_a, **_k: 1)
    monkeypatch.setattr(poleknig, "parse_search_results", lambda *_a, **_k: list(rows))
    monkeypatch.setattr(poleknig, "_hydrate_search_result_info", lambda item: (item, []))
    monkeypatch.setattr(poleknig, "_book_page_author_links", lambda *_a, **_k: [])
    monkeypatch.setattr(
        poleknig,
        "_expand_matching_author_catalogs",
        lambda *_a, **_k: list(author_expanded or []),
    )
    return poleknig.search(query)


def test_multiword_title_search_filters_broad_poleknig_hits(monkeypatch):
    rows = [
        SearchResult(title="Аль Капоне. Порядок вне закона", author="Екатерина Глаголева", narrator="Reader", url="https://poleknig.com/books/1", source="poleknig.com"),
        SearchResult(title="Наемник Айвэн 3: Закон и порядок", author="Юрий Уленгов", narrator="Reader", url="https://poleknig.com/books/2", source="poleknig.com"),
        SearchResult(title="Кошачий закон и порядок. Как найти общий язык с кошкой", author="София Царегородцева", narrator="Reader", url="https://poleknig.com/books/3", source="poleknig.com"),
        SearchResult(title="Экономика без догм. Как США создают новый экономический порядок", author="Автор", narrator="Reader", url="https://poleknig.com/books/4", source="poleknig.com"),
        SearchResult(title="Закон насилия и закон любви", author="Лев Толстой", narrator="Reader", url="https://poleknig.com/books/5", source="poleknig.com"),
    ]
    results = _run_search(monkeypatch, "Закон и порядок", rows)
    assert [item.title for item in results] == [
        "Наемник Айвэн 3: Закон и порядок",
        "Кошачий закон и порядок. Как найти общий язык с кошкой",
    ]


def test_exact_title_is_ranked_before_partial_title(monkeypatch):
    rows = [
        SearchResult(title="Кошачий закон и порядок", author="Автор 1", url="https://poleknig.com/books/1", source="poleknig.com"),
        SearchResult(title="Закон и порядок", author="Автор 2", url="https://poleknig.com/books/2", source="poleknig.com"),
        SearchResult(title="Наемник: Закон и порядок", author="Автор 3", url="https://poleknig.com/books/3", source="poleknig.com"),
    ]
    results = _run_search(monkeypatch, "Закон и порядок", rows)
    assert results[0].title == "Закон и порядок"
    assert {item.title for item in results[1:]} == {"Кошачий закон и порядок", "Наемник: Закон и порядок"}


def test_title_hit_suppresses_unrelated_author_name_hit(monkeypatch):
    rows = [
        SearchResult(title="Бесплатный тест-драйв материалов", author="Алекс Айвенго", url="https://poleknig.com/books/1", source="poleknig.com"),
        SearchResult(title="Айвенго", author="Вальтер Скотт", url="https://poleknig.com/books/2", source="poleknig.com"),
    ]
    results = _run_search(monkeypatch, "Айвенго", rows)
    assert [item.url for item in results] == ["https://poleknig.com/books/2"]


def test_author_search_keeps_author_catalog_when_no_title_hit(monkeypatch):
    rows = [
        SearchResult(title="Айвенго", author="Вальтер Скотт", url="https://poleknig.com/books/1", source="poleknig.com"),
        SearchResult(title="Квентин Дорвард", author="Вальтер Скотт", url="https://poleknig.com/books/2", source="poleknig.com"),
        SearchResult(title="Вальтер", author="Другой Автор", url="https://poleknig.com/books/3", source="poleknig.com"),
    ]
    expanded = [
        SearchResult(title="Роб Рой", author="Вальтер Скотт", url="https://poleknig.com/books/4", source="poleknig.com"),
    ]
    results = _run_search(monkeypatch, "Вальтер Скотт", rows, author_expanded=expanded)
    assert [item.url for item in results] == [
        "https://poleknig.com/books/4",
        "https://poleknig.com/books/1",
        "https://poleknig.com/books/2",
    ]


def test_extra_catalog_terms_still_keep_stable_two_word_title_phrase(monkeypatch):
    rows = [
        SearchResult(title="Гарри Поттер и философский камень", author="Джоан Роулинг", url="https://poleknig.com/books/1", source="poleknig.com"),
    ]
    results = _run_search(monkeypatch, "гарри поттер аудиокнига росмэн", rows)
    assert [item.url for item in results] == ["https://poleknig.com/books/1"]


def test_repeated_author_matches_beat_nonexact_one_word_title_hit(monkeypatch):
    rows = [
        SearchResult(title="Толстой о жизни", author="Другой Автор", url="https://poleknig.com/books/1", source="poleknig.com"),
        SearchResult(title="Война и мир", author="Лев Толстой", url="https://poleknig.com/books/2", source="poleknig.com"),
        SearchResult(title="Анна Каренина", author="Лев Толстой", url="https://poleknig.com/books/3", source="poleknig.com"),
    ]
    expanded = [
        SearchResult(title="Воскресение", author="Лев Толстой", url="https://poleknig.com/books/4", source="poleknig.com"),
    ]
    results = _run_search(monkeypatch, "Толстой", rows, author_expanded=expanded)
    assert [item.url for item in results] == [
        "https://poleknig.com/books/4",
        "https://poleknig.com/books/2",
        "https://poleknig.com/books/3",
    ]
