from __future__ import annotations

import threading
from unittest.mock import Mock

import pytest

from audioknigi.core import SiteStructureChanged
from audioknigi.sources import (is_akniga_collection_url, is_supported_url,
                                 normalize_akniga_collection_url)
from audioknigi.providers import extra_sources
from audioknigi.services import search_service

COLLECTION = "https://akniga.org/collection/v-derevne-yavno-tvoritsya-kakaya-to-hren/"

HTML = """<html><main><div class='content__main'><div class='content__main__articles'>
<div class='content__main__articles--item'>
 <div class='article--cover'><a href='/kniga-testovaya-istoriya'><img alt='Автор – Тестовая история'></a></div>
 <span class='link__action--author'><a href='/author/author'>Автор</a><a href='/performer/narrator'>Чтец</a></span>
</div><div class='content__main__articles--item'>
 <div class='article--cover'><a href='/drugaya-audiokniga'><img alt='Другая аудиокнига'></a></div>
</div><div class='content__main__articles--item'>
 <div class='article--cover'><a href='/collection/not-a-book/'><img alt='Подборка'></a></div>
</div>
</div></div></main><footer><a href='/chuzhaya-kniga'>Не книга коллекции</a></footer></html>"""


def test_collection_is_not_a_playable_book():
    assert is_akniga_collection_url(COLLECTION)
    assert is_akniga_collection_url("www.akniga.org/collection/test-collection/?utm_source=x")
    assert not is_supported_url(COLLECTION)
    assert normalize_akniga_collection_url(COLLECTION + "?tracking=1#part") == COLLECTION
    for url in ("https://akniga.org.evil.org/collection/foo/",
                "https://akniga.org/collection/", "https://akniga.org/collection/foo/extra/",
                "https://akniga.org/page/faq/", "javascript:alert(1)"):
        assert not is_akniga_collection_url(url)


def test_collection_cards_to_search_rows():
    books = extra_sources.parse_akniga_collection(HTML)
    assert len(books) == 2
    assert books[0].title == "Тестовая история"
    assert books[0].author == "Автор"
    assert books[0].url == "https://akniga.org/kniga-testovaya-istoriya"


def test_collection_anchor_fallback_and_dedup():
    html = "<main><div class='content__main'><a href='/odin-raz'><img alt='Одна книга'></a><a href='/odin-raz'>Одна книга</a></div></main>"
    items = extra_sources.parse_akniga_collection(html)
    assert len(items) == 1
    assert items[0].title == "Одна книга"


def test_collection_without_books_reports_structure_error():
    with pytest.raises(SiteStructureChanged):
        extra_sources.parse_akniga_collection("<main><p>No books</p></main>")


def test_collection_search_dispatches_without_global_search(monkeypatch):
    monkeypatch.setattr(extra_sources, "fetch_akniga_collection",
                        lambda url, cancel_event=None: extra_sources.parse_akniga_collection(HTML))
    monkeypatch.setattr(search_service, "registered_providers", lambda: (_ for _ in ()).throw(AssertionError("global search called")))
    outcome = search_service.search_all_sources(COLLECTION, sources=["knigavuhe.org"])
    assert not outcome.errors
    assert len(outcome.results) == 2
    assert outcome.results[0].source == "akniga.org"


def test_collection_search_cancelled(monkeypatch):
    from audioknigi.core import Cancelled
    cancel = threading.Event(); cancel.set()
    with pytest.raises(Cancelled):
        search_service.search_all_sources(COLLECTION, cancel_event=cancel)


def test_collection_fetch_url_normalized(monkeypatch):
    seen = []
    def fake_request(url, **kwargs):
        seen.append(url)
        return Mock(text=HTML)
    monkeypatch.setattr(extra_sources, "_request", fake_request)
    books = extra_sources.fetch_akniga_collection(COLLECTION + "?tracking=1")
    assert len(books) == 2
    assert seen == [COLLECTION]
