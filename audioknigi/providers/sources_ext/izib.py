"""izib catalogue extraction and public search.

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

def _izib_book_title(element) -> str:
    """Read a title without spaces introduced by highlighted inline fragments.

    Izib's search markup can split the query term from a Russian case ending,
    e.g. ``<b>Шерлок</b>а``.  BeautifulSoup's ``get_text(" ",
    strip=True)`` turns this into ``Шерлок а`` and also inserts a space
    before punctuation.  Read the original text nodes without adding a
    separator: whitespace explicitly present in the HTML is preserved.
    Do not attempt language-specific suffix guessing here.
    """
    if element is None:
        return ""
    # Preserve the original gaps around inline highlighting tags. A real
    # <br> is a word/line boundary; <wbr> is only a break opportunity and
    # must not introduce a space in the middle of a word.
    fragments = []
    for node in element.descendants:
        if isinstance(node, NavigableString):
            fragments.append(str(node))
        elif isinstance(node, Tag) and node.name == "br":
            fragments.append(" ")
    text = _clean("".join(fragments))
    # Fix visible artefacts like "Шерлок Холмс . Дыхание бога" without
    # changing genuine spaces between words or internal punctuation.
    return re.sub(r"\s+([.,!?;:…])", r"\1", text)


def fetch_izibuk(url: str, *, cancel_event=None) -> Book:
    page = _request(url, cancel_event=cancel_event).text
    soup = BeautifulSoup(page, "html.parser")
    player = _find_json_call(page, r"\bnew\s+XSPlayer\s*\(")
    if not isinstance(player, dict) or not isinstance(player.get("tracks"), list):
        raise SiteStructureChanged("izib.uk: настройки XSPlayer не найдены либо книга недоступна.")
    prefix = str(player.get("mp3_url_prefix") or "").strip()
    if not prefix:
        raise SiteStructureChanged("izib.uk: отсутствует адрес сервера аудиофайлов.")
    root = prefix if prefix.startswith(("https://", "http://")) else "https://" + prefix.lstrip("/")
    tracks = []
    for row in player["tracks"]:
        if not isinstance(row, (list, tuple)) or len(row) < 5 or not row[4]:
            continue
        media = str(row[4]).lstrip("/")
        tracks.append(_track(len(tracks) + 1, row[1], _public_media(media, root.rstrip("/") + "/"), url, row[2]))
    if not tracks:
        raise SiteStructureChanged("izib.uk: доступных аудиодорожек не найдено.")
    return _meta_book(url,
        title=(_izib_book_title(soup.select_one("span[itemprop='name']"))
               or _izib_book_title(soup.select_one("h1[itemprop='name']"))
               or _izib_book_title(soup.select_one("h1"))
               or _izib_book_title(soup.select_one("title"))),
        author=_izib_book_title(soup.select_one("a[href^='/author']")),
        narrator=_izib_book_title(soup.select_one("a[href^='/reader']")),
        description=_text(soup, "[itemprop='description']"),
        cover=_href(soup, "meta[property='og:image'], img[itemprop='image'], img", url),
        tracks=tracks)


def _izib_search_card(card, base_url: str) -> SearchResult | None:
    """Extract a real search card, not its cover or preview link.

    Izib renders the same /art link twice, once around the cover and once
    around the book title. Prefer the text-only anchor from the original
    AudioBookPlayer implementation and never infer a book from empty alt text.
    """
    anchors = card.select("a[href^='/art'], a[href^='/book/']")
    if not anchors:
        return None
    anchor = next((a for a in anchors if not a.select_one('img') and _izib_book_title(a)), None)
    anchor = anchor or next((a for a in anchors if _clean(a.get('title'))), None) or anchors[0]
    page_url = urljoin(base_url, str(anchor.get('href') or ''))
    if not is_supported_url(page_url):
        return None
    name = (_izib_book_title(anchor) if not anchor.select_one('img') else '')
    if not name:
        name = _clean(anchor.get('title')) or _clean((card.select_one('img') or {}).get('alt'))
        name = re.sub(r"\s+([.,!?;:…])", r"\1", name)
    if not name:
        return None
    return SearchResult(title=name, url=page_url, source='izib.uk',
                        author=_izib_book_title(card.select_one("a[href^='/author']")),
                        narrator=_izib_book_title(card.select_one("a[href^='/reader']")))


def search_izibuk(query: str, *, cancel_event=None) -> list[SearchResult]:
    """Browse the Izib search cards using the same layout as AudioBookPlayer.

    When the results block is missing, distinguish a redesigned/blocked page
    from a legitimate empty query instead of claiming zero search results.
    """
    results = []
    for page in range(1, 4):
        _check_cancel(cancel_event)
        search_url = 'https://izib.uk/search?q=' + quote(query) + f'&p={page}'
        soup = _soup(search_url, cancel_event)
        listing = soup.select_one('#books_list')
        if listing is None:
            if page > 1:
                break
            raise SiteStructureChanged('izib.uk: не найдена область результатов поиска (возможно, изменился сайт).')
        # Direct children are grid rows; book cards are their immediate children.
        cards = listing.select(':scope > div > div')
        if not cards:
            cards = listing.select(':scope > div')
        page_results = []
        for card in cards:
            # Preview/audio sample links may have a trailing <span> marker.
            if card.select_one("a[href^='/art'] + span"):
                continue
            result = _izib_search_card(card, 'https://izib.uk/')
            if result is not None:
                page_results.append(result)
        if not page_results:
            break
        results.extend(page_results)
        results = _dedupe_results(results)
        if len(results) >= _SEARCH_LIMIT:
            break
    return results[:_SEARCH_LIMIT]
