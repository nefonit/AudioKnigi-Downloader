"""akniga_catalog catalogue extraction and public search.

Shared request/session helpers live in the legacy facade until all consumers
can migrate. These delegations preserve existing monkeypatch contracts.
"""
from __future__ import annotations
import html
import json
import re
import threading
from pathlib import PurePosixPath
from urllib.parse import quote, urljoin, urlparse
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from ...core import Cancelled, SiteStructureChanged
from ...models import Book, Track, SearchResult
from ...sources import normalize_supported_url, is_supported_url, normalize_akniga_collection_url
from .. import extra_sources as _compat

_TIMEOUT = _compat._TIMEOUT
_SEARCH_LIMIT = _compat._SEARCH_LIMIT

def _check_cancel(*args, **kwargs):
    return _compat._check_cancel(*args, **kwargs)

def _request(*args, **kwargs):
    return _compat._request(*args, **kwargs)

def _clean(*args, **kwargs):
    return _compat._clean(*args, **kwargs)

def _text(*args, **kwargs):
    return _compat._text(*args, **kwargs)

def _href(*args, **kwargs):
    return _compat._href(*args, **kwargs)

def _public_media(*args, **kwargs):
    return _compat._public_media(*args, **kwargs)

def _track(*args, **kwargs):
    return _compat._track(*args, **kwargs)

def _meta_book(*args, **kwargs):
    return _compat._meta_book(*args, **kwargs)

def _soup(*args, **kwargs):
    return _compat._soup(*args, **kwargs)

def _find_json_call(*args, **kwargs):
    return _compat._find_json_call(*args, **kwargs)

def _dedupe_results(*args, **kwargs):
    return _compat._dedupe_results(*args, **kwargs)

def _akniga_search_card(card) -> SearchResult | None:
    """Parse a normal Akniga search entry, excluding catalogue previews."""
    if card.select_one('.caption__article-preview'):
        return None
    anchor = card.select_one('div.article--cover > a[href]') or card.select_one('a[href]')
    if anchor is None:
        return None
    url = urljoin('https://akniga.org/', str(anchor.get('href') or ''))
    if not is_supported_url(url):
        return None
    author = _text(card, "span.link__action--author a[href*='author']")
    narrator = _text(card, "span.link__action--author a[href*='performer']")
    cover = anchor.select_one('img') or card.select_one('img')
    name = _clean(cover.get('alt') if cover else '') or _text(card, '.caption__article-main')
    if not name:
        name = _clean(anchor.get_text(' ', strip=True))
    # Album artwork often contains `Author – Title`. Drop only the confirmed
    # author prefix, never guess one from an arbitrary dash inside a title.
    if author:
        for separator in (' – ', ' — ', ' - '):
            prefix = author + separator
            if name.casefold().startswith(prefix.casefold()):
                name = name[len(prefix):].strip()
                break
    if not name:
        return None
    return SearchResult(title=name, url=url, source='akniga.org',
                        author=author, narrator=narrator)



def parse_akniga_collection(html_text: str) -> list[SearchResult]:
    """Extract book links only from a collection's main content.

    Return distinct playable book entries, never the collection URL itself.
    Use the same article cards as the normal Akniga catalogue. The fallback
    handles collections where the site presents a list of individual anchors.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    cards = soup.select(".content__main__articles--item")
    results = []
    for card in cards:
        item = _akniga_search_card(card)
        if item is not None:
            results.append(item)
    if not results:
        # Avoid harvesting unrelated navigation/sidebar/footer recommendations.
        main = (soup.select_one("main .content__main") or
                soup.select_one(".content__main__articles") or
                soup.select_one(".content__main") or soup.select_one("main"))
        if main is None:
            raise SiteStructureChanged("akniga.org: не найдена область книг в подборке.")
        for anchor in main.select("a[href]"):
            href = urljoin("https://akniga.org/", str(anchor.get("href") or ""))
            if not is_supported_url(href) or not href.startswith("https://akniga.org/"):
                continue
            image = anchor.select_one("img")
            title = _clean((image.get("alt") if image else "") or
                           anchor.get("title") or anchor.get_text(" ", strip=True))
            if not title:
                # A cover link without a label is not a usable search result.
                continue
            results.append(SearchResult(title=title, url=normalize_supported_url(href),
                                        source="akniga.org"))
    # A valid empty collection should not silently look like successful search.
    if not results:
        raise SiteStructureChanged("akniga.org: книги в подборке не найдены; возможно, изменилась разметка страницы.")
    return _dedupe_results(results)[:100]


def fetch_akniga_collection(url: str, *, cancel_event=None) -> list[SearchResult]:
    canonical = normalize_akniga_collection_url(url)
    if not canonical:
        raise ValueError("Ожидалась ссылка на подборку akniga.org/collection/...")
    _check_cancel(cancel_event)
    response = _request(canonical, cancel_event=cancel_event)
    _check_cancel(cancel_event)
    return _compat.parse_akniga_collection(response.text)


def search_akniga(query: str, *, cancel_event=None) -> list[SearchResult]:
    """Akniga book catalogue search; no player token or media is requested."""
    results = []
    for page in range(1, 4):
        _check_cancel(cancel_event)
        url = f'https://akniga.org/search/books/page{page}/?q=' + quote(query)
        soup = _soup(url, cancel_event)
        cards = soup.select('div.content__main__articles--item')
        if not cards:
            if page == 1 and not (soup.select_one('.content__main__articles') or
                                  re.search(r'ничего не найдено|нет результатов|по вашему запросу', soup.get_text(' ', strip=True), re.I)):
                raise SiteStructureChanged('akniga.org: не найдена область результатов поиска (возможно, изменился сайт).')
            break
        page_results = []
        for card in cards:
            result = _akniga_search_card(card)
            if result is not None:
                page_results.append(result)
        if not page_results:
            break
        results.extend(page_results)
        results = _dedupe_results(results)
        if len(results) >= _SEARCH_LIMIT:
            break
    return results[:_SEARCH_LIMIT]
