from __future__ import annotations

import html as html_lib
import json
import re
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import replace
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .core import Cancelled, get_http_session, parse_time_seconds
from .models import Book, NarrationVariant, SearchResult, Track
from .sources import KNIGAVUHE_HOST, normalize_supported_url, source_key

BASE_URL = f"https://{KNIGAVUHE_HOST}/"
SEARCH_URL = urljoin(BASE_URL, "search/")
_BOOK_PATH_RE = re.compile(r"^/book/[^/?#]+/?$", re.I)
_RESTRICTED_MARKERS = (
    "доступ к аудиокниге ограничен по просьбе правообладателя",
    "доступ к книге ограничен по просьбе правообладателя",
)

# Knigavuhe currently exposes 10 books per search page.  AudioKnigi keeps the
# historical 100-result ceiling, so following at most ten pages gives complete
# results for normal searches without hammering the site for extremely broad
# queries that can contain hundreds of pages.
SEARCH_RESULT_LIMIT = 100
SEARCH_PAGE_LIMIT = 10
SEARCH_PAGE_WORKERS = 4


def _iter_completed_cancellable(futures, cancel_event=None):
    """Yield completed futures while polling cancellation independently of I/O."""
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


def _clean_text(value) -> str:
    text = html_lib.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\u2060", "")
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([!?,.;:])", r"\1", text)


def _extract_call_argument(text: str, marker: str = "BookController.enter") -> str:
    """Extract the first JS function argument while respecting strings/nesting."""
    source = str(text or "")
    pos = source.find(marker)
    if pos < 0:
        return ""
    open_pos = source.find("(", pos + len(marker))
    if open_pos < 0:
        return ""

    in_string = False
    quote = ""
    escaped = False
    brace_depth = 0
    bracket_depth = 0
    paren_depth = 0
    start = None
    for idx in range(open_pos + 1, len(source)):
        ch = source[idx]
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
            brace_depth += 1
        elif ch == "}":
            brace_depth = max(0, brace_depth - 1)
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif ch == "(":
            paren_depth += 1
        elif ch == ")" and brace_depth == 0 and bracket_depth == 0:
            if paren_depth > 0:
                paren_depth -= 1
                continue
            if start is None:
                return ""
            return source[start:idx].strip()
        elif ch == "," and brace_depth == 0 and bracket_depth == 0 and paren_depth == 0:
            if start is None:
                return ""
            return source[start:idx].strip()
    return ""


def _extract_names(value) -> list[str]:
    result: list[str] = []

    def walk(obj):
        if isinstance(obj, dict):
            name = _clean_text(obj.get("name", ""))
            if name and name not in result:
                result.append(name)
            for child in obj.values():
                if isinstance(child, (dict, list, tuple)):
                    walk(child)
        elif isinstance(obj, (list, tuple)):
            for child in obj:
                walk(child)
        elif isinstance(obj, str):
            name = _clean_text(obj)
            if name and name not in result:
                result.append(name)

    walk(value)
    return result


class _BookDescriptionParser(HTMLParser):
    """Extract book description without depending on HTML attribute order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._depth = 0
        self._chunks: list[str] = []
        self.meta_description = ""

    def handle_starttag(self, tag, attrs):
        name = str(tag or "").lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if name == "meta" and not self.meta_description:
            marker = str(attrs_dict.get("name") or attrs_dict.get("property") or "").casefold()
            if marker in {"description", "og:description"}:
                self.meta_description = _clean_text(attrs_dict.get("content", ""))
        if self._depth > 0:
            if name == "div":
                self._depth += 1
            return
        if name == "div":
            classes = str(attrs_dict.get("class", "") or "").casefold().split()
            normalized_classes = {re.sub(r"[^a-z0-9]+", "", value) for value in classes}
            if "bookdescription" in normalized_classes:
                self._depth = 1

    def handle_data(self, data):
        if self._depth > 0:
            text = _clean_text(data)
            if text:
                self._chunks.append(text)

    def handle_endtag(self, tag):
        if self._depth > 0 and str(tag or "").lower() == "div":
            self._depth -= 1

    @property
    def description(self) -> str:
        return _clean_text(" ".join(self._chunks)) or self.meta_description


def _description_from_html(html_text: str) -> str:
    parser = _BookDescriptionParser()
    try:
        parser.feed(html_text or "")
        parser.close()
    except Exception:
        pass
    return parser.description


def _absolute_audio_url(page_url: str, value) -> str:
    raw = str(value or "").replace("\\/", "/").strip()
    return urljoin(page_url, raw) if raw else ""


def _fallback_script_book(html_text: str, page_url: str) -> Book | None:
    """Legacy fallback based on direct MP3 URLs embedded in page scripts.

    This mirrors the simpler Python downloader supplied with the project and is
    intentionally used only when BookController data is absent.
    """
    normalized = (html_text or "").replace("\\/", "/")
    urls = re.findall(r'https?://[^"\'\s<>]+?\.mp3(?:\?[^"\'\s<>]*)?', normalized, re.I)
    unique = []
    for value in urls:
        value = value.strip()
        if value.endswith("/0.mp3") or value in unique:
            continue
        unique.append(value)
    if not unique:
        return None

    page_title = ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text or "", re.I | re.S)
    if title_match:
        page_title = _clean_text(title_match.group(1))
    title = re.sub(r"\s*\(слушать аудиокнигу.*$", "", page_title, flags=re.I).strip()
    author = ""
    author_match = re.search(r"[—–-]\s*автор\s+(.+)$", page_title, re.I)
    if author_match:
        author = _clean_text(author_match.group(1))
        title = re.sub(r"\s*[—–-]\s*автор\s+.+$", "", title, flags=re.I).strip()

    tracks = [
        Track(index=idx, title=f"{idx:03d}", file=url, selected=True)
        for idx, url in enumerate(unique, 1)
    ]
    return Book(
        url=page_url,
        title=title or "Аудиокнига",
        author=author,
        description=_description_from_html(html_text),
        tracks=tracks,
    )


class _NarrationVariantsParser(HTMLParser):
    """Extract anchors only from the book page's ``Другие озвучки`` section.

    Knigavuhe has used two layouts: older pages link the book title and reader
    separately, while the current new-design page links the alternative book
    URL with the reader name as the anchor text. Collection stops explicitly
    at comments/recommendations so unrelated links can never become a reader.
    """

    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.active = False
        self.anchors: list[dict[str, str]] = []
        self._current: dict[str, object] | None = None
        self._context_stack: list[tuple[str, set[str], str]] = []

    def handle_starttag(self, tag, attrs):
        name = str(tag or "").lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        classes = set(str(attrs_dict.get("class", "") or "").casefold().split())
        element_id = str(attrs_dict.get("id", "") or "").casefold()
        self._context_stack.append((name, classes, element_id))
        if self.active:
            if element_id == "comments_block" or "comments_block" in classes:
                self.active = False
                self._current = None
                return
        if name != "a" or not self.active:
            return
        href = attrs_dict.get("href", "")
        self._current = {"href": str(href or ""), "text": []}

    def handle_data(self, data):
        text = _clean_text(data)
        if not text:
            return
        lowered = text.casefold()
        if "другие озвучки" in lowered:
            heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}
            marker_tokens = (
                "narrat", "voice", "reader", "variant", "ozvuch",
                "block_title", "block-title", "caption", "sidebar_header",
                "sidebar-header", "heading", "header",
            )
            structural_heading = any(node[0] in heading_tags for node in self._context_stack)
            named_container = any(
                node[0] in {"div", "section", "span", "strong", "b"}
                and any(token in " ".join((*node[1], node[2])) for token in marker_tokens)
                for node in self._context_stack
            )
            if structural_heading or named_container:
                self.active = True
                self._current = None
                return
        if self.active and (lowered.startswith("рекомендац") or lowered.startswith("комментар")):
            self.active = False
            self._current = None
            return
        if self.active and self._current is not None:
            self._current["text"].append(text)

    def handle_endtag(self, tag):
        name = str(tag or "").lower()
        if name == "a" and self._current is not None:
            href = str(self._current.get("href", "") or "")
            text = _clean_text(" ".join(self._current.get("text", [])))
            if href and text:
                self.anchors.append({"href": href, "text": text})
            self._current = None
        for idx in range(len(self._context_stack) - 1, -1, -1):
            if self._context_stack[idx][0] == name:
                del self._context_stack[idx:]
                break


def _extract_narration_variants(
    html_text: str,
    page_url: str,
    title: str = "",
    current_narrator: str = "",
) -> list[NarrationVariant]:
    """Return current + alternative recordings linked from a Knigavuhe page."""
    variants: list[NarrationVariant] = []
    current_url = _canonical_search_book_url(page_url, page_url) or page_url
    clean_title = _clean_text(title)
    if current_url:
        variants.append(
            NarrationVariant(
                url=current_url,
                narrator=_clean_text(current_narrator),
                title=clean_title,
                current=True,
            )
        )

    parser = _NarrationVariantsParser(page_url)
    try:
        parser.feed(html_text or "")
        parser.close()
    except Exception:
        return variants

    seen = {v.url for v in variants if v.url}
    pending_old_layout: tuple[str, str] | None = None
    normalized_title = clean_title.casefold().replace("ё", "е")

    def add_variant(url: str, narrator: str = "", variant_title: str = ""):
        if not url or url in seen:
            return
        variants.append(
            NarrationVariant(
                url=url,
                narrator=_clean_text(narrator),
                title=_clean_text(variant_title) or clean_title,
            )
        )
        seen.add(url)

    for anchor in parser.anchors:
        href = anchor.get("href", "")
        label = _clean_text(anchor.get("text", ""))
        book_url = _canonical_search_book_url(page_url, href)
        if book_url:
            if pending_old_layout is not None:
                old_url, old_title = pending_old_layout
                add_variant(old_url, "", old_title)
                pending_old_layout = None

            normalized_label = label.casefold().replace("ё", "е")
            looks_like_title = bool(
                normalized_title
                and (
                    normalized_label == normalized_title
                    or re.search(
                        rf"(?<!\w){re.escape(normalized_title)}(?!\w)",
                        normalized_label,
                    )
                )
            )
            if looks_like_title:
                pending_old_layout = (book_url, label)
            else:
                # Current new-design layout: the /book/... link text is the reader.
                add_variant(book_url, label, clean_title)
            continue

        if pending_old_layout is not None and label:
            old_url, old_title = pending_old_layout
            try:
                linked_path = (urlparse(urljoin(page_url, href)).path or "").casefold()
            except Exception:
                linked_path = ""
            if linked_path.startswith(("/author/", "/genre/", "/series/")):
                # Old Knigavuhe cards may place author/genre links between the
                # alternative book link and its reader. Do not mistake those
                # labels for a narrator; keep waiting for the explicit reader.
                continue
            if linked_path.startswith(("/reader/", "/performer/", "/narrator/")):
                add_variant(old_url, label, old_title or clean_title)
                pending_old_layout = None
                continue
            # Unknown non-book links are ignored conservatively. The pending
            # recording is still emitted without a reader name at section end,
            # and hydration can recover the canonical narrator from its page.
            continue

    if pending_old_layout is not None:
        old_url, old_title = pending_old_layout
        add_variant(old_url, "", old_title or clean_title)
    return variants


def _hydrate_narration_variant_readers(variants: list[NarrationVariant], current_url: str = "", cancel_event=None) -> list[NarrationVariant]:
    """Fill missing reader names from each alternative book page."""
    # Hydration is an enrichment step; do not mutate caller-owned variants in
    # place. Worker futures return metadata and the coordinator applies it to
    # these clones on one thread.
    items = [replace(item) for item in (variants or [])]
    if len(items) <= 1:
        return items
    current = _canonical_search_book_url(current_url, current_url) or current_url
    # Re-read every alternative page, not only blank labels. Older Knigavuhe
    # markup may provide a grammatical form such as «Ильи Кривошеева»; the
    # alternative page heading gives the canonical reader name «Илья Кривошеев».
    indices = [
        idx for idx, item in enumerate(items)
        if (_canonical_search_book_url(current_url, getattr(item, "url", "")) or getattr(item, "url", "")) != current
    ]
    if not indices:
        return items

    def load(idx: int):
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Операция отменена пользователем")
        item = items[idx]
        session = get_http_session()
        response = session.get(
            item.url,
            headers={"Referer": current_url or BASE_URL},
            cookies={"new_design": "1"},
            timeout=(5, 12),
            allow_redirects=True,
        )
        response.raise_for_status()
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Операция отменена пользователем")
        return idx, _book_page_search_metadata(response.text or "")

    workers = min(4, len(indices))
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="knigavuhe-readers")
    futures = {}
    try:
        futures = {pool.submit(load, idx): idx for idx in indices}
        for future in _iter_completed_cancellable(futures, cancel_event):
            idx = futures[future]
            try:
                _idx, meta = future.result()
            except Cancelled:
                raise
            except Exception:
                continue
            narrator = _clean_text(meta.get("narrator", ""))
            title_text = _clean_text(meta.get("title", ""))
            if narrator:
                items[idx].narrator = narrator
            if title_text:
                items[idx].title = title_text
    finally:
        _shutdown_pool_now(pool, futures)
    return items


def parse_book_html(html_text: str, page_url: str) -> Book:
    lowered = (html_text or "").casefold()
    if any(marker in lowered for marker in _RESTRICTED_MARKERS):
        meta = _book_page_search_metadata(html_text)
        restricted_title = meta.get("title", "") or "Аудиокнига"
        restricted_narrator = meta.get("narrator", "")
        variants = _extract_narration_variants(
            html_text,
            page_url,
            title=restricted_title,
            current_narrator=restricted_narrator,
        )
        # If the site exposes other recordings, return metadata-only Book so the
        # GUI can offer an accessible reader selector instead of dead-ending on
        # a rights-restricted recording.  We still never bypass the restriction.
        if len(variants) > 1:
            return Book(
                url=page_url,
                title=restricted_title,
                author=meta.get("author", ""),
                narrator=restricted_narrator,
                description=_description_from_html(html_text),
                tracks=[],
                narration_variants=variants,
                restricted=True,
            )
        raise RuntimeError(
            "Доступ к этой аудиокниге ограничен по просьбе правообладателя. "
            "AudioKnigi Downloader не обходит ограничения сайта."
        )

    payload_text = _extract_call_argument(html_text)
    if not payload_text:
        fallback_book = _fallback_script_book(html_text, page_url)
        if fallback_book is not None:
            return fallback_book
        raise RuntimeError("На странице knigavuhe.org не найден плейлист BookController или прямые MP3-ссылки.")
    try:
        # ``\/`` is valid JSON escaping. Let json.loads decode it instead of
        # rewriting the raw payload first; pre-replacement can corrupt strings
        # containing an escaped backslash immediately before a slash.
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        fallback_book = _fallback_script_book(html_text, page_url)
        if fallback_book is not None:
            return fallback_book
        raise RuntimeError(f"Не удалось разобрать данные книги knigavuhe.org: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Неизвестный формат данных книги knigavuhe.org.")

    book_data = payload.get("book") if isinstance(payload.get("book"), dict) else {}
    title = _clean_text(book_data.get("name") or payload.get("name"))
    if not title:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text or "", re.I | re.S)
        title = _clean_text(title_match.group(1) if title_match else "")
        title = re.sub(r"\s*\(слушать аудиокнигу.*$", "", title, flags=re.I).strip()

    authors = _extract_names(book_data.get("authors"))
    readers = _extract_names(book_data.get("readers"))
    cover_url = _absolute_audio_url(page_url, book_data.get("cover"))

    primary = payload.get("playlist") if isinstance(payload.get("playlist"), list) else []
    merged = payload.get("merged_playlist") if isinstance(payload.get("merged_playlist"), list) else []
    if not primary and merged:
        primary, merged = merged, []
    if not primary:
        raise RuntimeError("Плейлист knigavuhe.org пуст или недоступен.")

    tracks: list[Track] = []
    for pos, item in enumerate(primary, 1):
        if not isinstance(item, dict):
            continue
        file_url = _absolute_audio_url(page_url, item.get("url") or item.get("file"))
        if not file_url:
            continue
        fallback_url = ""
        if len(merged) == len(primary) and isinstance(merged[pos - 1], dict):
            fallback_url = _absolute_audio_url(
                page_url,
                merged[pos - 1].get("url") or merged[pos - 1].get("file"),
            )
            if fallback_url == file_url:
                fallback_url = ""
        track_index = len(tracks) + 1
        title_text = _clean_text(item.get("title")) or f"{track_index:03d}"
        duration = None
        for duration_key in ("duration", "length", "time"):
            duration = parse_time_seconds(item.get(duration_key))
            if duration is not None:
                break
        tracks.append(
            Track(
                index=track_index,
                title=title_text,
                file=file_url,
                fallback_file=fallback_url,
                duration=duration,
                selected=True,
            )
        )
    if not tracks:
        raise RuntimeError("В плейлисте knigavuhe.org нет аудиофайлов.")

    narrator_text = ", ".join(readers)
    narration_variants = _extract_narration_variants(
        html_text,
        page_url,
        title=title or "Аудиокнига",
        current_narrator=narrator_text,
    )

    return Book(
        url=page_url,
        title=title or "Аудиокнига",
        author=", ".join(authors),
        narrator=narrator_text,
        description=_description_from_html(html_text),
        cover_url=cover_url,
        tracks=tracks,
        narration_variants=narration_variants,
        playlist_url="",
    )


def fetch_book(url: str, cancel_event=None) -> Book:
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    canonical = normalize_supported_url(str(url or ""))
    try:
        parsed = urlparse(canonical)
    except Exception:
        parsed = None
    if (
        parsed is None
        or source_key(canonical) != "knigavuhe"
        or not _BOOK_PATH_RE.match(parsed.path or "")
    ):
        raise RuntimeError("Для knigavuhe.org нужна ссылка на страницу книги вида https://knigavuhe.org/book/...")
    session = get_http_session()
    response = session.get(
        canonical,
        headers={"Referer": BASE_URL},
        cookies={"new_design": "1"},
        timeout=(7, 15),
        allow_redirects=True,
    )
    response.raise_for_status()
    final_url = response.url or canonical
    book = parse_book_html(response.text or "", final_url)
    book.narration_variants = _hydrate_narration_variant_readers(
        list(getattr(book, "narration_variants", None) or []),
        final_url,
        cancel_event=cancel_event,
    )
    return book


class _BookLinkParser(HTMLParser):
    """Collect only direct book-page anchors from Knigavuhe search cards.

    Search cards contain several links around the same book (comments, authors,
    genres, readers).  In particular a comments counter points to
    ``/book/<slug>/#comments_block``.  That link must never become a search
    result.  A small anchor stack also keeps malformed/complex card markup from
    replacing the currently parsed book anchor when another ``<a>`` starts.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, list[str]]] = []
        self._anchors: list[dict | None] = []

    @staticmethod
    def _book_anchor(href: str) -> bool:
        try:
            parsed = urlparse(href)
        except Exception:
            return False
        # Anchors such as #comments_block are controls inside a result card,
        # not links to a distinct book result.  Query parameters are harmless
        # and are stripped later when the canonical URL is produced.
        return bool(not parsed.fragment and _BOOK_PATH_RE.match(parsed.path or ""))

    def handle_starttag(self, tag, attrs):
        name = str(tag or "").lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if name == "a":
            href = attrs_dict.get("href", "").strip()
            if self._book_anchor(href):
                self._anchors.append(
                    {
                        "href": href,
                        "labels": [attrs_dict.get("title", ""), attrs_dict.get("aria-label", "")],
                        "text": [],
                    }
                )
            else:
                self._anchors.append(None)
            return
        if name == "img" and self._anchors and self._anchors[-1] is not None:
            current = self._anchors[-1]
            for key in ("alt", "title"):
                value = attrs_dict.get(key, "")
                if value:
                    current["labels"].append(value)

    def handle_data(self, data):
        if self._anchors and self._anchors[-1] is not None and data:
            self._anchors[-1]["text"].append(data)

    def handle_endtag(self, tag):
        if str(tag or "").lower() != "a" or not self._anchors:
            return
        current = self._anchors.pop()
        if current is None:
            return
        visible = _clean_text(" ".join(current["text"]))
        # Visible anchor text is the strongest title signal.  Image alt/title
        # and accessibility labels are useful fallbacks for cover-only links.
        labels = [visible, *current["labels"]]
        cleaned = []
        for value in labels:
            value = _clean_text(value)
            if value and value not in cleaned:
                cleaned.append(value)
        if cleaned:
            self.links.append((current["href"], cleaned))


class _BookCardParser(HTMLParser):
    """Parse the current Knigavuhe ``.bookitem`` search-card structure.

    The cover link contains genre text, while ``.bookitem_name`` contains the
    actual book title. Author and reader are likewise in dedicated metadata
    blocks. Reading those structural classes prevents genre/reader labels from
    being mistaken for a title and avoids detail-page requests in the normal
    current template.
    """

    def __init__(self, base_url: str = SEARCH_URL):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.results: list[SearchResult] = []
        self._card = None
        self._div_depth = 0
        self._field_depths: dict[str, int | None] = {
            "title": None,
            "author": None,
            "narrator": None,
        }
        # Current markup uses div wrappers, but keep field capture resilient if
        # Knigavuhe moves these semantic classes onto <a>/<span>/<h3> later.
        self._field_tags: dict[str, str | None] = {
            "title": None,
            "author": None,
            "narrator": None,
        }

    @staticmethod
    def _classes(attrs_dict) -> set[str]:
        return {
            part
            for part in str(attrs_dict.get("class", "") or "").split()
            if part
        }

    def _finish_card(self):
        card = self._card or {}
        url = str(card.get("url") or card.get("cover_url") or "")
        # HTMLParser splits text around inline highlight spans.  Joining the
        # chunks without injecting extra spaces preserves words such as
        # ``Филатов`` + ``а`` -> ``Филатова``.
        title = _clean_text("".join(card.get("title", [])))
        if not title:
            title = _clean_text(card.get("cover_alt", ""))
        author = _clean_text(" ".join(card.get("author", [])))
        narrator = _clean_text(" ".join(card.get("narrator", [])))
        if url and _usable_search_title(title):
            self.results.append(
                SearchResult(
                    title=title,
                    author=author,
                    narrator=narrator,
                    url=url,
                    source="knigavuhe.org",
                )
            )
        self._card = None
        self._div_depth = 0
        for key in self._field_depths:
            self._field_depths[key] = None
            self._field_tags[key] = None

    def handle_starttag(self, tag, attrs):
        name = str(tag or "").lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        classes = self._classes(attrs_dict)

        if name == "div":
            if self._card is None and "bookitem" in classes:
                self._card = {
                    "url": "",
                    "cover_url": "",
                    "cover_alt": "",
                    "title": [],
                    "author": [],
                    "narrator": [],
                }
                self._div_depth = 1
                return
            if self._card is not None:
                self._div_depth += 1
                if "bookitem_name" in classes:
                    self._field_depths["title"] = self._div_depth
                if "icon_author" in classes or any(token in classes for token in {"bookitem_author", "bookitem-author"}):
                    self._field_depths["author"] = self._div_depth
                if "icon_reader" in classes or any(token in classes for token in {"bookitem_reader", "bookitem-reader"}):
                    self._field_depths["narrator"] = self._div_depth
                return

        if self._card is None:
            return

        if name != "div":
            semantic_classes = (
                ("title", "bookitem_name"),
                ("author", "icon_author"),
                ("narrator", "icon_reader"),
            )
            for field, class_name in semantic_classes:
                if class_name in classes:
                    self._field_tags[field] = name

        if name == "a":
            href = attrs_dict.get("href", "").strip()
            href_path = urlparse(urljoin(self.base_url, href)).path.casefold()
            if "/author/" in href_path or "/authors/" in href_path:
                self._field_tags["author"] = "a"
            elif "/reader/" in href_path or "/readers/" in href_path or "/narrator/" in href_path:
                self._field_tags["narrator"] = "a"
            canonical = _canonical_search_book_url(self.base_url, href)
            if canonical:
                # The title anchor (normally class=is_black) is authoritative.
                # Keep the cover URL only as a fallback because its visible text
                # is the genre in the current Knigavuhe template.
                if (
                    self._field_depths["title"] is not None
                    or self._field_tags["title"] is not None
                    or "is_black" in classes
                    or "bookitem_name" in classes
                ):
                    self._card["url"] = canonical
                elif "bookitem_cover" in classes and not self._card.get("cover_url"):
                    self._card["cover_url"] = canonical
            return

        if name == "img" and "bookitem_cover_img" in classes:
            alt = _clean_text(attrs_dict.get("alt", ""))
            if alt:
                self._card["cover_alt"] = alt

    def handle_data(self, data):
        if self._card is None or not data:
            return
        for field in ("title", "author", "narrator"):
            if self._field_depths[field] is not None or self._field_tags[field] is not None:
                self._card[field].append(data)

    def handle_endtag(self, tag):
        name = str(tag or "").lower()
        if self._card is None:
            return
        for field, field_tag in tuple(self._field_tags.items()):
            if field_tag == name:
                self._field_tags[field] = None
        if name != "div":
            return
        current_depth = self._div_depth
        for field, depth in tuple(self._field_depths.items()):
            if depth == current_depth:
                self._field_depths[field] = None
        self._div_depth -= 1
        if self._div_depth <= 0:
            self._finish_card()


def _search_last_page(html_text: str) -> int:
    """Return the last page exposed by Knigavuhe pagination controls."""
    pages = [1]
    for pattern in (
        r'data-page=["\'](\d+)["\']',
        r'[?&]page=(\d+)',
    ):
        for value in re.findall(pattern, html_text or "", flags=re.I):
            try:
                pages.append(max(1, int(value)))
            except (TypeError, ValueError):
                pass
    return max(pages)


def _canonical_search_book_url(base_url: str, href: str) -> str:
    absolute = urljoin(base_url or SEARCH_URL, href)
    try:
        parsed = urlparse(absolute)
    except Exception:
        return ""
    host = (parsed.hostname or "").lower()
    if host not in {KNIGAVUHE_HOST, "www." + KNIGAVUHE_HOST}:
        return ""
    if parsed.fragment or not _BOOK_PATH_RE.match(parsed.path or ""):
        return ""
    # Search-card tracking parameters do not identify a different book.
    path = parsed.path
    if not path.endswith("/"):
        path += "/"
    return f"https://{KNIGAVUHE_HOST}{path}"


def _usable_search_title(value: str) -> bool:
    text = _clean_text(value)
    if not text or len(text) > 240:
        return False
    if not re.search(r"[A-Za-zА-Яа-яЁёІіЇїЄє]", text):
        return False
    lowered = text.casefold().strip(" \t\r\n,;:–—-….")
    # Reject UI action labels without broad substring matching: legitimate book
    # titles such as "Отзыв посла" or "Комментарии к Галльской войне" must
    # remain searchable.  Counter-only review/comment links are still ignored.
    if lowered in {"на полку", "слушать онлайн", "подробнее", "просмотр"}:
        return False
    if re.fullmatch(r"(?:комментарии|отзывы)\s*(?:\(\d+\)|\d+)", lowered):
        return False
    return True


def parse_search_results(html_text: str, base_url: str = SEARCH_URL) -> list[SearchResult]:
    # Prefer the current structural card parser. It separates title, author and
    # reader directly from the search page and therefore cannot confuse the
    # genre text inside ``bookitem_cover`` with the book title.
    card_parser = _BookCardParser(base_url)
    try:
        card_parser.feed(html_text or "")
        card_parser.close()
    except Exception:
        pass
    if card_parser.results:
        seen = set()
        results = []
        for item in card_parser.results:
            if item.url in seen:
                continue
            seen.add(item.url)
            results.append(item)
        return results[:SEARCH_RESULT_LIMIT]

    # Backward-compatible fallback for older/minimal templates and fixtures.
    parser = _BookLinkParser()
    try:
        parser.feed(html_text or "")
        parser.close()
    except Exception:
        pass

    best_by_url: dict[str, str] = {}
    for href, labels in parser.links:
        canonical_url = _canonical_search_book_url(base_url, href)
        if not canonical_url:
            continue

        candidates = [label for label in labels if _usable_search_title(label)]
        if not candidates:
            continue

        # The first candidate is direct visible text.  Prefer it unless it is
        # suspiciously verbose; then fall back to concise aria/title/img text.
        visible = candidates[0]
        concise = [value for value in candidates if len(value) <= 180]
        if len(visible) <= 180:
            title = visible
        elif concise:
            title = min(concise, key=len)
        else:
            title = min(candidates, key=len)

        current = best_by_url.get(canonical_url)
        if current is None:
            best_by_url[canonical_url] = title
        else:
            # Prefer a natural title over a longer card/accessibility sentence.
            current_score = (len(current) > 180, len(current))
            title_score = (len(title) > 180, len(title))
            if title_score < current_score:
                best_by_url[canonical_url] = title

    return [
        SearchResult(title=title, url=url, source="knigavuhe.org")
        for url, title in best_by_url.items()
    ][:SEARCH_RESULT_LIMIT]



def _book_page_search_metadata(html_text: str) -> dict[str, str]:
    """Extract stable title/author/narrator metadata from a Knigavuhe book page.

    Knigavuhe search intentionally also matches performers/readers.  We hydrate
    every hit from its own book page so the application can distinguish
    "query matched author/title" from "query matched reader only".
    """
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text or "", re.I | re.S)
    page_title = _clean_text(match.group(1) if match else "")
    if not page_title:
        return {"title": "", "author": "", "narrator": ""}

    raw_page_title = page_title
    metadata_page_title = re.sub(
        r"\s*\(\s*слушать\s+аудиокнигу[^)]*\)", "", raw_page_title, flags=re.I
    ).strip()
    title = re.split(r"\s+[—–-]\s+автор\s+", metadata_page_title, maxsplit=1, flags=re.I)[0].strip()

    author = ""
    narrator = ""
    author_match = re.search(
        r"(?:^|[—–-]\s*)автор\s+(.+?)(?=\s*,\s*читает\s+|$)",
        metadata_page_title,
        re.I,
    )
    if author_match:
        author = _clean_text(author_match.group(1))
    narrator_match = re.search(r"\s*,\s*читает\s+(.+?)\s*$", metadata_page_title, re.I)
    if narrator_match:
        narrator = _clean_text(narrator_match.group(1))

    # Older/newer templates may omit reader data from <title> but keep it in
    # the main heading.  This conservative fallback avoids reading comments or
    # recommendation text as metadata.
    if not author or not narrator:
        heading = re.search(r"<h1[^>]*>(.*?)</h1>", html_text or "", re.I | re.S)
        heading_text = _clean_text(heading.group(1) if heading else "")
        if heading_text:
            if not author:
                m = re.search(r"\bавтор\s+(.+?)(?=\s+читает\s+|$)", heading_text, re.I)
                if m:
                    author = _clean_text(m.group(1))
            if not narrator:
                m = re.search(r"\bчитает\s+(.+?)\s*$", heading_text, re.I)
                if m:
                    narrator = _clean_text(m.group(1))

    return {"title": title, "author": author, "narrator": narrator}


def _book_page_search_title(html_text: str) -> str:
    """Backward-compatible helper returning only the canonical book title."""
    return _book_page_search_metadata(html_text).get("title", "")


def _resolve_search_result_title(result: SearchResult) -> SearchResult:
    """Hydrate one search hit from its own book page without failing search."""
    try:
        session = get_http_session()
        response = session.get(
            result.url,
            headers={"Referer": SEARCH_URL},
            cookies={"new_design": "1"},
            timeout=(5, 12),
            allow_redirects=True,
        )
        response.raise_for_status()
        html_text = response.text or ""
        meta = _book_page_search_metadata(html_text)
        title = meta.get("title", "")
        if _usable_search_title(title):
            availability = "available"
            if any(marker in html_text.casefold() for marker in _RESTRICTED_MARKERS):
                availability = "restricted"
            return SearchResult(
                title=title,
                url=result.url,
                source=result.source,
                author=meta.get("author", ""),
                narrator=meta.get("narrator", ""),
                availability=availability,
            )
    except Exception:
        # Search must remain useful even if one detail page is temporarily
        # unavailable.  In that case keep the card-derived fallback label.
        pass
    return result


def _hydrate_search_result_titles(results: list[SearchResult], query: str = "", cancel_event=None) -> list[SearchResult]:
    """Resolve Knigavuhe metadata concurrently and retain title/author/reader matches."""
    items = list(results or [])
    if not items:
        return []
    resolved = list(items)
    unresolved_indices = [
        idx for idx, item in enumerate(items)
        # Resolve the detail page whenever author/reader metadata is incomplete,
        # because Knigavuhe itself supports searching by performer.
        if not str(getattr(item, "author", "") or "").strip()
        or not str(getattr(item, "narrator", "") or "").strip()
    ]
    workers = min(6, len(unresolved_indices))
    if workers > 0:
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="knigavuhe-title")
        futures = {}
        try:
            futures = {
                pool.submit(_resolve_search_result_title, items[idx]): idx
                for idx in unresolved_indices
            }
            for future in _iter_completed_cancellable(futures, cancel_event):
                idx = futures[future]
                try:
                    resolved[idx] = future.result()
                except Cancelled:
                    raise
                except Exception:
                    resolved[idx] = items[idx]
        finally:
            _shutdown_pool_now(pool, futures)

    # Knigavuhe's own search also matches reader, description, series and genre.
    # Hydration enriches metadata only; do not second-guess the site's relevance
    # ranking by dropping a result just because the query is absent from the
    # title/author/reader fields we happen to expose.
    return resolved


def _merge_narration_variants(*variant_lists) -> list[NarrationVariant]:
    merged: list[NarrationVariant] = []
    by_url: dict[str, NarrationVariant] = {}
    for values in variant_lists:
        for item in values or []:
            url = _canonical_search_book_url(BASE_URL, str(getattr(item, "url", "") or ""))
            if not url:
                continue
            current = by_url.get(url)
            if current is None:
                clone = replace(item, url=url)
                by_url[url] = clone
                merged.append(clone)
                continue
            if not _clean_text(getattr(current, "narrator", "")) and _clean_text(getattr(item, "narrator", "")):
                current.narrator = _clean_text(getattr(item, "narrator", ""))
            if not _clean_text(getattr(current, "title", "")) and _clean_text(getattr(item, "title", "")):
                current.title = _clean_text(getattr(item, "title", ""))
            if getattr(item, "current", False):
                current.current = True
    return merged


def _enrich_search_result_variants(result: SearchResult) -> SearchResult:
    """Read one detail page to count all Knigavuhe recordings accurately."""
    try:
        session = get_http_session()
        response = session.get(
            result.url,
            headers={"Referer": SEARCH_URL},
            cookies={"new_design": "1"},
            timeout=(5, 12),
            allow_redirects=True,
        )
        response.raise_for_status()
        html_text = response.text or ""
        meta = _book_page_search_metadata(html_text)
        page_variants = _extract_narration_variants(
            html_text,
            response.url or result.url,
            title=meta.get("title", "") or result.title,
            current_narrator=meta.get("narrator", "") or result.narrator,
        )
        variants = _merge_narration_variants(
            list(getattr(result, "narration_variants", None) or []),
            page_variants,
        )
        availability = "available"
        if any(marker in html_text.casefold() for marker in _RESTRICTED_MARKERS):
            availability = "restricted"
        return SearchResult(
            title=meta.get("title", "") or result.title,
            author=meta.get("author", "") or result.author,
            narrator=meta.get("narrator", "") or result.narrator,
            url=result.url,
            source=result.source,
            variant_count=max(1, len(variants), int(getattr(result, "variant_count", 1) or 1)),
            narration_variants=variants,
            availability=availability,
        )
    except Exception:
        return result


def enrich_search_variants(results: list[SearchResult], cancel_event=None) -> list[SearchResult]:
    """Add accurate variant counts to logical Knigavuhe search rows."""
    items = list(results or [])
    if not items:
        return []
    resolved = list(items)
    workers = min(8, len(items))
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="knigavuhe-variants")
    futures = {}
    try:
        futures = {pool.submit(_enrich_search_result_variants, item): idx for idx, item in enumerate(items)}
        for future in _iter_completed_cancellable(futures, cancel_event):
            idx = futures[future]
            try:
                resolved[idx] = future.result()
            except Cancelled:
                raise
            except Exception:
                resolved[idx] = items[idx]
    finally:
        _shutdown_pool_now(pool, futures)
    return resolved


def _fetch_search_page(query: str, page: int = 1):
    session = get_http_session()
    params = {"q": str(query or "").strip()}
    if int(page) > 1:
        params["page"] = int(page)
    response = session.get(
        SEARCH_URL,
        params=params,
        headers={"Referer": BASE_URL},
        cookies={"new_design": "1"},
        timeout=(10, 35),
    )
    response.raise_for_status()
    return response


def search(query: str, cancel_event=None) -> list[SearchResult]:
    """Search Knigavuhe across its paginated result pages.

    The site currently exposes ten books per page. AudioKnigi follows the
    pagination automatically up to the application's 100-result limit. Pages
    after the first are fetched concurrently, then merged in page order and
    deduplicated by canonical book URL.
    """
    query_text = str(query or "").strip()
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    first = _fetch_search_page(query_text, 1)
    first_html = first.text or ""
    first_url = first.url or SEARCH_URL
    pages: dict[int, list[SearchResult]] = {
        1: parse_search_results(first_html, first_url),
    }

    last_page = _search_last_page(first_html)
    target_last_page = min(last_page, SEARCH_PAGE_LIMIT)
    if target_last_page > 1:
        workers = min(SEARCH_PAGE_WORKERS, target_last_page - 1)
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="knigavuhe-search")
        futures = {}
        try:
            futures = {
                pool.submit(_fetch_search_page, query_text, page): page
                for page in range(2, target_last_page + 1)
            }
            for future in _iter_completed_cancellable(futures, cancel_event):
                page = futures[future]
                try:
                    response = future.result()
                    pages[page] = parse_search_results(
                        response.text or "",
                        response.url or SEARCH_URL,
                    )
                except Exception:
                    # A transient page-specific failure must not destroy already
                    # collected results from the same provider.
                    pages[page] = []
        finally:
            _shutdown_pool_now(pool, futures)

    combined: list[SearchResult] = []
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

    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    hydrated = _hydrate_search_result_titles(combined, query_text, cancel_event=cancel_event)

    # Collapse separate recording pages into one logical search row while
    # preserving every URL already present in the search index as a variant.
    # Determine whether a title has one known author or genuinely collides
    # across different authors. Authorless recording pages may safely join the
    # sole known author, but must not collapse distinct books that share a title.
    authors_by_title: dict[str, set[str]] = {}
    for item in hydrated:
        title_key = _clean_text(item.title).casefold().replace("ё", "е")
        author_key = _clean_text(getattr(item, "author", "")).casefold().replace("ё", "е")
        if title_key and author_key:
            authors_by_title.setdefault(title_key, set()).add(author_key)

    grouped: dict[tuple[str, str], list[SearchResult]] = {}
    order: list[tuple[str, str]] = []
    for item in hydrated:
        title_key = _clean_text(item.title).casefold().replace("ё", "е")
        author_key = _clean_text(getattr(item, "author", "")).casefold().replace("ё", "е")
        known_authors = authors_by_title.get(title_key, set())
        if not title_key:
            key = (item.url, "")
        elif len(known_authors) == 1:
            key = (title_key, next(iter(known_authors)))
        elif author_key:
            key = (title_key, author_key)
        else:
            # Ambiguous authorless hit: keep it independent rather than merge
            # it into the wrong book with the same title.
            key = (item.url, "")
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        if all(existing.url != item.url for existing in grouped[key]):
            grouped[key].append(item)

    unique: list[SearchResult] = []
    for key in order:
        members = grouped[key]
        representative = members[0]
        variants = [
            NarrationVariant(
                url=item.url,
                narrator=_clean_text(getattr(item, "narrator", "")),
                title=representative.title,
                current=(idx == 0),
                available=(
                    False
                    if str(getattr(item, "availability", "") or "").casefold() == "restricted"
                    else True
                    if str(getattr(item, "availability", "") or "").casefold() == "available"
                    else None
                ),
            )
            for idx, item in enumerate(members)
        ]
        unique.append(
            SearchResult(
                title=representative.title,
                author=next((_clean_text(item.author) for item in members if _clean_text(item.author)), ""),
                narrator=next((_clean_text(item.narrator) for item in members if _clean_text(item.narrator)), ""),
                url=representative.url,
                source=representative.source,
                variant_count=max(1, len(variants)),
                narration_variants=variants,
                availability=(
                    "available"
                    if any(str(getattr(item, "availability", "") or "").casefold() == "available" for item in members)
                    else str(getattr(representative, "availability", "") or "")
                ),
            )
        )
        if len(unique) >= SEARCH_RESULT_LIMIT:
            break
    return unique


__all__ = [
    "BASE_URL", "SEARCH_URL", "fetch_book", "parse_book_html",
    "parse_search_results", "search", "_extract_call_argument", "_fallback_script_book",
    "_book_page_search_title", "_book_page_search_metadata", "_hydrate_search_result_titles",
    "_search_last_page",
    "_extract_narration_variants", "_hydrate_narration_variant_readers",
    "_enrich_search_result_variants", "enrich_search_variants",
]
