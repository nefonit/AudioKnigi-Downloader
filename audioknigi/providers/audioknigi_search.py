from __future__ import annotations

"""Low-level audioknigi.com.ua search adapter used by the provider registry."""

import html as html_lib
from html.parser import HTMLParser
import re
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from urllib.parse import urljoin, urlparse

from ..core import Cancelled, extract_extended_metadata_from_html, extract_metadata_from_html, get_http_session
from ..models import NarrationVariant, SearchResult
from ..sources import AUDIOKNIGI_HOST

SEARCH_URL = f"https://{AUDIOKNIGI_HOST}/search"
_AUDIO_PATH_RE = re.compile(r"^/audio-\d+(?:[-/][^?#]*)?$", re.I)
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


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


def _clean_text(value) -> str:
    text = html_lib.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _canonical_title(value) -> str:
    """Return the human book title without AudioKnigi SEO decorations."""
    title = _clean_text(value)
    # Search-card title/alt attributes occasionally include the canonical site
    # URL as part of an SEO label.  A URL can never be part of a human title.
    title = re.sub(r"https?://(?:www\.)?audioknigi\.com\.ua/?\S*", " ", title, flags=re.I)
    title = re.sub(r"\b(?:www\.)?audioknigi\.com\.ua/?\b", " ", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(
        r"^(?:слушать\s+)?(?:онлайн\s+)?аудиокниг(?:а|у|и)(?:\s+онлайн)?\s*[:\-–—]?\s*",
        "",
        title,
        flags=re.I,
    ).strip(" -–—|:")
    # Current search/meta labels can also append SEO text after the real title:
    # ``Крыса аудиокнига слушать онлайн ...``.  Only strip suffix forms that
    # actually contain the listen/online wording, avoiding a generic deletion
    # of the word ``аудиокнига`` from a legitimate title.
    seo_tail = re.compile(
        r"\s*(?:[-–—|:]\s*)?(?:"
        r"аудиокниг(?:а|у|и)\s+(?:слушать(?:\s+онлайн)?|онлайн)"
        r"|слушать\s+(?:аудиокниг(?:а|у|и)\s+)?онлайн"
        r"|слушать\s+онлайн"
        r").*$",
        re.I,
    )
    title = seo_tail.sub("", title).strip(" -–—|:")
    return re.sub(r"\s+", " ", title).strip()


def _looks_like_author_prefix(value: str) -> bool:
    candidate = _clean_text(value)
    if not (2 <= len(candidate) <= 90) or any(ch.isdigit() for ch in candidate):
        return False
    # Reject acronym/series labels such as S.T.A.L.K.E.R. while retaining
    # ordinary initials ("А. С. Пушкин").
    if candidate.count(".") > 3:
        return False
    words = re.findall(r"[^\W\d_]+", candidate, re.UNICODE)
    if not (1 <= len(words) <= 6):
        return False
    if len(words) >= 2 and len(words[-1]) == 1 and words[-1].upper() in {"I", "V", "X"}:
        return False
    residue = re.sub(r"[^\W\d_]+", "", candidate, flags=re.UNICODE)
    return not residue.strip(" .'-’")


def _split_multi_author_prefix(value: str) -> tuple[str, str]:
    """Split AudioKnigi's ``Author 1, Author 2 - Title`` form safely.

    Multi-author prefixes are substantially less ambiguous than a generic
    two-word phrase before a dash, so require at least two comma/semicolon
    separated person-like chunks.  This fixes coauthor labels without turning
    ordinary dashed book titles into author metadata.
    """
    label = _canonical_title(value)
    parts = re.split(r"\s+[–—-]\s+", label, maxsplit=1)
    if len(parts) != 2:
        return label, ""
    prefix = _clean_text(parts[0])
    title = _clean_text(parts[1])
    if not prefix or not title:
        return label, ""
    authors = [
        _clean_text(item)
        for item in re.split(r"\s*(?:,|;)\s*", prefix)
        if _clean_text(item)
    ]
    if len(authors) < 2:
        return label, ""
    for author in authors:
        words = re.findall(r"[^\W\d_]+", author, re.UNICODE)
        if len(words) < 2 or not _looks_like_author_prefix(author):
            return label, ""
    return title, ", ".join(authors)


def _split_audioknigi_title(value: str) -> tuple[str, str]:
    label = _canonical_title(value)
    multi_title, multi_authors = _split_multi_author_prefix(label)
    if multi_authors:
        return multi_title, multi_authors
    parts = re.split(r"\s+[–—-]\s+", label, maxsplit=1)
    if len(parts) == 2:
        author = _clean_text(parts[0])
        title = _clean_text(parts[1])
        if author and title and _looks_like_author_prefix(author):
            return title, author
    return label, ""


def _normalize_text(value) -> str:
    return _canonical_title(value).casefold().replace("ё", "е")


_QUERY_NOISE_TOKENS = {"аудиокнига", "аудиокнигу", "аудиокниги", "слушать", "онлайн", "и", "в", "во", "на"}


def _query_tokens(query) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(_normalize_text(query))
        if token and token not in _QUERY_NOISE_TOKENS
    ]


def _response_html_text(response) -> str:
    """Decode a requests-like response without corrupting legacy Cyrillic pages."""
    content = bytes(getattr(response, "content", b"") or b"")
    if not content:
        return str(getattr(response, "text", "") or "")

    encodings: list[str] = ["utf-8-sig"]
    declared = str(getattr(response, "encoding", "") or "").strip()
    if declared:
        encodings.append(declared)
    try:
        apparent = str(getattr(response, "apparent_encoding", "") or "").strip()
    except Exception:
        apparent = ""
    if apparent:
        encodings.append(apparent)

    seen: set[str] = set()
    for encoding in encodings:
        folded = encoding.casefold()
        if not folded or folded in seen:
            continue
        seen.add(folded)
        try:
            return content.decode(encoding, errors="strict")
        except (LookupError, UnicodeDecodeError):
            continue
    # Last resort preserves evidence of malformed bytes rather than returning an
    # empty page or silently dropping data.
    return content.decode(declared or "utf-8", errors="replace")


def _matches_query(title: str, query: str, author: str = "", narrator: str = "") -> bool:
    haystack = _normalize_text(" ".join(part for part in (title, author, narrator) if part))
    tokens = _query_tokens(query)
    if not haystack:
        return False
    if not tokens:
        # A query made only of generic words such as "аудиокнига" should not
        # discard the search engine's own results during client-side hydration.
        return True

    # Single-letter query initials must not count merely because that character
    # appears somewhere inside a title/author word.  Longer query tokens retain
    # the historical substring behavior for conservative inflection/partial-name
    # matching.
    full_matches = {token for token in tokens if len(token) > 1 and token in haystack}
    if len(full_matches) == len(tokens):
        return True
    if not full_matches:
        return False

    person_haystack = _normalize_text(" ".join(part for part in (author, narrator) if part))
    person_tokens = _TOKEN_RE.findall(person_haystack)
    person_initials = {token for token in person_tokens if len(token) == 1}
    for token in tokens:
        if token in full_matches:
            continue
        if len(token) == 1:
            if token in person_initials or any(
                len(candidate) > 1 and candidate.startswith(token)
                for candidate in person_tokens
            ):
                continue
        elif token[:1] in person_initials:
            continue
        return False
    return True


def _title_score(title: str, query: str) -> tuple[int, int, int]:
    normalized_title = _normalize_text(title)
    normalized_query = _normalize_text(query)
    tokens = _query_tokens(query)
    exact_phrase = int(bool(normalized_query and normalized_query in normalized_title))
    token_hits = sum(token in normalized_title for token in tokens)
    shape_bonus = int(bool(re.search(r"\s[–—-]\s", title)))
    return exact_phrase, token_hits + shape_bonus, -min(len(title), 300)


def _logical_book_key(title: str, author: str) -> tuple[str, str]:
    def norm(value):
        return re.sub(r"\s+", " ", _clean_text(value).casefold().replace("ё", "е")).strip()

    return norm(title), norm(author)


class _AudioLinkParser(HTMLParser):
    """Collect labels attached to /audio-* links without CSS assumptions."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, list[str]]] = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        name = str(tag or "").lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if name == "a":
            href = attrs_dict.get("href", "").strip()
            try:
                path = urlparse(href).path
            except Exception:
                path = ""
            match_path = path if str(path or "").startswith("/") else "/" + str(path or "").lstrip("/")
            if _AUDIO_PATH_RE.match(match_path):
                labels = [attrs_dict.get("title", ""), attrs_dict.get("aria-label", "")]
                self._current = {"href": href, "labels": labels, "text": []}
            else:
                self._current = None
            return
        if name == "img" and self._current is not None:
            alt = attrs_dict.get("alt", "")
            title = attrs_dict.get("title", "")
            if alt:
                self._current["labels"].append(alt)
            if title:
                self._current["labels"].append(title)

    def handle_data(self, data):
        if self._current is not None and data:
            self._current["text"].append(data)

    def handle_endtag(self, tag):
        if str(tag or "").lower() != "a" or self._current is None:
            return
        visible = _clean_text(" ".join(self._current["text"]))
        visible = re.sub(r"\s+([!?,.;:])", r"\1", visible)
        labels = [visible, *self._current["labels"]]
        labels = [_clean_text(value) for value in labels]
        labels = [value for value in labels if value]
        self.links.append((self._current["href"], labels))
        self._current = None

def parse_audioknigi_results(html_text: str, base_url: str, query: str = "") -> list[SearchResult]:
    parser = _AudioLinkParser()
    try:
        parser.feed(html_text or "")
        parser.close()
    except Exception:
        pass

    best_by_url: dict[str, str] = {}
    for href, labels in parser.links:
        href_text = str(href or "").strip()
        try:
            href_parsed = urlparse(href_text)
        except Exception:
            href_parsed = None
        href_path = str(getattr(href_parsed, "path", "") or "")
        root_candidate = href_path if href_path.startswith("/") else "/" + href_path.lstrip("/")
        if href_parsed is not None and not href_parsed.scheme and not href_parsed.netloc and _AUDIO_PATH_RE.match(root_candidate):
            # DLE-style search pages sometimes emit ``audio-123-title`` without
            # a leading slash.  Those book routes are root-relative, not relative
            # to /search/page/N/.
            absolute = urljoin(base_url or SEARCH_URL, root_candidate)
        else:
            absolute = urljoin(base_url or SEARCH_URL, href_text)
        try:
            parsed = urlparse(absolute)
        except Exception:
            continue
        if (parsed.hostname or "").lower() not in {AUDIOKNIGI_HOST, "www." + AUDIOKNIGI_HOST}:
            continue
        if not _AUDIO_PATH_RE.match(parsed.path or ""):
            continue

        candidates = [_canonical_title(label) for label in labels if label]
        candidates = [label for label in candidates if label]
        if query:
            # Search cards often expose only the book title while the author is
            # stored elsewhere on the page. Trust the server result here and use
            # token hits only for ranking; strict title+author+narrator matching
            # happens after metadata hydration below.
            tokens = _query_tokens(query)
            matched = [label for label in candidates if any(token in _normalize_text(label) for token in tokens)]
            if matched:
                candidates = matched
        if not candidates:
            continue
        title = max(candidates, key=lambda value: _title_score(value, query))
        current = best_by_url.get(absolute)
        if current is None or _title_score(title, query) > _title_score(current, query):
            best_by_url[absolute] = title

    results: list[SearchResult] = []
    for url, label in best_by_url.items():
        multi_title, multi_authors = _split_multi_author_prefix(label)
        if multi_authors:
            book_title, author = multi_title, multi_authors
            author_inferred = False
        else:
            book_title, author = _split_audioknigi_title(label)
            author_inferred = bool(author)
        results.append(
            SearchResult(
                title=book_title,
                author=author,
                author_inferred=author_inferred,
                url=url,
                source=AUDIOKNIGI_HOST,
            )
        )
    results.sort(
        key=lambda item: _title_score(
            f"{item.author} - {item.title}" if item.author else item.title,
            query,
        ),
        reverse=True,
    )
    return results[:100]

def _strip_author_prefix_from_title(value: str, author: str) -> str:
    """Remove a proven author prefix, with or without a visual separator."""
    title = _canonical_title(value)
    author_text = _clean_text(author)
    if not title or not author_text:
        return title

    # An explicit separator is always safe.  A whitespace-only author prefix is
    # accepted only for multi-word author names; otherwise a legitimate title
    # such as ``Александр I`` would be misread as author ``Александр`` + title
    # ``I``.
    direct = re.match(rf"^\s*{re.escape(author_text)}\s*[-–—:]\s*(.+)$", title, re.I)
    if direct and _clean_text(direct.group(1)):
        return _clean_text(direct.group(1))

    def words_with_spans(text: str):
        return [
            (m.group(0).casefold().replace("ё", "е"), m.start(), m.end())
            for m in re.finditer(r"[^\W\d_]+", text, re.UNICODE)
        ]

    title_words = words_with_spans(title)
    author_words = [word for word, _start, _end in words_with_spans(author_text)]
    if len(title_words) < 2 or not author_words:
        return title
    author_set = set(author_words)
    if len(author_words) >= 2:
        direct_space = re.match(rf"^\s*{re.escape(author_text)}\s+(.+)$", title, re.I)
        if direct_space and _clean_text(direct_space.group(1)):
            return _canonical_title(direct_space.group(1))

    # Handles reordered names such as ``Бурносов Юрий Тоннельная крыса`` when
    # structured metadata independently says ``Юрий Бурносов``.  Require at
    # least two author tokens unless the exact-prefix path above already proved
    # a one-word author.  Never consume the complete title.
    max_prefix = min(len(author_words), len(title_words) - 1, 5)
    for count in range(max_prefix, 1, -1):
        prefix_tokens = [word for word, _start, _end in title_words[:count]]
        if set(prefix_tokens) <= author_set and len(set(prefix_tokens)) >= 2:
            remainder = title[title_words[count - 1][2]:].lstrip(" \t-–—:,|")
            if remainder:
                return _canonical_title(remainder)

    # Existing explicit-separator heuristic remains useful for short/initialed
    # author forms that are not textually identical to structured metadata.
    match = re.match(r"^(.{2,120}?)\s*[-–—:]\s*(.+)$", title)
    if not match:
        return title
    prefix, remainder = (_clean_text(part) for part in match.groups())
    prefix_tokens = {word for word, _start, _end in words_with_spans(prefix)}
    if prefix_tokens and prefix_tokens <= author_set:
        return _canonical_title(remainder) or title
    return title


def _looks_like_audioknigi_seo_description(value: str, *, title: str = "", author: str = "") -> bool:
    text = _clean_text(value)
    if not text:
        return True
    folded = text.casefold().replace("ё", "е")
    markers = (
        "скачать аудиокнигу", "слушать аудиокнигу", "аудиокнига слушать",
        "слушать онлайн", "audioknigi.com.ua",
    )
    if any(marker in folded for marker in markers):
        return True
    compact = re.sub(r"[^\w]+", " ", folded, flags=re.UNICODE).strip()
    title_key = re.sub(r"[^\w]+", " ", _canonical_title(title).casefold().replace("ё", "е"), flags=re.UNICODE).strip()
    author_key = re.sub(r"[^\w]+", " ", _clean_text(author).casefold().replace("ё", "е"), flags=re.UNICODE).strip()
    return bool(title_key and author_key and title_key in compact and author_key in compact and len(text) < 220)


def _meta_content(html_text: str, key: str) -> str:
    escaped = re.escape(str(key or ""))
    patterns = (
        rf'<meta\b[^>]*(?:name|property)=["\']{escaped}["\'][^>]*content=["\']([^"\']*)["\'][^>]*>',
        rf'<meta\b[^>]*content=["\']([^"\']*)["\'][^>]*(?:name|property)=["\']{escaped}["\'][^>]*>',
    )
    for pattern in patterns:
        match = re.search(pattern, html_text or "", re.I | re.S)
        if match:
            return _clean_text(match.group(1))
    return ""


def _audioknigi_description_lines(html_text: str) -> list[str]:
    """Return visible page text as stable block-like lines.

    AudioKnigi detail pages mix bibliographic fields, app advertising and the
    real synopsis inside the same broad content area.  Keeping common block
    boundaries lets us anchor the annotation to the ``краткое содержание``
    heading instead of treating the whole article container as a description.
    """
    text = re.sub(
        r"</?(?:p|div|section|article|br|h[1-6]|li|ul|ol|hr)\b[^>]*>",
        "\n",
        str(html_text or ""),
        flags=re.I,
    )
    text = html_lib.unescape(re.sub(r"<[^>]+>", " ", text))
    lines: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if line:
            lines.append(line)
    return lines


def _clean_audioknigi_description_candidate(value: str, *, title: str = "", author: str = "") -> str:
    text = _clean_text(value)
    if not text:
        return ""

    # Every current detail page places an SEO sentence immediately below the
    # synopsis heading, e.g. ``Title - описание и краткое содержание,
    # исполнитель: X, слушайте бесплатно онлайн ...``.  It is page chrome, not
    # the author's/book's annotation.
    text = re.sub(
        r"^.{0,260}?[-–—]\s*описание\s+и\s+краткое\s+содержание\s*,?\s*"
        r"(?:исполнитель\s*:[^,.]{1,140}\s*,?\s*)?"
        r"слушайте\s+бесплатно\s+онлайн\s+на\s+сайте\s+электронной\s+библиотеки\s+"
        r"AudioKnigi\.com\.ua\s*[.!?]?\s*",
        "",
        text,
        flags=re.I,
    ).strip()
    text = re.sub(
        r"^Тут\s+можно\s+слушать\s+бесплатно\b.{0,700}?"
        r"(?:отзывами?\s*\(комментариями?\)|AudioKnigi\.com\.ua)\s*[.!?]?\s*",
        "",
        text,
        flags=re.I,
    ).strip()

    # If a broad semantic container slipped through, cut everything after the
    # next site section rather than leaking player/comments/recommendations.
    text = re.split(
        r"\s+(?:.{0,180}?\s+)?(?:слушать\s+онлайн\s+бесплатно|отзывы(?:\s+слушателей)?|"
        r"комментарии|другие\s+озвучки|рекомендации)\b",
        text,
        maxsplit=1,
        flags=re.I,
    )[0].strip()
    if not text or _looks_like_audioknigi_seo_description(text, title=title, author=author):
        return ""
    return text


def _audioknigi_labeled_description(html_text: str, *, title: str = "", author: str = "") -> str:
    lines = _audioknigi_description_lines(html_text)
    if not lines:
        return ""
    heading_index = None
    for index, line in enumerate(lines):
        # The page intro also says "прочесть краткое содержание".  Treat only
        # a heading-like line that *ends* with the section name as the synopsis
        # anchor, otherwise we would start capturing author/reader/app metadata.
        if re.search(r"\bкраткое\s+содержание\s*[:\-–—]?\s*$", line, re.I):
            heading_index = index
            break
    if heading_index is None:
        return ""

    stop = re.compile(
        r"(?:слушать\s+онлайн\s+бесплатно|отзывы(?:\s+слушателей)?|комментарии|"
        r"другие\s+озвучки|рекомендации)\b",
        re.I,
    )
    chunks: list[str] = []
    for line in lines[heading_index + 1:]:
        if stop.search(line):
            break
        # Skip the site's fixed SEO bridge line and obvious UI/app advertising.
        folded = line.casefold().replace("ё", "е")
        if (
            ("описание и краткое содержание" in folded and "слушайте бесплатно онлайн" in folded)
            or folded.startswith("слушать эту аудиокнигу в приложении")
            or folded.startswith("добавляйте книги в android приложение")
        ):
            continue
        chunks.append(line)

    return _clean_audioknigi_description_candidate(
        " ".join(chunks), title=title, author=author
    )


def _audioknigi_description_from_html(html_text: str, *, title: str = "", author: str = "") -> str:
    """Extract the real AudioKnigi synopsis without page/player metadata."""
    html = str(html_text or "")

    # Prefer the exact visible section headed ``... краткое содержание``.
    # On the live site this sits after Author/Reader/genres/app promotion and
    # before the player/reviews sections, so it is substantially safer than a
    # generic ``shortstory``/``full-text`` container.
    labeled = _audioknigi_labeled_description(html, title=title, author=author)
    if labeled:
        return labeled

    visible: list[str] = []
    block_pattern = re.compile(
        r'<(?P<tag>div|section|article)\b(?P<attrs>[^>]*)>(?P<body>[\s\S]*?)</(?P=tag)>',
        re.I,
    )
    semantic = (
        "description", "annotation", "annot", "book-description", "book_description",
        "book-text", "book_text", "shortstory", "short-story", "story-text",
        "story_text", "full-text", "full_text",
    )
    for match in block_pattern.finditer(html):
        attrs = match.group("attrs") or ""
        marker = " ".join(re.findall(r'(?:class|id)=["\']([^"\']+)["\']', attrs, re.I)).casefold()
        if any(token in marker for token in semantic):
            clean = _clean_audioknigi_description_candidate(
                match.group("body"), title=title, author=author
            )
            # Broad DLE containers often contain Author/Reader/genres/player UI.
            # Reject them when several technical labels remain after cleaning.
            technical_hits = sum(
                bool(re.search(rf"\b{label}\s*:", clean, re.I))
                for label in ("Автор", "Исполнитель", "Серия", "Добавлено", "Жанр", "Год", "Размер", "Качество")
            )
            if clean and technical_hits < 2:
                visible.append(clean)

    structured, _narrator, _genre, _year = extract_extended_metadata_from_html(html)
    candidates = [*visible, structured, _meta_content(html, "og:description"), _meta_content(html, "description")]
    for candidate in candidates:
        clean = _clean_audioknigi_description_candidate(candidate, title=title, author=author)
        if clean:
            return clean
    return ""


def _author_name_tokens(value: str) -> tuple[set[str], set[str]]:
    tokens = re.findall(
        r"[^\W\d_]+",
        _clean_text(value).casefold().replace("ё", "е"),
        re.UNICODE,
    )
    return ({token for token in tokens if len(token) > 1}, {token for token in tokens if len(token) == 1})


def _same_author_identity(left: str, right: str) -> bool:
    """Match reordered/full-vs-initial author spellings without surname-only guesses."""
    left_words, left_initials = _author_name_tokens(left)
    right_words, right_initials = _author_name_tokens(right)
    if not left_words or not right_words:
        return _clean_text(left).casefold() == _clean_text(right).casefold()

    if left_words == right_words:
        # ``А. Иванов`` and ``Б. Иванов`` must remain distinct even though the
        # long-token set contains only the shared surname.
        if bool(left_initials) != bool(right_initials):
            return False
        if left_initials and right_initials and left_initials != right_initials:
            return False
        return True

    def initial_form_matches(short_words, initials, full_words) -> bool:
        if not initials or not short_words < full_words:
            return False
        expanded = full_words - short_words
        return all(any(word.startswith(initial) for word in expanded) for initial in initials)

    return initial_form_matches(left_words, left_initials, right_words) or initial_form_matches(
        right_words, right_initials, left_words
    )


def _author_detail_score(value: str) -> tuple[int, int, int]:
    words, initials = _author_name_tokens(value)
    return (len(words), -len(initials), len(_clean_text(value)))


def _merge_author_names(*values: str) -> str:
    authors: list[str] = []
    for value in values:
        for raw in re.split(r"\s*(?:,|;|\s+и\s+)\s*", _clean_text(value), flags=re.I):
            name = _clean_text(raw)
            if not name:
                continue
            duplicate_index = next(
                (index for index, existing in enumerate(authors) if _same_author_identity(name, existing)),
                None,
            )
            if duplicate_index is not None:
                if _author_detail_score(name) > _author_detail_score(authors[duplicate_index]):
                    authors[duplicate_index] = name
                continue
            authors.append(name)
    return ", ".join(authors)


def _audioknigi_plain_narrator(html_text: str) -> str:
    """Extract a reader label from ordinary page text when structured data omits it."""
    plain = _clean_text(html_text)
    match = re.search(
        r"(?:Исполнитель|Читает|Диктор)\s*:\s*(.{2,120}?)(?=\s*,?\s*(?:"
        r"Серия|Добавлено|Жанр|Автор|Краткое содержание|Описание|Время звучания|Год|Размер|Качество"
        r")\s*:|$)",
        plain,
        re.I,
    )
    return _clean_text(match.group(1)) if match else ""


def _audioknigi_page_metadata(
    result: SearchResult,
    *,
    session_factory=get_http_session,
    metadata_extractor=extract_metadata_from_html,
    extended_metadata_extractor=extract_extended_metadata_from_html,
) -> SearchResult:
    try:
        session = session_factory()
        response = session.get(
            result.url,
            headers={"Referer": SEARCH_URL},
            timeout=(7, 20),
            allow_redirects=True,
        )
        response.raise_for_status()
        html_text = _response_html_text(response)

        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
        page_label = _canonical_title(title_match.group(1) if title_match else "")
        page_book_title, page_authors = _split_multi_author_prefix(page_label)

        # Preserve every author signal independently.  AudioKnigi sometimes
        # renders ``Author 1, Author 2 - Title`` in the visible/page title while
        # JSON-LD exposes only one of those authors.
        title = page_book_title if page_authors else (page_label or result.title)
        result_author = _clean_text(result.author)
        meta_title, meta_author, _cover = metadata_extractor(html_text, title)
        meta_clean = _canonical_title(meta_title) if meta_title else ""
        meta_book_title, meta_prefix_authors = _split_multi_author_prefix(meta_clean)
        page_author = _merge_author_names(
            page_authors, _clean_text(meta_author), meta_prefix_authors
        )
        if bool(getattr(result, "author_inferred", False)) and page_author:
            # A single ``X - Y`` search label is inherently ambiguous (X can be
            # a series/character, e.g. "Гарри Поттер").  Once the detail page
            # supplies a real author, do not promote that search-card guess to
            # a coauthor.  Explicit card author fields and multi-author prefixes
            # remain trusted and continue to merge below.
            author = page_author
        else:
            author = _merge_author_names(result_author, page_author)
        if meta_clean:
            title = meta_book_title if meta_prefix_authors else meta_clean

        # Strip only an author that was independently observed in the search
        # card, multi-author page prefix or structured metadata.  This preserves
        # legitimate dashed titles such as "Гарри Поттер — Философский камень".
        if author:
            stripped = title
            for known_author in [part.strip() for part in author.split(",") if part.strip()]:
                candidate = _strip_author_prefix_from_title(stripped, known_author)
                if candidate != stripped:
                    stripped = candidate.lstrip(" ,;")
            title = stripped or title

        _description, narrator, _genre, _year = extended_metadata_extractor(html_text)
        if not narrator:
            narrator = _audioknigi_plain_narrator(html_text)

        return SearchResult(
            title=title or result.title,
            author=author or result.author,
            narrator=_clean_text(narrator) or result.narrator,
            url=result.url,
            source=result.source,
            variant_count=result.variant_count,
            narration_variants=list(result.narration_variants or []),
            availability="available",
        )
    except Exception:
        return result

def _group_audioknigi_recordings(results: list[SearchResult], cancel_event=None, query: str = "") -> list[SearchResult]:
    source_items = list(results or [])
    hydrated: list[SearchResult] = list(source_items)
    if source_items:
        workers = min(8, len(source_items))
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="audioknigi-readers")
        futures = {}
        try:
            futures = {pool.submit(_audioknigi_page_metadata, item): idx for idx, item in enumerate(source_items)}
            for future in _iter_completed_cancellable(futures, cancel_event):
                idx = futures[future]
                try:
                    hydrated[idx] = future.result()
                except Exception:
                    hydrated[idx] = source_items[idx]
        finally:
            _shutdown_pool_now(pool, futures)

    if query:
        # The site's search response can contain recommendations/sidebar links.
        # Re-check every hydrated result, even if detail metadata failed, so an
        # unrelated card can never survive merely because author/reader fields
        # are empty.  The title itself is always available as a fallback.
        hydrated = [
            item for item in hydrated
            if _matches_query(item.title, query, item.author, item.narrator)
        ]

    groups: dict[tuple[str, str], list[SearchResult]] = {}
    order: list[tuple[str, str]] = []
    for item in hydrated:
        key = _logical_book_key(item.title, item.author)
        if not key[0] or not key[1]:
            key = (f"url:{item.url}", "")
        if key not in groups:
            groups[key] = []
            order.append(key)
        if all(existing.url != item.url for existing in groups[key]):
            groups[key].append(item)

    grouped: list[SearchResult] = []
    for key in order:
        members = groups[key]
        representative = members[0]
        variants: list[NarrationVariant] = []
        narrators: list[str] = []
        seen_urls: set[str] = set()
        for idx, item in enumerate(members):
            if item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            narrator = _clean_text(getattr(item, "narrator", ""))
            if narrator and narrator not in narrators:
                narrators.append(narrator)
            variants.append(
                NarrationVariant(
                    url=item.url,
                    narrator=narrator,
                    title=representative.title or item.title,
                    current=(idx == 0),
                    available=True,
                )
            )

        grouped.append(
            SearchResult(
                title=representative.title,
                author=representative.author,
                narrator=", ".join(narrators),
                url=representative.url,
                source=AUDIOKNIGI_HOST,
                variant_count=max(1, len(variants)),
                narration_variants=variants,
                availability="available",
            )
        )
    return grouped

def search_audioknigi(query: str, cancel_event=None) -> list[SearchResult]:
    query_text = str(query or "").strip()
    if not query_text:
        return []
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Поиск отменён пользователем")
    session = get_http_session()
    response = session.get(
        SEARCH_URL,
        params={"text": query_text},
        timeout=(10, 30),
        headers={"Referer": f"https://{AUDIOKNIGI_HOST}/"},
    )
    response.raise_for_status()
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Поиск отменён пользователем")
    content = bytes(getattr(response, "content", b"") or b"")
    declared_encoding = str(getattr(response, "encoding", "") or "").strip().casefold()
    if declared_encoding and declared_encoding not in {"utf-8", "utf8", "utf-8-sig"}:
        html_text = _response_html_text(response)
    else:
        # Preserve the site's normal UTF-8/BOM path while allowing explicitly
        # declared legacy Cyrillic encodings to use the decoder above.
        html_text = content.decode("utf-8-sig", errors="replace")
        if not html_text:
            html_text = str(getattr(response, "text", "") or "")
    return _group_audioknigi_recordings(
        parse_audioknigi_results(html_text, response.url, query=query_text),
        cancel_event=cancel_event,
        query=query_text,
    )

__all__ = ["SEARCH_URL", "parse_audioknigi_results", "search_audioknigi"]
