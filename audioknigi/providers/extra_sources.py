"""Additional public audiobook sources adapted for AudioKnigi Downloader.

Based on the published AudioBookPlayer adapter interfaces; rewritten for our Book,
Track and SearchResult models. No external executable, session token extraction,
protection bypass, or provider-specific downloader process is required.

Network behavior cannot be guaranteed without live tests. Only publicly available,
authorized media should be saved; restricted/paid pages fail clearly.
"""
from __future__ import annotations

import html
import json
import re
import threading
import requests
from pathlib import PurePosixPath
from urllib.parse import quote, urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

from ..core import Cancelled, SiteStructureChanged, get_http_session, parse_time_seconds
from ..models import Book, Track, SearchResult
from ..sources import normalize_supported_url, is_supported_url, normalize_akniga_collection_url

_TIMEOUT = (6, 18)
# GraphQL is a read-only catalogue API. Two short attempts are preferable to
# one long blocked connection (and never retry mutations).
_YAKNIGA_QUERY_TIMEOUT = (3, 5)
_SEARCH_LIMIT = 30


def _check_cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")


def _request(url, *, cancel_event=None, json_payload=None, params=None):
    _check_cancel(cancel_event)
    session = get_http_session()
    # The optional HTML metadata fallback must not hold up an otherwise
    # successful GraphQL book analysis for the full general-purpose timeout.
    host = urlparse(url).hostname
    if url == "https://yakniga.org/graphql":
        timeout = _YAKNIGA_QUERY_TIMEOUT
    elif host in {"yakniga.org", "www.yakniga.org"}:
        timeout = (3, 7)
    else:
        timeout = _TIMEOUT
    if json_payload is not None:
        response = session.post(url, json=json_payload, timeout=timeout)
    else:
        response = session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    _check_cancel(cancel_event)
    return response


def _clean(value) -> str:
    if isinstance(value, (list, tuple)):
        value = " ".join(str(x) for x in value)
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def _text(soup, selector: str) -> str:
    element = soup.select_one(selector)
    return _clean(element.get_text(" ", strip=True)) if element else ""


def _href(soup, selector, base=""):
    element = soup.select_one(selector)
    if not element:
        return ""
    link = str(element.get("href") or element.get("src") or element.get("data-original") or element.get("content") or "").strip()
    return urljoin(base, link) if link else ""


def _public_media(candidate: str, base_url: str) -> str:
    """Never pass script/file/credential URLs to the download engine."""
    resolved = urljoin(base_url, str(candidate or "").strip())
    parsed = urlparse(resolved)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise SiteStructureChanged("Источник вернул недопустимый адрес аудиофайла.")
    return resolved


def _track(index, title, candidate, base, duration=None):
    length = parse_time_seconds(duration)
    return Track(index=index, title=_clean(title) or f"Глава {index}", file=_public_media(candidate, base),
                 start=None, end=None,
                 duration=length if length and length > 0 else None)


def _meta_book(url, *, title, author="", narrator="", description="", cover="", tracks=None, restricted=False):
    title = _clean(title)
    if not title:
        raise SiteStructureChanged("Не найдено название аудиокниги.")
    return Book(url=normalize_supported_url(url), title=title, author=_clean(author),
                narrator=_clean(narrator), description=_clean(description),
                cover_url=urljoin(url, cover) if cover else "", tracks=list(tracks or []),
                restricted=bool(restricted))


def _soup(url, cancel_event):
    return BeautifulSoup(_request(url, cancel_event=cancel_event).text, "html.parser")


def _find_json_call(text: str, start_regex: str):
    """Extract the JSON argument of a call; tolerate quoted ')' characters."""
    m = re.search(start_regex, text, re.I | re.S)
    if not m:
        return None
    decoder = json.JSONDecoder()
    try:
        payload, _ = decoder.raw_decode(text[m.end():].lstrip())
        return payload
    except ValueError:
        return None




def _dedupe_results(results):
    seen = set()
    unique = []
    for row in results:
        if row.url not in seen:
            seen.add(row.url)
            unique.append(row)
    return unique



from .sources_ext.izib import (
    _izib_book_title,
    fetch_izibuk,
    _izib_search_card,
    search_izibuk,
)

from .sources_ext.akniga_catalog import (
    _akniga_search_card,
    parse_akniga_collection,
    fetch_akniga_collection,
    search_akniga,
)

from .sources_ext.yakniga import (
    _YAKNIGA_FIELDS,
    _YAKNIGA_BOOK_QUERY,
    _YAKNIGA_SEARCH_QUERY,
    _yakniga_payload,
    _yakniga_identity,
    _yakniga_book,
    _yakniga_description_from_html,
    _yakniga_html_description_fallback,
    fetch_yakniga,
    search_yakniga,
)

from .sources_ext.uknig import (
    _uknig_description_from_html,
    fetch_uknig,
    search_uknig,
)

from .sources_ext.librivox import (
    _librivox_id,
    _contains_librivox,
    fetch_librivox,
    _librivox_archive_identifier,
    _librivox_search_from_catalogue,
    search_librivox,
)

__all__ = ['fetch_izibuk','search_izibuk','fetch_yakniga','search_yakniga','fetch_uknig','search_uknig','fetch_librivox','search_librivox']
