from __future__ import annotations

import ast
import html as html_lib
import json
import re
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse

from .network_dns import launch_playwright_chromium
from .core import Cancelled, USER_AGENT, get_http_session, load_browser_context_profile, parse_time_seconds
from .models import Book, NarrationVariant, SearchResult, Track
from .logging_utils import app_logger
from .sources import POLEKNIG_HOST, normalize_supported_url

BASE_URL = f"https://{POLEKNIG_HOST}/"
SEARCH_URL = BASE_URL
_BOOK_PATH_RE = re.compile(r"^/books/(\d+)(?:(?:-|/)[^/?#]+)?(?:/read)?/?$", re.I)
_AUTHOR_PATH_RE = re.compile(r"^/authors/(\d+)(?:-[^/?#]+)?/?$", re.I)
_AUDIO_URL_RE = re.compile(
    r"(?:(?:https?:)?//|/)[^\"'\s<>]+?\.(?:mp3|m4a|aac|ogg|wav)(?:\?[^\"'\s<>]*)?",
    re.I,
)
_RESTRICTED_MARKERS = (
    "удалено правообладателем",
    "удалена правообладателем",
    "удалён правообладателем",
    "удален правообладателем",
)
SEARCH_RESULT_LIMIT = 100
SEARCH_PAGE_LIMIT = 10
SEARCH_PAGE_WORKERS = 4


def _iter_completed_cancellable(futures, cancel_event=None):
    pending = set(futures)
    while pending:
        if cancel_event is not None and cancel_event.is_set():
            for future in pending:
                future.cancel()
            raise Cancelled("Операция отменена пользователем")
        done, pending = wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)
        for future in done:
            yield future


def _shutdown_pool_now(pool, futures) -> None:
    for future in futures:
        if not future.done():
            future.cancel()
    pool.shutdown(wait=False, cancel_futures=True)


AUTHOR_SEARCH_PAGE_LIMIT = 10
AUTHOR_SEARCH_WORKERS = 4
VARIANT_AUTHOR_PAGE_LIMIT = 5
VARIANT_WORKERS = 4

_SEARCH_UI_LABELS = {
    "слушать",
    "слушать онлайн",
    "слушать аудиокнигу",
    "воспроизвести",
    "подробнее",
    "подробнее о книге",
    "скачать",
    "скачать аудиокнигу",
    "читать",
    "читать онлайн",
    "play",
    "listen",
    "listen online",
    "download",
    "read",
    "read more",
    "details",
}


def _clean_text(value) -> str:
    text = html_lib.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\u2060", "")
    return re.sub(r"\s+", " ", text).strip(" \t\r\n,;:–—-")


def _clean_title_text(value) -> str:
    """Normalize visible title text without stripping meaningful punctuation."""
    text = html_lib.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\u2060", "")
    return re.sub(r"\s+", " ", text).strip()


def _is_search_ui_label(value: str) -> bool:
    """Return True for short action labels that are not book titles."""
    text = _clean_text(value).casefold()
    # Trim common decorative button glyphs without using broad ``startswith``
    # rules that could hide legitimate titles such as "Слушать тишину".
    text = re.sub(r"^[▶►⏵▷\s]+", "", text)
    text = re.sub(r"[›»→…\.\s]+$", "", text).strip()
    return text in _SEARCH_UI_LABELS


def _search_title_score(value: str):
    """Prefer descriptive title labels over short catalogue badges."""
    text = _clean_text(value)
    folded = text.casefold()
    badge = bool(
        folded in {"новинка", "новое", "хит", "серия", "аудиокнига", "книга", "new", "bestseller"}
        or re.fullmatch(r"(?:глава|часть|том|chapter|part|volume)\s*\d+", folded)
    )
    letters = sum(ch.isalpha() for ch in text)
    return (1 if badge else 0, 1 if letters == 0 else 0, -min(len(text), 180))


def _canonical_book_url(base_url: str, href: str) -> str:
    raw = str(href or "").strip()
    normalized = normalize_supported_url(raw)
    absolute = urljoin(base_url or BASE_URL, normalized)
    try:
        parsed = urlparse(absolute)
    except Exception:
        return ""
    host = (parsed.hostname or "").lower()
    if host not in {POLEKNIG_HOST, "www." + POLEKNIG_HOST}:
        return ""
    match = _BOOK_PATH_RE.match(parsed.path or "")
    if not match:
        return ""
    return f"https://{POLEKNIG_HOST}/books/{match.group(1)}"




def _canonical_author_url(base_url: str, href: str) -> str:
    absolute = urljoin(base_url or BASE_URL, str(href or "").strip())
    try:
        parsed = urlparse(absolute)
    except Exception:
        return ""
    host = (parsed.hostname or "").lower()
    if host not in {POLEKNIG_HOST, "www." + POLEKNIG_HOST}:
        return ""
    match = _AUTHOR_PATH_RE.match(parsed.path or "")
    if not match:
        return ""
    return f"https://{POLEKNIG_HOST}/authors/{match.group(1)}"


def _book_page_author_links(html_text: str, page_url: str = "") -> list[tuple[str, str]]:
    """Return visible author names together with canonical PoleKnig author URLs."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    pattern = r'<a\b[^>]*href=["\']([^"\']*/authors/\d+/?[^"\']*)["\'][^>]*>(.*?)</a>'
    for match in re.finditer(pattern, html_text or "", re.I | re.S):
        url = _canonical_author_url(page_url or BASE_URL, html_lib.unescape(match.group(1)))
        name = _clean_text(match.group(2))
        if not url or not name or url in seen:
            continue
        seen.add(url)
        found.append((name, url))
    return found


def _book_page_author_url(html_text: str, page_url: str = "") -> str:
    links = _book_page_author_links(html_text, page_url)
    return links[0][1] if links else ""


def _logical_title_key(title: str) -> str:
    """Normalize harmless PoleKnig title prefixes used for the same work.

    PoleKnig may list one recording as ``Про Федота...`` and another as
    ``Сказ про Федота...`` or ``Пьеса: Сказ про Федота...``.  The author
    must still match separately; this helper only removes such leading
    presentation labels and normalizes punctuation/case.
    """
    value = _clean_text(title).casefold().replace("ё", "е")
    # Strip generic presentation prefixes only at the beginning.
    for _ in range(3):
        updated = re.sub(r"^(?:пьеса|аудиокнига)\s*[:–—-]?\s*", "", value, flags=re.I)
        updated = re.sub(r"^(?:сказ|сказка)\s+(?=про\b)", "", updated, flags=re.I)
        if updated == value:
            break
        value = updated
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _person_key(value: str) -> str:
    normalized = _clean_text(value).casefold().replace("ё", "е")
    tokens = re.findall(r"\w+", normalized, flags=re.UNICODE)
    return " ".join(sorted(tokens))


def _person_keys_compatible(left_key: str, right_key: str) -> bool:
    """Match full names with initials/surname-only variants without broad fuzziness."""
    left = str(left_key or "").strip()
    right = str(right_key or "").strip()
    if not left or not right:
        return not left and not right
    if left == right:
        return True

    left_sig = {token for token in left.split() if len(token) >= 3}
    right_sig = {token for token in right.split() if len(token) >= 3}
    if not left_sig or not right_sig:
        return False
    shared = left_sig & right_sig
    if not shared:
        return False
    smaller = min(len(left_sig), len(right_sig))
    if smaller == 1:
        return any(len(token) >= 4 for token in shared)
    return len(shared) / smaller >= 0.5


def _extract_tag_text(html_text: str, tag: str) -> str:
    match = re.search(fr"<{tag}\b[^>]*>(.*?)</{tag}>", html_text or "", re.I | re.S)
    return _clean_title_text(match.group(1) if match else "")


def _extract_meta_content(html_text: str, key: str) -> str:
    patterns = (
        fr'<meta[^>]+(?:property|name)=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']*)["\']',
        fr'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{re.escape(key)}["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, html_text or "", re.I | re.S)
        if match:
            # Meta content may be a URL. Normalize whitespace/HTML entities but
            # never strip URL-significant punctuation such as '-', ':', or ';'.
            value = html_lib.unescape(str(match.group(1) or ""))
            value = re.sub(r"<[^>]+>", " ", value)
            value = value.replace("\u200b", "").replace("\ufeff", "").replace("\u2060", "")
            return re.sub(r"\s+", " ", value).strip()
    return ""


def _extract_link_text_by_path(html_text: str, path_prefix: str) -> str:
    pattern = (
        fr'<a\b[^>]*href=["\'][^"\']*{re.escape(path_prefix)}[^"\']*["\'][^>]*>'
        r'(.*?)</a>'
    )
    match = re.search(pattern, html_text or "", re.I | re.S)
    return _clean_text(match.group(1) if match else "")


def _looks_like_poleknig_seo_description(value: str, *, title: str = "", author: str = "") -> bool:
    text = _clean_title_text(value)
    if not text:
        return True
    folded = text.casefold().replace("ё", "е")
    seo_markers = (
        "скачать аудиокнигу", "слушать аудиокнигу онлайн",
        "аудиокнига онлайн", "бесплатно скачать", "poleknig",
    )
    if any(marker in folded for marker in seo_markers):
        return True
    compact = re.sub(r"[^\w]+", " ", folded, flags=re.UNICODE).strip()
    title_key = re.sub(r"[^\w]+", " ", _clean_title_text(title).casefold().replace("ё", "е"), flags=re.UNICODE).strip()
    author_key = re.sub(r"[^\w]+", " ", _clean_text(author).casefold().replace("ё", "е"), flags=re.UNICODE).strip()
    # A meta-description that is almost entirely "author + title + listen/download"
    # is catalogue SEO, not the book annotation shown on the page.
    if title_key and title_key in compact and author_key and author_key in compact and len(text) < 260:
        return True
    return False


def _poleknig_description_from_html(html_text: str, *, title: str = "", author: str = "") -> str:
    """Extract the visible book annotation instead of the page SEO description.

    PoleKnig detail pages expose the real synopsis in visible content while the
    meta description can contain a search-engine phrase such as "скачать
    аудиокнигу ...". Prefer semantically named description/annotation blocks,
    then substantial paragraphs, then JSON-LD, and only finally a non-SEO meta
    description.
    """
    html = str(html_text or "")
    candidates: list[str] = []

    block_pattern = re.compile(
        r'<(?P<tag>div|section|article)\b(?P<attrs>[^>]*)>(?P<body>[\s\S]*?)</(?P=tag)>',
        re.I,
    )
    for match in block_pattern.finditer(html):
        attrs = match.group("attrs") or ""
        marker = " ".join(re.findall(r'(?:class|id)=["\']([^"\']+)["\']', attrs, re.I)).casefold()
        if any(token in marker for token in ("description", "annotation", "annot", "book-text", "book_text", "book__text", "book-description", "book_description")):
            text = _clean_title_text(match.group("body"))
            if text:
                candidates.append(text)

    for body in re.findall(r'<p\b[^>]*>([\s\S]*?)</p>', html, re.I):
        text = _clean_title_text(body)
        if len(text) >= 80:
            candidates.append(text)

    # Structured data is a useful secondary source on layouts where the visible
    # synopsis container has no stable CSS class.
    for script in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', html, re.I):
        try:
            payload = json.loads(html_lib.unescape(script).strip())
        except Exception:
            continue
        stack = payload if isinstance(payload, list) else [payload]
        for item in stack:
            if isinstance(item, dict):
                text = _clean_title_text(item.get("description", ""))
                if text:
                    candidates.append(text)

    def score(text: str):
        clean = _clean_title_text(text)
        bad = _looks_like_poleknig_seo_description(clean, title=title, author=author)
        footer = any(x in clean.casefold() for x in ("contact@poleknig", "правообладателям", "правила сайта"))
        sentence_marks = sum(clean.count(mark) for mark in (".", "!", "?", "…"))
        return (1 if bad or footer else 0, 1 if len(clean) < 80 else 0, -min(len(clean), 4000), -sentence_marks)

    usable = [_clean_title_text(item) for item in candidates if _clean_title_text(item)]
    if usable:
        best = min(usable, key=score)
        if not _looks_like_poleknig_seo_description(best, title=title, author=author):
            return best

    for key in ("og:description", "description"):
        meta = _extract_meta_content(html, key)
        if meta and not _looks_like_poleknig_seo_description(meta, title=title, author=author):
            return meta
    return ""


def _book_page_metadata(html_text: str, page_url: str = "") -> dict[str, str]:
    """Extract stable PoleKnig title/author/reader metadata from a detail page."""
    title = _extract_tag_text(html_text, "h1")
    if not title:
        page_title = _extract_tag_text(html_text, "title")
        title = re.split(r"\s*:\s*слушать\s+аудиокнигу", page_title, maxsplit=1, flags=re.I)[0].strip()
        # Current page titles are commonly ``«Book» Author: слушать ...``.
        # Extract the quoted book name before stripping punctuation; otherwise
        # removing only the leading quote leaves ``Book» Author`` as the title.
        quoted = re.match(r'^\s*«([^»]+)»', title)
        if quoted:
            title = _clean_text(quoted.group(1))
        else:
            title = re.sub(r'^[«"]|[»"]$', "", title).strip()

    author_links = _book_page_author_links(html_text, page_url)
    author = ", ".join(name for name, _url in author_links)
    narrator = (
        _extract_link_text_by_path(html_text, "/readers/")
        or _extract_link_text_by_path(html_text, "/reader/")
        or _extract_link_text_by_path(html_text, "/performers/")
    )
    if not narrator:
        # The rendered page uses "Читает <a>Reader</a>". Keep this fallback for
        # older templates where the reader link path differs.
        match = re.search(
            r"Читает\s*(?:</?[^>]+>\s*)*([^<\n\r]{2,160})",
            html_text or "",
            re.I,
        )
        if match:
            narrator = _clean_text(match.group(1))

    year = ""
    match = re.search(r"Год\s+выхода\s*:\s*(?:</?[^>]+>\s*)*((?:19|20)\d{2})", html_text or "", re.I)
    if match:
        year = match.group(1)

    genre = ""
    genre_values = []
    for match in re.finditer(r'<a\b[^>]*href=["\'][^"\']*/genres/[^"\']*["\'][^>]*>(.*?)</a>', html_text or "", re.I | re.S):
        value = _clean_text(match.group(1))
        if value and value not in genre_values:
            genre_values.append(value)
    if genre_values:
        genre = ", ".join(genre_values)

    description = _poleknig_description_from_html(html_text, title=title, author=author)
    cover_url = _extract_meta_content(html_text, "og:image")
    if cover_url:
        cover_url = urljoin(page_url or BASE_URL, cover_url)

    return {
        "title": title or "Аудиокнига",
        "author": author,
        "narrator": narrator,
        "genre": genre,
        "year": year,
        "description": description,
        "cover_url": cover_url,
    }


def _extract_balanced_call_argument(source: str, marker: str = "Playerjs") -> str:
    """Return the first argument passed to Playerjs/new Playerjs."""
    text = str(source or "")
    match = re.search(rf"(?:new\s+)?{re.escape(marker)}\s*\(", text, re.I)
    if not match:
        return ""
    open_pos = text.find("(", match.start())
    if open_pos < 0:
        return ""
    in_string = False
    quote = ""
    escaped = False
    brace = bracket = paren = 0
    start = None
    for idx in range(open_pos + 1, len(text)):
        ch = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'", "`"):
            in_string = True
            quote = ch
            if start is None:
                start = idx
            continue
        if start is None and not ch.isspace():
            start = idx
        if ch == "{":
            brace += 1
        elif ch == "}":
            brace = max(0, brace - 1)
        elif ch == "[":
            bracket += 1
        elif ch == "]":
            bracket = max(0, bracket - 1)
        elif ch == "(":
            paren += 1
        elif ch == ")":
            if brace == 0 and bracket == 0 and paren == 0:
                return text[start:idx].strip() if start is not None else ""
            paren = max(0, paren - 1)
        elif ch == "," and brace == 0 and bracket == 0 and paren == 0:
            return text[start:idx].strip() if start is not None else ""
    return ""


def _read_js_value(text: str, start: int) -> str:
    source = str(text or "")
    idx = int(start)
    while idx < len(source) and source[idx].isspace():
        idx += 1
    if idx >= len(source):
        return ""
    first = source[idx]
    if first in ('"', "'", "`"):
        quote = first
        escaped = False
        for pos in range(idx + 1, len(source)):
            ch = source[pos]
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                return source[idx:pos + 1]
        return source[idx:]
    if first in "[{":
        opening, closing = ("[", "]") if first == "[" else ("{", "}")
        depth = 0
        in_string = False
        quote = ""
        escaped = False
        for pos in range(idx, len(source)):
            ch = source[pos]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    in_string = False
                continue
            if ch in ('"', "'", "`"):
                in_string = True
                quote = ch
                continue
            if ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    return source[idx:pos + 1]
        return source[idx:]
    end = idx
    while end < len(source) and source[end] not in ",}\n\r":
        end += 1
    return source[idx:end].strip()


def _js_position_is_code(source: str, position: int) -> bool:
    """Tell whether *position* is outside JS strings/comments.

    PlayerJS configuration is JavaScript rather than strict JSON.  A regex for
    ``file:`` alone can accidentally match text inside a title/description,
    e.g. ``title: "Аудиокнига, file: часть 1"``.  This lightweight scanner is
    sufficient for object literals and deliberately ignores property-looking
    text inside quoted strings and comments.
    """
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    i = 0
    limit = max(0, min(int(position), len(source)))
    while i < limit:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < limit else ""
        if line_comment:
            if ch in "\r\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in ('"', "'", "`"):
            quote = ch
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        i += 1
    return quote is None and not line_comment and not block_comment


def _extract_js_property(object_text: str, name: str) -> str:
    source = str(object_text or "")
    pattern = re.compile(rf"(?:^|[,{{\s])(?:[\"']?{re.escape(name)}[\"']?)\s*:\s*", re.I)
    for match in pattern.finditer(source):
        if _js_position_is_code(source, match.start()):
            return _read_js_value(source, match.end())
    return ""


def _decode_js_string(value: str) -> str:
    raw = str(value or "").strip()
    if len(raw) >= 2 and raw[0] in ('"', "'") and raw[-1] == raw[0]:
        try:
            return str(ast.literal_eval(raw.replace(r"\/", "/")))
        except Exception:
            body = raw[1:-1]
            return body.replace("\\/", "/").replace("\\\"", '"').replace("\\'", "'")
    if len(raw) >= 2 and raw[0] == "`" and raw[-1] == "`":
        return raw[1:-1].replace("\\/", "/")
    return raw


def _iter_js_object_literals(source: str):
    """Yield balanced JS object literals outside strings and comments."""
    text = str(source or "")
    depth = 0
    start = None
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch in "\r\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in ('"', "'", "`"):
            quote = ch
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                yield text[start : i + 1]
                start = None
        i += 1


def _normalize_js_literals_for_python(candidate: str) -> str:
    """Translate JS true/false/null only outside quoted string literals."""
    text = str(candidate or "")
    out: list[str] = []
    i = 0
    quote = ""
    escaped = False
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            out.append(ch)
            i += 1
            continue
        matched = False
        for token, replacement in (("true", "True"), ("false", "False"), ("null", "None")):
            end = i + len(token)
            if text[i:end].casefold() != token:
                continue
            before = text[i - 1] if i > 0 else ""
            after = text[end] if end < len(text) else ""
            if (before and (before.isalnum() or before == "_")) or (after and (after.isalnum() or after == "_")):
                continue
            out.append(replacement)
            i = end
            matched = True
            break
        if matched:
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _parse_playlist_objects(value: str, page_url: str) -> list[Track]:
    raw = str(value or "").strip()
    if not raw:
        return []
    decoded = _decode_js_string(raw)
    # A quoted PlayerJS value may itself contain a JSON array.
    candidates = [raw, decoded]
    for candidate in candidates:
        value_obj = None
        try:
            value_obj = json.loads(candidate)
        except Exception:
            try:
                sanitized = _normalize_js_literals_for_python(candidate)
                value_obj = ast.literal_eval(sanitized)
            except Exception:
                value_obj = None
        if isinstance(value_obj, dict):
            value_obj = value_obj.get("playlist") or value_obj.get("file") or value_obj.get("files")
        if isinstance(value_obj, list):
            tracks = []
            for pos, item in enumerate(value_obj, 1):
                if isinstance(item, str):
                    file_url = urljoin(page_url, item.replace("\\/", "/"))
                    track_index = len(tracks) + 1
                    tracks.append(Track(index=track_index, title=f"{track_index:03d}", file=file_url))
                    continue
                if not isinstance(item, dict):
                    continue
                file_url = str(item.get("file") or item.get("url") or item.get("src") or "").replace("\\/", "/").strip()
                if not file_url:
                    continue
                track_index = len(tracks) + 1
                title = _clean_text(item.get("title") or item.get("name")) or f"{track_index:03d}"
                start = parse_time_seconds(item.get("start"))
                end = parse_time_seconds(item.get("end"))
                duration = parse_time_seconds(item.get("duration") or item.get("length") or item.get("time"))
                if duration is None and start is not None and end is not None and end > start:
                    duration = end - start
                tracks.append(
                    Track(
                        index=track_index,
                        title=title,
                        file=urljoin(page_url, file_url),
                        start=start,
                        end=end,
                        duration=duration,
                    )
                )
            if tracks:
                return tracks

    # JavaScript arrays sometimes use unquoted object keys, which neither JSON
    # nor ``ast.literal_eval`` accepts. Parse those PlayerJS objects conservatively.
    if raw.lstrip().startswith("[") and "file" in raw.casefold():
        object_tracks = []
        for pos, obj in enumerate(_iter_js_object_literals(raw), 1):
            file_value = _decode_js_string(_extract_js_property(obj, "file") or _extract_js_property(obj, "url")).strip()
            if not file_value:
                continue
            track_index = len(object_tracks) + 1
            title_value = _clean_text(_decode_js_string(_extract_js_property(obj, "title") or _extract_js_property(obj, "name"))) or f"{track_index:03d}"
            start = parse_time_seconds(_decode_js_string(_extract_js_property(obj, "start")))
            end = parse_time_seconds(_decode_js_string(_extract_js_property(obj, "end")))
            duration = parse_time_seconds(_decode_js_string(
                _extract_js_property(obj, "duration") or _extract_js_property(obj, "length") or _extract_js_property(obj, "time")
            ))
            if duration is None and start is not None and end is not None and end > start:
                duration = end - start
            object_tracks.append(Track(
                index=track_index, title=title_value, file=urljoin(page_url, file_value),
                start=start, end=end, duration=duration
            ))
        if object_tracks:
            return object_tracks

    # PlayerJS also accepts compact strings: [Part 1]url,[Part 2]url.
    compact = decoded.strip()
    parts = re.split(r"\s*,\s*(?=\[[^\]]+\])", compact)
    if len(parts) == 1 and "," in compact:
        raw_parts = [part.strip() for part in compact.split(",") if part.strip()]
        if raw_parts and all(re.search(r"\.(?:mp3|m4a|aac|ogg|wav)(?:\?|$)", part, re.I) for part in raw_parts):
            parts = raw_parts
    compact_tracks = []
    for pos, part in enumerate(parts, 1):
        match = re.match(r"\[([^\]]+)\](.+)$", part.strip(), re.S)
        start = None
        if match:
            label, file_url = _clean_text(match.group(1)), match.group(2).strip()
            parsed_marker = parse_time_seconds(label)
            if parsed_marker is not None and re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?", label):
                start = parsed_marker
                title = f"{pos:03d}"
            else:
                title = label
        elif re.search(r"\.(?:mp3|m4a|aac|ogg|wav)(?:\?|$)", part, re.I):
            title, file_url = f"{pos:03d}", part.strip()
        else:
            continue
        track_index = len(compact_tracks) + 1
        compact_tracks.append(Track(index=track_index, title=title or f"{track_index:03d}", file=urljoin(page_url, file_url), start=start))
    for current, following in zip(compact_tracks, compact_tracks[1:]):
        if current.start is not None and following.start is not None and following.start > current.start:
            current.end = following.start
            current.duration = following.start - current.start
    return compact_tracks


def _tracks_from_playerjs(html_text: str, page_url: str) -> list[Track]:
    normalized = str(html_text or "")
    argument = _extract_balanced_call_argument(normalized, "Playerjs")
    if argument:
        for key in ("playlist", "file", "files"):
            value = _extract_js_property(argument, key)
            tracks = _parse_playlist_objects(value, page_url)
            if tracks:
                return tracks

    # Resilient fallback for templates that build the config in a variable
    # before constructing PlayerJS.
    script_chunks = re.findall(r"<script\b[^>]*>(.*?)</script>", normalized, re.I | re.S) or [normalized]
    for script_text in script_chunks:
        for key in ("playlist", "file", "files"):
            pattern = rf"(?:^|[,{{\s])(?:[\"']?{re.escape(key)}[\"']?)\s*:\s*"
            for match in re.finditer(pattern, script_text, re.I):
                if not _js_position_is_code(script_text, match.start()):
                    continue
                tracks = _parse_playlist_objects(_read_js_value(script_text, match.end()), page_url)
                if tracks:
                    return tracks

    # Last-resort public direct audio references. This does not decode or bypass
    # protected/obfuscated sources; it only uses URLs already exposed in HTML.
    seen = []
    technical_tokens = {"beep", "click", "notification", "sample", "preview"}
    for match in _AUDIO_URL_RE.finditer(normalized.replace("\\/", "/")):
        value = match.group(0)
        absolute = urljoin(page_url, value)
        stem = urlparse(absolute).path.rsplit("/", 1)[-1].rsplit(".", 1)[0].casefold()
        tokens = {token for token in re.split(r"[^a-zа-яё0-9]+", stem) if token}
        if tokens & technical_tokens:
            continue
        if absolute not in seen:
            seen.append(absolute)
    return [Track(index=i, title=f"{i:03d}", file=url) for i, url in enumerate(seen, 1)]


def _external_playlist_url(html_text: str, page_url: str) -> str:
    normalized = str(html_text or "")
    argument = _extract_balanced_call_argument(normalized, "Playerjs")
    if argument:
        for key in ("playlist", "file"):
            value = _decode_js_string(_extract_js_property(argument, key)).strip()
            if re.search(r"\.(?:json|txt)(?:\?|$)", value, re.I):
                return urljoin(page_url, value)

    # Some templates build the PlayerJS config in a variable and pass only the
    # variable name to ``new Playerjs(...)``.  Search script object properties
    # conservatively before paying the cost of a browser fallback.
    script_chunks = re.findall(r"<script\b[^>]*>(.*?)</script>", normalized, re.I | re.S) or [normalized]
    for script_text in script_chunks:
        for key in ("playlist", "file"):
            pattern = rf"(?:^|[,{{\s])(?:[\"']?{re.escape(key)}[\"']?)\s*:\s*"
            for match in re.finditer(pattern, script_text, re.I):
                if not _js_position_is_code(script_text, match.start()):
                    continue
                value = _decode_js_string(_read_js_value(script_text, match.end())).strip()
                if re.search(r"\.(?:json|txt)(?:\?|$)", value, re.I):
                    return urljoin(page_url, value)
    return ""


def parse_book_html(html_text: str, page_url: str, playlist_text: str = "", playlist_url: str = "") -> Book:
    meta = _book_page_metadata(html_text, page_url)
    restricted = any(marker in (html_text or "").casefold() for marker in _RESTRICTED_MARKERS)
    if restricted:
        return Book(
            url=page_url,
            title=meta["title"],
            author=meta["author"],
            narrator=meta["narrator"],
            description=meta["description"],
            genre=meta["genre"],
            year=meta["year"],
            cover_url=meta["cover_url"],
            tracks=[],
            restricted=True,
        )

    tracks = []
    if playlist_text:
        tracks = _parse_playlist_objects(playlist_text, playlist_url or page_url)
    if not tracks:
        tracks = _tracks_from_playerjs(html_text, page_url)
    if not tracks:
        raise RuntimeError(
            "На странице poleknig.com не найден открытый плейлист PlayerJS. "
            "Если сайт изменил формат плеера, потребуется обновление программы."
        )

    return Book(
        url=page_url,
        title=meta["title"],
        author=meta["author"],
        narrator=meta["narrator"],
        description=meta["description"],
        genre=meta["genre"],
        year=meta["year"],
        cover_url=meta["cover_url"],
        playlist_url=playlist_url,
        tracks=tracks,
        narration_variants=[
            NarrationVariant(
                url=page_url,
                narrator=meta["narrator"],
                title=meta["title"],
                current=True,
                available=True,
            )
        ],
    )



def _fetch_book_playwright(url: str, cancel_event=None) -> Book | None:
    """Best-effort fallback for PlayerJS configs materialized by JavaScript.

    It only reads public DOM/resource URLs already exposed to the browser. It
    does not attempt to decode DRM, protected tokens or rights-restricted pages.
    """
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    captured: list[str] = []
    try:
        with sync_playwright() as pw:
            app_logger.info("NETWORK DNS | client=Playwright/Chromium | provider=Cloudflare | mode=DoH-secure | proxy=enabled")
            browser = launch_playwright_chromium(pw.chromium)
            try:
                persisted_headers, persisted_cookies = load_browser_context_profile()
                context_options = {"locale": "ru-RU"}
                context_options["user_agent"] = str(persisted_headers.pop("User-Agent", "") or USER_AGENT)
                if persisted_headers:
                    context_options["extra_http_headers"] = persisted_headers
                context = browser.new_context(**context_options)
                if persisted_cookies:
                    for cookie in persisted_cookies:
                        try:
                            context.add_cookies([cookie])
                        except Exception:
                            app_logger.debug("Failed to restore PoleKnig cookie into Playwright context", exc_info=True)
                page = context.new_page()

                def on_request(request):
                    if cancel_event is not None and cancel_event.is_set():
                        return
                    value = str(request.url or "")
                    if re.search(r"\.(?:mp3|m4a|aac|ogg|wav)(?:\?|$)", value, re.I):
                        if value not in captured:
                            captured.append(value)

                page.on("request", on_request)
                if cancel_event is not None and cancel_event.is_set():
                    raise Cancelled("Операция отменена пользователем")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                if cancel_event is not None and cancel_event.is_set():
                    raise Cancelled("Операция отменена пользователем")
                for _ in range(18):
                    if cancel_event is not None and cancel_event.is_set():
                        raise Cancelled("Операция отменена пользователем")
                    page.wait_for_timeout(100)
                html_text = page.content()
                final_url = _canonical_book_url(url, page.url) or url

                book = None
                try:
                    book = parse_book_html(html_text, final_url)
                except RuntimeError:
                    book = None
                if book is not None:
                    try:
                        rendered_meta = _book_page_metadata(html_text, final_url)
                        rendered_variants = _discover_narration_variants(
                            html_text, final_url, rendered_meta, cancel_event=cancel_event
                        )
                        if rendered_variants:
                            book.narration_variants = rendered_variants
                    except Cancelled:
                        raise
                    except Exception:
                        app_logger.debug("Rendered PoleKnig narration discovery failed", exc_info=True)
                    return book

                exposed = page.evaluate(
                    """() => {
                        const values = [];
                        const add = (v) => { if (typeof v === 'string' && v) values.push(v); };
                        const safeJson = (value) => {
                            try {
                                const seen = new WeakSet();
                                return JSON.stringify(value, (_key, item) => {
                                    if (item && typeof item === 'object') {
                                        if (seen.has(item)) return '[Circular]';
                                        seen.add(item);
                                    }
                                    return item;
                                });
                            } catch (_) {
                                return '';
                            }
                        };
                        document.querySelectorAll('audio, audio source').forEach(el => {
                            add(el.currentSrc); add(el.src); add(el.getAttribute && el.getAttribute('src'));
                        });
                        try {
                            performance.getEntriesByType('resource').forEach(e => add(e.name));
                        } catch (_) {}
                        for (const key of Object.keys(window)) {
                            if (!/player/i.test(key)) continue;
                            let obj; try { obj = window[key]; } catch (_) { continue; }
                            if (!obj || typeof obj.api !== 'function') continue;
                            for (const cmd of ['file', 'playlist']) {
                                try {
                                    const v = obj.api(cmd);
                                    if (typeof v === 'string') add(v);
                                    else if (v != null) {
                                        const encoded = safeJson(v);
                                        if (encoded) values.push(encoded);
                                    }
                                } catch (_) {}
                            }
                        }
                        return values;
                    }"""
                )
                tracks: list[Track] = []
                for value in exposed or []:
                    parsed = _parse_playlist_objects(str(value), final_url)
                    if parsed:
                        tracks = parsed
                        break
                if not tracks:
                    seen = []
                    for value in [*captured, *(exposed or [])]:
                        raw = str(value or "")
                        if re.search(r"\.(?:mp3|m4a|aac|ogg|wav)(?:\?|$)", raw, re.I):
                            absolute = urljoin(final_url, raw)
                            if absolute not in seen:
                                seen.append(absolute)
                    tracks = [Track(index=i, title=f"{i:03d}", file=v) for i, v in enumerate(seen, 1)]
                if not tracks:
                    return None
                meta = _book_page_metadata(html_text, final_url)
                book = Book(
                    url=final_url, title=meta["title"], author=meta["author"],
                    narrator=meta["narrator"], description=meta["description"],
                    genre=meta["genre"], year=meta["year"], cover_url=meta["cover_url"],
                    tracks=tracks, narration_variants=[NarrationVariant(
                        url=final_url, narrator=meta["narrator"], title=meta["title"], current=True, available=True
                    )],
                )
                try:
                    rendered_variants = _discover_narration_variants(
                        html_text, final_url, meta, cancel_event=cancel_event
                    )
                    if rendered_variants:
                        book.narration_variants = rendered_variants
                except Cancelled:
                    raise
                except Exception:
                    app_logger.debug("Rendered PoleKnig narration discovery failed", exc_info=True)
                return book
            finally:
                try:
                    browser.close()
                except Exception:
                    pass
    except Cancelled:
        raise
    except Exception:
        return None

def fetch_book(url: str, cancel_event=None) -> Book:
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    canonical = _canonical_book_url(BASE_URL, url)
    if not canonical:
        raise RuntimeError("Для poleknig.com нужна ссылка на страницу книги вида https://poleknig.com/books/12345")
    session = get_http_session()
    response = session.get(
        canonical,
        headers={"Referer": BASE_URL},
        timeout=(7, 15),
        allow_redirects=True,
    )
    response.raise_for_status()
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    final_url = _canonical_book_url(canonical, response.url or canonical) or canonical
    html_text = response.text or ""

    playlist_url = _external_playlist_url(html_text, final_url)
    playlist_text = ""
    if playlist_url:
        try:
            playlist_response = session.get(
                playlist_url,
                headers={"Referer": final_url},
                timeout=(10, 35),
                allow_redirects=True,
            )
            playlist_response.raise_for_status()
            playlist_text = bytes(getattr(playlist_response, "content", b"") or b"").decode("utf-8", errors="replace") or str(getattr(playlist_response, "text", "") or "")
            playlist_url = playlist_response.url or playlist_url
        except Exception:
            playlist_text = ""
    browser_fallback_used = False
    try:
        book = parse_book_html(html_text, final_url, playlist_text, playlist_url)
    except RuntimeError as exc:
        # PlayerJS can be rendered dynamically. If plain HTTP does not expose a
        # public playlist, inspect the browser-visible player/resources.
        browser_book = _fetch_book_playwright(final_url, cancel_event=cancel_event)
        if browser_book is None:
            raise exc
        book = browser_book
        browser_fallback_used = True

    # A manually pasted PoleKnig URL may have alternative recordings even
    # though the detail page itself does not link them.  Discover those pages
    # through the author's public catalogue so the existing narration selector
    # works the same way as it does for search-originated books.
    try:
        if not browser_fallback_used:
            meta = _book_page_metadata(html_text, final_url)
            variants = _discover_narration_variants(
                html_text, final_url, meta, session=session, cancel_event=cancel_event
            )
            if variants:
                book.narration_variants = variants
    except Cancelled:
        raise
    except Exception:
        if not getattr(book, "narration_variants", None):
            book.narration_variants = [NarrationVariant(
                url=final_url, narrator=getattr(book, "narrator", ""),
                title=getattr(book, "title", ""), current=True
            )]
    return book


class _BookLinkParser(HTMLParser):
    def __init__(self, base_url: str = BASE_URL):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[tuple[str, list[str]]] = []
        self._stack: list[dict | None] = []

    def handle_starttag(self, tag, attrs):
        name = str(tag or "").lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if name == "a":
            href = attrs_dict.get("href", "").strip()
            canonical = _canonical_book_url(self.base_url, href)
            if canonical:
                self._stack.append({
                    "url": canonical,
                    "labels": [attrs_dict.get("title", ""), attrs_dict.get("aria-label", "")],
                    "text": [],
                })
            else:
                self._stack.append(None)
            return
        if name == "img" and self._stack and self._stack[-1] is not None:
            for key in ("alt", "title"):
                value = attrs_dict.get(key, "")
                if value:
                    self._stack[-1]["labels"].append(value)

    def handle_data(self, data):
        if self._stack and self._stack[-1] is not None and data:
            self._stack[-1]["text"].append(data)

    def handle_endtag(self, tag):
        if str(tag or "").lower() != "a" or not self._stack:
            return
        current = self._stack.pop()
        if current is None:
            return
        labels = [_clean_text(" ".join(current["text"])), *[_clean_text(v) for v in current["labels"]]]
        labels = [v for v in labels if v]
        if labels:
            self.links.append((current["url"], labels))


def parse_search_results(html_text: str, base_url: str = BASE_URL) -> list[SearchResult]:
    parser = _BookLinkParser(base_url)
    try:
        parser.feed(html_text or "")
        parser.close()
    except Exception:
        pass
    by_url: dict[str, str] = {}
    for url, labels in parser.links:
        candidates = []
        for label in labels:
            value = _clean_text(label)
            if 1 < len(value) <= 240 and not _is_search_ui_label(value):
                candidates.append(value)
        if not candidates:
            continue
        title = min(candidates, key=_search_title_score)
        current = by_url.get(url)
        if current is None or _search_title_score(title) < _search_title_score(current):
            by_url[url] = title
    return [SearchResult(title=title, url=url, source="poleknig.com") for url, title in by_url.items()][:SEARCH_RESULT_LIMIT]


def _search_last_page(html_text: str, query: str = "") -> int:
    pages = [1]
    for href in re.findall(r'href=["\']([^"\']+)["\']', html_text or "", re.I):
        try:
            parsed = urlparse(html_lib.unescape(href))
            params = parse_qs(parsed.query)
            if "p" not in params:
                continue
            if query and "q" in params:
                q_value = " ".join(params.get("q") or [])
                if q_value and q_value.strip().casefold() != query.strip().casefold():
                    continue
            pages.append(max(1, int((params.get("p") or [1])[0])))
        except Exception:
            pass
    return max(pages)


def _fetch_search_page(query: str, page: int = 1):
    session = get_http_session()
    params = {"q": str(query or "").strip()}
    if int(page) > 1:
        params["p"] = int(page)
    response = session.get(
        SEARCH_URL,
        params=params,
        headers={"Referer": BASE_URL},
        timeout=(6, 15),
        allow_redirects=True,
    )
    response.raise_for_status()
    return response


def _logical_title_compatible(left: str, right: str) -> bool:
    """Return True for the same normalized title with a harmless suffix/prefix."""
    left_key = _logical_title_key(left)
    right_key = _logical_title_key(right)
    if not left_key or not right_key:
        return False
    if left_key == right_key:
        return True
    shorter, longer = sorted((left_key, right_key), key=len)
    return len(shorter) >= 6 and (longer.startswith(shorter + " ") or longer.endswith(" " + shorter))


def _query_matches_metadata(query: str, title: str, author: str, narrator: str = "") -> bool:
    tokens = [part for part in re.findall(r"\w+", str(query or "").casefold(), re.UNICODE) if part]
    if not tokens:
        return True
    haystack = f"{title} {author} {narrator}".casefold().replace("ё", "е")
    return all(token.replace("ё", "е") in haystack for token in tokens)


def _candidate_detail_variant(result: SearchResult, expected_title_key: str, expected_author_key: str) -> NarrationVariant | None:
    # Each executor worker receives its own thread-local requests.Session.
    session = get_http_session()
    try:
        response = session.get(
            result.url,
            headers={"Referer": BASE_URL},
            timeout=(6, 20),
            allow_redirects=True,
        )
        response.raise_for_status()
        html_text = response.text or ""
        if any(marker in html_text.casefold() for marker in _RESTRICTED_MARKERS):
            return None
        final_url = _canonical_book_url(result.url, response.url or result.url) or result.url
        meta = _book_page_metadata(html_text, final_url)
        meta_title = str(meta.get("title", "") or "")
        meta_author = str(meta.get("author", "") or "")
        if not _logical_title_compatible(meta_title, expected_title_key):
            return None
        if expected_author_key and not _person_keys_compatible(_person_key(meta_author), expected_author_key):
            return None
        return NarrationVariant(
            url=final_url,
            narrator=str(meta.get("narrator", "") or ""),
            title=meta_title,
            current=False,
            available=True,
        )
    except Exception:
        return None


def _discover_narration_variants(html_text: str, page_url: str, meta: dict[str, str], session=None, cancel_event=None) -> list[NarrationVariant]:
    """Find accessible alternative PoleKnig recordings for a detail page.

    Alternative recordings are separate ``/books/<id>`` pages and are not
    linked from the PlayerJS block itself.  The author's catalogue is a
    stable public index for discovering them.  Rights-restricted alternatives
    are intentionally excluded; the currently requested page stays visible
    even when it is restricted so the user understands what was analysed.
    """
    current_url = _canonical_book_url(BASE_URL, page_url) or page_url
    current = NarrationVariant(
        url=current_url,
        narrator=meta.get("narrator", ""),
        title=meta.get("title", ""),
        current=True,
        available=not any(marker in (html_text or "").casefold() for marker in _RESTRICTED_MARKERS),
    )
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    title_key = _logical_title_key(meta.get("title", ""))
    author_key = _person_key(meta.get("author", ""))
    author_url = _book_page_author_url(html_text, page_url)
    if not title_key or not author_url:
        return [current]

    session = session or get_http_session()
    pages: dict[int, str] = {}
    try:
        first = session.get(
            author_url,
            headers={"Referer": current_url},
            timeout=(6, 20),
            allow_redirects=True,
        )
        first.raise_for_status()
        pages[1] = first.text or ""
        last_page = min(_search_last_page(first.text or ""), VARIANT_AUTHOR_PAGE_LIMIT)
    except Exception:
        return [current]

    if last_page > 1:
        workers = min(SEARCH_PAGE_WORKERS, last_page - 1)
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="poleknig-variants-pages")
        futures = {}
        try:
            def fetch_author_page(page_number: int) -> str:
                worker_session = get_http_session()
                response = worker_session.get(
                    author_url, params={"p": page_number}, headers={"Referer": author_url},
                    timeout=(5, 12), allow_redirects=True
                )
                response.raise_for_status()
                return response.text or ""

            for page in range(2, last_page + 1):
                futures[pool.submit(fetch_author_page, page)] = page
            for future in _iter_completed_cancellable(futures, cancel_event):
                page = futures[future]
                try:
                    pages[page] = future.result()
                except Exception:
                    pages[page] = ""
        finally:
            _shutdown_pool_now(pool, futures)

    candidates: list[SearchResult] = []
    seen_urls = {current_url}
    for page in sorted(pages):
        base = author_url if page == 1 else f"{author_url}?p={page}"
        for item in parse_search_results(pages[page], base):
            if item.url in seen_urls:
                continue
            if not _logical_title_compatible(item.title, title_key):
                continue
            seen_urls.add(item.url)
            candidates.append(item)

    if not candidates:
        return [current]

    found: list[NarrationVariant | None] = [None] * len(candidates)
    workers = min(VARIANT_WORKERS, len(candidates))
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="poleknig-variants-meta")
    futures = {}
    try:
        futures = {
            pool.submit(_candidate_detail_variant, item, title_key, author_key): idx
            for idx, item in enumerate(candidates)
        }
        for future in _iter_completed_cancellable(futures, cancel_event):
            idx = futures[future]
            try:
                found[idx] = future.result()
            except Exception:
                found[idx] = None
    finally:
        _shutdown_pool_now(pool, futures)

    variants = [current]
    variant_urls = {current_url}
    for item in found:
        if item is None:
            continue
        canonical = _canonical_book_url(BASE_URL, item.url) or item.url
        if canonical in variant_urls:
            continue
        variant_urls.add(canonical)
        item.url = canonical
        variants.append(item)
    return variants


def _hydrate_search_result_info(result: SearchResult) -> tuple[SearchResult, list[tuple[str, str]]]:
    """Hydrate a search row and retain author catalogue links from its detail page."""
    try:
        session = get_http_session()
        response = session.get(
            result.url,
            headers={"Referer": BASE_URL},
            timeout=(6, 20),
            allow_redirects=True,
        )
        response.raise_for_status()
        page_url = response.url or result.url
        html_text = response.text or ""
        meta = _book_page_metadata(html_text, page_url)
        hydrated = SearchResult(
            title=meta["title"] or result.title,
            author=meta["author"],
            narrator=meta["narrator"],
            url=result.url,
            source="poleknig.com",
            availability=("restricted" if any(marker in html_text.casefold() for marker in _RESTRICTED_MARKERS) else "available"),
        )
        return hydrated, _book_page_author_links(html_text, page_url)
    except Exception:
        return result, []


def _hydrate_search_result(result: SearchResult) -> SearchResult:
    return _hydrate_search_result_info(result)[0]


def _author_name_matches_query(query: str, name: str) -> bool:
    return _query_matches_metadata(query, "", name)


def _fetch_author_catalog(author_url: str, cancel_event=None) -> list[SearchResult]:
    """Fetch all visible pages of one author's catalogue up to the app result ceiling."""
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    session = get_http_session()
    first = session.get(
        author_url,
        headers={"Referer": BASE_URL},
        timeout=(6, 15),
        allow_redirects=True,
    )
    first.raise_for_status()
    pages: dict[int, list[SearchResult]] = {
        1: parse_search_results(first.text or "", first.url or author_url),
    }
    last_page = min(_search_last_page(first.text or ""), AUTHOR_SEARCH_PAGE_LIMIT)
    if last_page > 1:
        workers = min(AUTHOR_SEARCH_WORKERS, last_page - 1)
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="poleknig-author-pages")
        futures = {}

        def _fetch_author_page(page: int):
            # get_http_session() is thread-local.  Never share the caller's
            # requests.Session/cookie jar across ThreadPoolExecutor workers.
            worker_session = get_http_session()
            return worker_session.get(
                author_url, params={"p": page}, headers={"Referer": author_url},
                timeout=(6, 15), allow_redirects=True,
            )

        try:
            futures = {
                pool.submit(_fetch_author_page, page): page
                for page in range(2, last_page + 1)
            }
            for future in _iter_completed_cancellable(futures, cancel_event):
                page = futures[future]
                try:
                    response = future.result()
                    response.raise_for_status()
                    pages[page] = parse_search_results(
                        response.text or "", response.url or f"{author_url}?p={page}"
                    )
                except Exception:
                    pages[page] = []
        finally:
            _shutdown_pool_now(pool, futures)

    results: list[SearchResult] = []
    seen: set[str] = set()
    for page in sorted(pages):
        for item in pages[page]:
            if item.url in seen:
                continue
            seen.add(item.url)
            results.append(item)
            if len(results) >= SEARCH_RESULT_LIMIT:
                return results
    return results


def _expand_matching_author_catalogs(
    query: str,
    hydrated: list[SearchResult],
    author_links: list[list[tuple[str, str]]],
    seed_links: list[tuple[str, str]] | None = None,
    cancel_event=None,
) -> list[SearchResult]:
    """Supplement generic search with complete paginated catalogues of matching authors.

    PoleKnig's generic ``?q=`` search is not a complete author catalogue.  Once a
    detail page proves that the query matches an author name, crawl that author's
    own ``/authors/<id>?p=`` pages so books from later author pages are not lost.
    """
    targets: dict[str, str] = {}
    for name, url in seed_links or []:
        if _author_name_matches_query(query, name):
            targets.setdefault(url, name)
    for item, links in zip(hydrated, author_links):
        if not _author_name_matches_query(query, item.author):
            continue
        for name, url in links:
            if _author_name_matches_query(query, name):
                targets.setdefault(url, name)
    if not targets:
        return []

    catalog_rows: list[SearchResult] = []
    workers = min(AUTHOR_SEARCH_WORKERS, len(targets))
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="poleknig-authors")
    futures = {}
    try:
        futures = {pool.submit(_fetch_author_catalog, url, cancel_event): url for url in targets}
        for future in _iter_completed_cancellable(futures, cancel_event):
            try:
                catalog_rows.extend(future.result())
            except Cancelled:
                raise
            except Exception:
                pass
    finally:
        _shutdown_pool_now(pool, futures)
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")

    # Detail-hydrate catalogue rows because catalogue cards can omit a reader and
    # because final filtering must be based on the real author metadata.
    unique: list[SearchResult] = []
    seen: set[str] = set()
    for item in catalog_rows:
        if item.url in seen:
            continue
        seen.add(item.url)
        unique.append(item)
        if len(unique) >= SEARCH_RESULT_LIMIT:
            break

    known_by_url = {item.url: item for item in hydrated if item.author}
    expanded: list[SearchResult] = [known_by_url.get(item.url, item) for item in unique]
    pending = [idx for idx, item in enumerate(unique) if item.url not in known_by_url]
    if pending:
        workers = min(8, len(pending))
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="poleknig-author-meta")
        futures = {}
        try:
            futures = {pool.submit(_hydrate_search_result, unique[idx]): idx for idx in pending}
            for future in _iter_completed_cancellable(futures, cancel_event):
                idx = futures[future]
                try:
                    expanded[idx] = future.result()
                except Exception:
                    expanded[idx] = unique[idx]
        finally:
            _shutdown_pool_now(pool, futures)

    return [item for item in expanded if _author_name_matches_query(query, item.author)]


def search(query: str, cancel_event=None) -> list[SearchResult]:
    query_text = str(query or "").strip()
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    first = _fetch_search_page(query_text, 1)
    search_page_html: dict[int, tuple[str, str]] = {1: (first.text or "", first.url or BASE_URL)}
    pages: dict[int, list[SearchResult]] = {
        1: parse_search_results(first.text or "", first.url or BASE_URL),
    }
    target_last = min(_search_last_page(first.text or "", query_text), SEARCH_PAGE_LIMIT)
    if target_last > 1:
        workers = min(SEARCH_PAGE_WORKERS, target_last - 1)
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="poleknig-search")
        futures = {}
        try:
            futures = {pool.submit(_fetch_search_page, query_text, p): p for p in range(2, target_last + 1)}
            for future in _iter_completed_cancellable(futures, cancel_event):
                page = futures[future]
                try:
                    response = future.result()
                    search_page_html[page] = (response.text or "", response.url or BASE_URL)
                    pages[page] = parse_search_results(response.text or "", response.url or BASE_URL)
                except Exception:
                    search_page_html[page] = ("", BASE_URL)
                    pages[page] = []
        finally:
            _shutdown_pool_now(pool, futures)

    combined = []
    seen = set()
    for page in sorted(pages):
        for item in pages[page]:
            if item.url in seen:
                continue
            seen.add(item.url)
            combined.append(item)
            if len(combined) >= SEARCH_RESULT_LIMIT:
                break
        if len(combined) >= SEARCH_RESULT_LIMIT:
            break

    hydrated = list(combined)
    hydrated_author_links: list[list[tuple[str, str]]] = [[] for _ in combined]
    if combined:
        workers = min(8, len(combined))
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="poleknig-meta")
        futures = {}
        try:
            futures = {pool.submit(_hydrate_search_result_info, item): idx for idx, item in enumerate(combined)}
            for future in _iter_completed_cancellable(futures, cancel_event):
                idx = futures[future]
                try:
                    hydrated[idx], hydrated_author_links[idx] = future.result()
                except Exception:
                    hydrated[idx] = combined[idx]
                    hydrated_author_links[idx] = []
        finally:
            _shutdown_pool_now(pool, futures)

    # PoleKnig already ranked these rows for the user's query.  Do not
    # second-guess that ranking with an ``all(tokens)`` metadata filter: words
    # such as "аудиокнига" or publisher/series terms can be present in the
    # site's index without appearing in title/author/narrator metadata.
    filtered = list(hydrated)

    # Generic PoleKnig search is not guaranteed to enumerate every book by an
    # author.  When the query actually matches an author, supplement it from the
    # author's own paginated catalogue.  Put catalogue rows first so a broad
    # surname query cannot crowd out the author's books with unrelated title hits.
    seed_author_links: list[tuple[str, str]] = []
    seen_seed_authors: set[str] = set()
    for page in sorted(search_page_html):
        html_text, page_url = search_page_html[page]
        for name, url in _book_page_author_links(html_text, page_url):
            if url in seen_seed_authors or not _author_name_matches_query(query_text, name):
                continue
            seen_seed_authors.add(url)
            seed_author_links.append((name, url))

    author_expanded = _expand_matching_author_catalogs(
        query_text, hydrated, hydrated_author_links, seed_author_links, cancel_event=cancel_event
    )
    merged_filtered: list[SearchResult] = []
    seen_filtered: set[str] = set()
    for item in [*author_expanded, *filtered]:
        if item.url in seen_filtered:
            continue
        seen_filtered.add(item.url)
        merged_filtered.append(item)
    filtered = merged_filtered

    groups: dict[tuple[str, str], list[SearchResult]] = {}
    order = []
    for item in filtered:
        title_key = _logical_title_key(item.title)
        author_key = _person_key(item.author)
        key = (title_key, author_key) if (title_key and author_key) else (item.url, "")
        if key not in groups:
            groups[key] = []
            order.append(key)
        if all(existing.url != item.url for existing in groups[key]):
            groups[key].append(item)

    results = []
    for key in order:
        members = groups[key]
        representative = members[0]
        variants = []
        narrators = []
        for idx, item in enumerate(members):
            if item.narrator and item.narrator not in narrators:
                narrators.append(item.narrator)
            variants.append(
                NarrationVariant(
                    url=item.url,
                    narrator=item.narrator,
                    title=representative.title,
                    current=(idx == 0),
                    available=(False if getattr(item, "availability", "") == "restricted" else True if getattr(item, "availability", "") == "available" else None),
                )
            )
        results.append(
            SearchResult(
                title=representative.title,
                author=representative.author,
                narrator=", ".join(narrators),
                url=representative.url,
                source="poleknig.com",
                variant_count=max(1, len(variants)),
                narration_variants=variants,
                availability=(
                    "available" if any(getattr(v, "available", None) is True for v in variants)
                    else "restricted" if variants and all(getattr(v, "available", None) is False for v in variants)
                    else ""
                ),
            )
        )
    return results[:SEARCH_RESULT_LIMIT]


__all__ = [
    "BASE_URL", "SEARCH_URL", "fetch_book", "parse_book_html", "parse_search_results",
    "search", "_book_page_metadata", "_tracks_from_playerjs", "_search_last_page",
    "_logical_title_key", "_discover_narration_variants", "_fetch_author_catalog",
    "_expand_matching_author_catalogs", "_book_page_author_links",
]
