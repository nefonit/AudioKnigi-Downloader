"""uknig catalogue extraction and public search.

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

def _uknig_description_from_html(page: str) -> str:
    """Read only the book description, excluding neighboring page sections.

    Unlike the outer page, `div.description` may contain <p> and <br> nodes.
    Do not mistake comments, series, sidebar or embedded script text for it.
    """
    soup = BeautifulSoup(page or "", "html.parser")
    for block in soup.select("div.description"):
        for unwanted in block.select("script, style, noscript, form, button"):
            unwanted.decompose()
        paragraphs = block.find_all("p", recursive=False)
        if paragraphs:
            description = _clean(" ".join(p.get_text(" ", strip=True) for p in paragraphs))
        else:
            description = _clean(block.get_text(" ", strip=True))
        if description:
            return description
    return ""


def fetch_uknig(url: str, *, cancel_event=None) -> Book:
    page = _request(url, cancel_event=cancel_event).text
    soup = BeautifulSoup(page, "html.parser")
    playlist_url = re.search(r'createPlayer\s*\(\s*["\']([^"\']+)["\']\s*\)', page, re.I)
    if playlist_url is None:
        raise RuntimeError("uknig.com: плейлист отсутствует или эта книга лицензионная.")
    source_url = urljoin(url, html.unescape(playlist_url.group(1)))
    if urlparse(source_url).hostname not in {"uknig.com", "www.uknig.com"}:
        raise SiteStructureChanged("uknig.com: плейлист расположен на неожиданном сервере.")
    playlist = _request(source_url, cancel_event=cancel_event).json()
    if not isinstance(playlist, list):
        raise SiteStructureChanged("uknig.com: неверный JSON плейлиста.")
    tracks = []
    for entry in playlist:
        if not isinstance(entry, dict) or not entry.get("file"):
            continue
        file_url = str(entry["file"]).split(" or ", 1)[0]
        tracks.append(_track(len(tracks) + 1, entry.get("title"), file_url, source_url))
    if not tracks:
        raise SiteStructureChanged("uknig.com: глав не найдено.")
    return _meta_book(url, title=_text(soup, "h1[itemprop='name'], h1"),
                      author=_text(soup, "a[href*='/authors']"),
                      narrator=_text(soup, "a[href*='/readers']"),
                      description=_uknig_description_from_html(page),
                      cover=_href(soup, "meta[property='og:image'], img[itemprop='image'], img", url),
                      tracks=tracks)


def search_uknig(query: str, *, cancel_event=None) -> list[SearchResult]:
    soup = _soup("https://uknig.com/?q=" + quote(query), cancel_event)
    results = []
    for el in soup.select(".book-item"):
        anchor = el.select_one("a[href*='/books/']")
        if not anchor:
            continue
        url = urljoin("https://uknig.com", anchor.get("href", ""))
        title = _clean(anchor.get_text(" ", strip=True)) or _clean((el.select_one("img") or {}).get("alt", ""))
        if title:
            results.append(SearchResult(title=title, url=url, source="uknig.com",
                                        author=_text(el,"a[href*='/authors']"),
                                        narrator=_text(el,"a[href*='/readers']")))
        if len(results) >= _SEARCH_LIMIT:
            break
    return _dedupe_results(results)
