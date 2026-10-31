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
    return parse_akniga_collection(response.text)


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
    data = _yakniga_payload(payload, cancel_event).get("book")
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
    rows = _yakniga_payload(payload, cancel_event).get("search") or []
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


def _dedupe_results(results):
    seen = set()
    unique = []
    for row in results:
        if row.url not in seen:
            seen.add(row.url)
            unique.append(row)
    return unique


__all__ = ["fetch_izibuk", "search_izibuk", "fetch_yakniga", "search_yakniga",
           "fetch_uknig", "search_uknig", "fetch_librivox", "search_librivox"]
