"""librivox catalogue extraction and public search.

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

def _librivox_id(url):
    pieces = [p for p in urlparse(url).path.split("/") if p]
    if len(pieces) != 2 or pieces[0] != "details":
        raise SiteStructureChanged("LibriVox: ожидается ссылка archive.org/details/идентификатор.")
    return pieces[1]


def _contains_librivox(metadata: dict) -> bool:
    collections = metadata.get("collection") or []
    if isinstance(collections, str):
        collections = [collections]
    return isinstance(collections, list) and any(str(c).casefold() == "librivoxaudio" for c in collections)


def fetch_librivox(url: str, *, cancel_event=None) -> Book:
    identifier = _librivox_id(url)
    payload = _request("https://archive.org/metadata/" + quote(identifier), cancel_event=cancel_event).json()
    if not isinstance(payload, dict) or not isinstance(payload.get("metadata"), dict):
        raise SiteStructureChanged("LibriVox: метаданные отсутствуют.")
    info = payload["metadata"]
    if not _contains_librivox(info):
        raise SiteStructureChanged("Archive.org: этот объект не входит в коллекцию LibriVox.")
    files = payload.get("files") or []
    candidates = [item for item in files if isinstance(item, dict) and item.get("name")
                  and item.get("format") in {"128Kbps MP3", "VBR MP3", "64Kbps MP3"}]
    # Prefer 128kbps and avoid downloading duplicate chapters at two bitrates.
    for fmt in ("128Kbps MP3", "VBR MP3", "64Kbps MP3"):
        selected = [x for x in candidates if x.get("format") == fmt]
        if selected:
            break
    else:
        selected = []
    tracks = []
    for item in selected:
        name = str(item.get("name") or "")
        remote_url = "https://archive.org/download/" + quote(identifier) + "/" + quote(name, safe="/")
        tracks.append(_track(len(tracks) + 1, item.get("title") or PurePosixPath(name).stem,
                             remote_url, url, item.get("length")))
    if not tracks:
        raise SiteStructureChanged("LibriVox: для этой записи не найдены MP3-главы.")
    cover = next((x.get("name") for x in files if isinstance(x, dict) and x.get("format") == "JPEG" and x.get("name")), "")
    author = info.get("creator") or ""
    description = _clean(BeautifulSoup(str(info.get("description") or ""), "html.parser").get_text(" ", strip=True))
    return _meta_book(url, title=info.get("title"), author=author, description=description,
                      cover=("https://archive.org/download/" + quote(identifier) + "/" + quote(cover, safe="/")) if cover else "",
                      tracks=tracks)



def _librivox_archive_identifier(row: dict) -> str:
    """Only accept archive.org item IDs, never arbitrary API-supplied URLs."""
    for key in ("url_iarchive", "url_zip_file"):
        value = str(row.get(key) or "").strip()
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or parsed.hostname not in ("archive.org", "www.archive.org"):
            continue
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in ("details", "download"):
            ident = parts[1]
            if re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,255}", ident) and ident not in {".", ".."}:
                return ident
    return ""


def _librivox_search_from_catalogue(query: str, *, cancel_event=None) -> list[SearchResult]:
    """Official LibriVox API fallback, for works missed by Archive search.

    The API searches titles or authors (not full text). Only entries with
    a validated Archive item URL can be analyzed by our current downloader.
    """
    output = []
    for field in ("title", "author"):
        _check_cancel(cancel_event)
        payload = _request("https://librivox.org/api/feed/audiobooks", params={
            field: query, "format": "json", "extended": 1, "limit": _SEARCH_LIMIT,
        }, cancel_event=cancel_event).json()
        if not isinstance(payload, dict):
            raise SiteStructureChanged("LibriVox: неверный формат ответа каталога.")
        rows = payload.get("books") or []
        if not isinstance(rows, list):
            raise SiteStructureChanged("LibriVox: неверный список аудиокниг.")
        for row in rows:
            if not isinstance(row, dict) or not row.get("title"):
                continue
            ident = _librivox_archive_identifier(row)
            if not ident:
                continue
            authors = row.get("authors") or []
            names = []
            if isinstance(authors, list):
                for person in authors:
                    if isinstance(person, dict):
                        name = _clean(" ".join(str(person.get(part) or "") for part in ("first_name", "last_name")))
                        if name:
                            names.append(name)
            output.append(SearchResult(
                title=_clean(row["title"]), url="https://archive.org/details/" + quote(ident),
                source="archive.org", author=", ".join(names)))
            if len(output) >= _SEARCH_LIMIT:
                return _dedupe_results(output)
        if output:
            break
    return _dedupe_results(output)


def search_librivox(query: str, *, cancel_event=None) -> list[SearchResult]:
    """Search archived LibriVox recordings, then the official catalogue.

    Searches such as 'Поттер' can legitimately return nothing: LibriVox
    only catalogues public-domain audiobooks and matches original titles.
    """
    _check_cancel(cancel_event)
    params = {"q": f'collection:librivoxaudio AND (title:({query}) OR creator:({query}))',
              "fl[]": ["creator", "identifier", "title"],
              "rows": _SEARCH_LIMIT, "page": 1, "output": "json"}
    archive_error = None
    output = []
    try:
        data = _request("https://archive.org/advancedsearch.php", params=params, cancel_event=cancel_event).json()
        rows = ((data.get("response") or {}).get("docs") or []) if isinstance(data, dict) else []
        for item in rows:
            if not isinstance(item, dict) or not item.get("identifier") or not item.get("title"):
                continue
            ident = str(item["identifier"])
            if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,255}", ident):
                continue
            output.append(SearchResult(
                title=_clean(item["title"]), url="https://archive.org/details/" + quote(ident),
                source="archive.org", author=_clean(item.get("creator"))))
    except (requests.RequestException, ValueError, SiteStructureChanged) as exc:
        archive_error = exc
    if output:
        return _dedupe_results(output)
    try:
        return _librivox_search_from_catalogue(query, cancel_event=cancel_event)
    except (requests.RequestException, ValueError, SiteStructureChanged):
        if archive_error is not None:
            raise archive_error
        # Archive returned a legitimate empty result, but the optional official
        # catalogue was unavailable. Do not turn that into a hard search failure.
        return []
