"""yakniga catalogue extraction and public search.

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

_YAKNIGA_FIELDS = """title authorName readers { name } seriesName seriesNum
 duration cover description authorAlias aliasName isBiblio"""
_YAKNIGA_BOOK_QUERY = """query getBook($bookAlias: String, $authorAliasName: String) {
 book(aliasName: $bookAlias, authorAliasName: $authorAliasName) {
 """ + _YAKNIGA_FIELDS + """ chapters { collection { name duration fileUrl } }
 } }"""
_YAKNIGA_SEARCH_QUERY = """query ($term: String!) {
 search(autocomplete: true, term: $term) { ... on Book { """ + _YAKNIGA_FIELDS + """ } } }"""


def _yakniga_payload(payload, cancel_event=None):
    """Read-only GraphQL request with one bounded transient-network retry.

    POST is normally not safe to retry. Here the known payloads are GraphQL
    *queries* only: never retry mutations, HTTP status errors or bad JSON.
    Do not log the request body or signed links from any raised exception.
    """
    query = str(payload.get("query", "") if isinstance(payload, dict) else "")
    is_read_only = bool(re.match(r"\s*(?:query\b|\{)", query, re.I)) and not re.search(
        r"\bmutation\b", query, re.I
    )
    for attempt in range(2 if is_read_only else 1):
        _check_cancel(cancel_event)
        try:
            response = _request("https://yakniga.org/graphql", json_payload=payload,
                                cancel_event=cancel_event)
            data = response.json()
            if not isinstance(data, dict) or data.get("errors"):
                raise SiteStructureChanged("yakniga.org: GraphQL вернул ошибку.")
            if not isinstance(data.get("data"), dict):
                raise SiteStructureChanged("yakniga.org: GraphQL вернул неверные данные.")
            return data["data"]
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout,
                requests.exceptions.ProxyError) as exc:
            if not is_read_only or attempt:
                raise
            # Cancellation-aware delay, no unbounded retries or sleep in UI.
            if cancel_event is not None:
                if cancel_event.wait(0.15):
                    raise Cancelled("Операция отменена пользователем") from exc
            else:
                threading.Event().wait(0.15)
    raise AssertionError("Unreachable: GraphQL retry loop exhausted")


def _yakniga_identity(url):
    parts = [segment for segment in urlparse(url).path.split("/") if segment]
    if len(parts) != 2:
        raise SiteStructureChanged("yakniga.org: ожидается адрес книги /автор/книга.")
    return parts[0], parts[1]


def _yakniga_book(item, url):
    author = item.get("authorName", "")
    readers = item.get("readers") or []
    reader = readers[0].get("name", "") if isinstance(readers, list) and readers and isinstance(readers[0], dict) else ""
    cover = item.get("cover") or ""
    description = _clean(BeautifulSoup(str(item.get("description") or ""), "html.parser").get_text(" ", strip=True))
    return _meta_book(url, title=item.get("title"), author=author,
                      narrator=reader, description=description, cover=cover,
                      restricted=bool(item.get("isBiblio")))


def _yakniga_description_from_html(html_text: str) -> str:
    """Read only the book's on-page synopsis, never nearby series/comments.

    Yakniga can return an empty GraphQL `description` even when the book page
    contains the synopsis in `<div class="page__description ...">`. Its
    `page__description-hide` class means *collapsed*, not missing. Do not use
    meta descriptions, which commonly contain generic advertising text.
    """
    soup = BeautifulSoup(html_text or "", "html.parser")
    for node in soup.select("div.page__description"):
        for irrelevant in node.select("script, style, noscript"):
            irrelevant.decompose()
        synopsis = _clean(node.get_text(" ", strip=True))
        if synopsis:
            return synopsis
    return ""


def _yakniga_html_description_fallback(url: str, cancel_event=None) -> str:
    """Optional metadata request; errors must not discard usable chapters."""
    _check_cancel(cancel_event)
    if urlparse(url).hostname not in {"yakniga.org", "www.yakniga.org"}:
        return ""
    try:
        response = _request(url, cancel_event=cancel_event)
    except Cancelled:
        raise
    except requests.RequestException:
        # GraphQL already provided the chapters and title: an optional page
        # timeout/403 is not a reason to reject the otherwise usable book.
        return ""
    _check_cancel(cancel_event)
    return _yakniga_description_from_html(response.text)


def fetch_yakniga(url: str, *, cancel_event=None) -> Book:
    author_alias, book_alias = _yakniga_identity(url)
    payload = {"operationName":"getBook", "variables":{"bookAlias":book_alias, "authorAliasName":author_alias},
               "query":_YAKNIGA_BOOK_QUERY}
    data = _compat._yakniga_payload(payload, cancel_event).get("book")
    if not isinstance(data, dict):
        raise SiteStructureChanged("yakniga.org: книга не найдена в GraphQL.")
    book = _yakniga_book(data, url)
    if book.restricted:
        raise RuntimeError("yakniga.org: эта книга доступна только по лицензии; скачивание недоступно.")
    # Some book records have an empty GraphQL description even though the
    # public book page has a complete synopsis. Fetch the *page metadata*
    # only in that case, and keep the GraphQL chapter list untouched.
    if not book.description:
        book.description = _yakniga_html_description_fallback(url, cancel_event)
    chapters = (data.get("chapters") or {}).get("collection") or []
    if not isinstance(chapters, list):
        raise SiteStructureChanged("yakniga.org: неверный список глав.")
    book.tracks = [
        _track(index, item.get("name"), item.get("fileUrl"), "https://yakniga.org/", item.get("duration"))
        for index, item in enumerate((item for item in chapters if isinstance(item, dict) and item.get("fileUrl")), 1)
    ]
    if not book.tracks:
        raise SiteStructureChanged("yakniga.org: доступных глав не найдено.")
    return book


def search_yakniga(query: str, *, cancel_event=None) -> list[SearchResult]:
    payload = {"operationName":None, "variables":{"term":query}, "query":_YAKNIGA_SEARCH_QUERY}
    rows = _compat._yakniga_payload(payload, cancel_event).get("search") or []
    output = []
    for item in rows:
        if not isinstance(item, dict) or not item.get("aliasName") or not item.get("authorAlias"):
            continue
        if item.get("isBiblio"):
            continue
        try:
            url = f"https://yakniga.org/{quote(item['authorAlias'])}/{quote(item['aliasName'])}"
            book = _yakniga_book(item, url)
        except (SiteStructureChanged, TypeError, ValueError):
            continue
        output.append(SearchResult(title=book.title, url=book.url, source="yakniga.org",
                                   author=book.author, narrator=book.narrator))
        if len(output) >= _SEARCH_LIMIT:
            break
    return _dedupe_results(output)
