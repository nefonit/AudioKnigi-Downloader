"""Offline catalogue regressions: fallback, links and malformed source data."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
import requests
from bs4 import BeautifulSoup

from audioknigi.core import SiteStructureChanged
from audioknigi.providers.sources_ext import librivox, uknig, izib, yakniga


def test_librivox_404_for_title_still_searches_author(monkeypatch):
    queried = []

    def request(_url, *, params, **_kwargs):
        field = "title" if "title" in params else "author"
        queried.append(field)
        if field == "title":
            response = requests.Response()
            response.status_code = 404
            raise requests.HTTPError("Not Found", response=response)
        return SimpleNamespace(json=lambda: {"books": []})

    monkeypatch.setattr(librivox, "_request", request)
    assert librivox._librivox_search_from_catalogue("Unknown Writer") == []
    assert queried == ["title", "author"]


def test_librivox_non404_error_is_not_hidden(monkeypatch):
    response = requests.Response()
    response.status_code = 503

    def request(*_args, **_kwargs):
        raise requests.HTTPError("Unavailable", response=response)

    monkeypatch.setattr(librivox, "_request", request)
    with pytest.raises(requests.HTTPError):
        librivox._librivox_search_from_catalogue("Book")


def test_librivox_blank_query_does_not_contact_archive(monkeypatch):
    monkeypatch.setattr(
        librivox, "_request", lambda *_a, **_kw: pytest.fail("unexpected request")
    )
    assert librivox.search_librivox("   ") == []


def test_uknig_prefers_named_book_link_over_empty_cover(monkeypatch):
    html = (
        '<div class="book-item">'
        '<a href="/books/123"><img src="cover.jpg" alt=""></a>'
        '<a href="/books/123">Правильное название</a>'
        '</div>'
    )
    monkeypatch.setattr(
        uknig, "_soup",
        lambda *_a, **_kw: BeautifulSoup(html, "html.parser"),
    )
    results = uknig.search_uknig("Название")
    assert len(results) == 1
    assert results[0].title == "Правильное название"


def test_izib_canonicalizes_search_result_url():
    html = BeautifulSoup(
        '<div><a href="/art/123/?ref=search#comments">Название книги</a></div>',
        "html.parser",
    )
    item = izib._izib_search_card(html, "https://izib.uk/")
    assert item is not None
    assert "ref=search" not in item.url
    assert "#comments" not in item.url


def test_yakniga_invalid_chapter_payload_raises_site_structure(monkeypatch):
    monkeypatch.setattr(
        yakniga._compat, "_yakniga_payload",
        lambda *_a: {"book": {"title": "Book", "chapters": ["bad", "payload"]}},
    )
    with pytest.raises(SiteStructureChanged, match="списка глав"):
        yakniga.fetch_yakniga("https://yakniga.org/author/book")
