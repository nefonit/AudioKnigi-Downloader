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
    title = _clean_text(value)
    title = re.sub(
        r"^(?:слушать\s+)?(?:онлайн\s+)?аудиокниг(?:а|у|и)(?:\s+онлайн)?\s*[:\-–—]?\s*",
        "",
        title,
        flags=re.I,
    ).strip(" -–—")
    return title


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


def _split_audioknigi_title(value: str) -> tuple[str, str]:
    label = _canonical_title(value)
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


def _matches_query(title: str, query: str, author: str = "", narrator: str = "") -> bool:
    haystack = _normalize_text(" ".join(part for part in (title, author, narrator) if part))
    tokens = _query_tokens(query)
    if not haystack:
        return False
    if not tokens:
        # A query made only of generic words such as "аудиокнига" should not
        # discard the search engine's own results during client-side hydration.
        return True
    full_matches = {token for token in tokens if token in haystack}
    if len(full_matches) == len(tokens):
        return True
    # Search cards often abbreviate first/middle names ("Л. Н. Толстой").
    # Permit an unmatched query name to match its initial only when at least
    # one other query token matched fully, preventing a lone "Лев" from
    # matching every author whose card merely contains "Л.".
    if not full_matches:
        return False
    # Initial expansion is meaningful only for person names.  Do not let a
    # one-letter word/preposition in the title satisfy an arbitrary first name.
    person_haystack = _normalize_text(" ".join(part for part in (author, narrator) if part))
    person_initials = {
        token for token in _TOKEN_RE.findall(person_haystack) if len(token) == 1
    }
    for token in tokens:
        if token in full_matches:
            continue
        if len(token) > 1 and token[:1] in person_initials:
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
            if _AUDIO_PATH_RE.match(path or ""):
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
        absolute = urljoin(base_url or SEARCH_URL, href)
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
        book_title, author = _split_audioknigi_title(label)
        results.append(
            SearchResult(
                title=book_title,
                author=author,
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
        content = bytes(getattr(response, "content", b"") or b"")
        html_text = content.decode("utf-8-sig", errors="replace") if content else (response.text or "")

        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
        page_label = _clean_text(title_match.group(1) if title_match else "")
        page_label = re.sub(r"\s+аудиокнига.*$", "", page_label, flags=re.I).strip()
        # A dash inside a book title is inherently ambiguous (for example
        # "Метро 2033 — Тёмные туннели").  Do not invent an author from the
        # HTML <title>; wait for independent structured metadata.
        title = page_label or result.title
        author = result.author
        meta_title, meta_author, _cover = metadata_extractor(html_text, title)
        if meta_author:
            author = _clean_text(meta_author)
        if meta_title:
            # Structured metadata wins over the ambiguous visual "A - B" title.
            # Only apply the dash heuristic when no independent author was parsed.
            if author:
                cleaned_meta = _clean_text(meta_title)
                author_text = _clean_text(author)
                if cleaned_meta and author_text and cleaned_meta.casefold().startswith(author_text.casefold()):
                    suffix = cleaned_meta[len(author_text):]
                    # Strip an author prefix only when structured metadata uses
                    # an explicit title separator.  Whitespace alone is
                    # ambiguous (e.g. a title such as "Александр I").
                    separator = re.match(r"^\s*[-–—:]\s*", suffix)
                    if separator and separator.end() > 0:
                        stripped = suffix[separator.end():].strip()
                        title = stripped or title
                    else:
                        title = cleaned_meta
                else:
                    title = cleaned_meta or title
            else:
                # Without a separately parsed author, preserve the complete
                # metadata title instead of guessing that text before a dash is
                # a person name.
                title = _clean_text(meta_title) or title

        _description, narrator, _genre, _year = extended_metadata_extractor(html_text)
        if not narrator:
            plain = _clean_text(html_text)
            match = re.search(
                r"(?:Исполнитель|Читает|Диктор)\s*:\s*(.{2,120}?)(?=\s*,?\s*(?:Серия|Добавлено|Жанр|Автор|Краткое содержание|Описание)\s*:|$)",
                plain,
                re.I,
            )
            if match:
                narrator = _clean_text(match.group(1))

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
        filtered: list[SearchResult] = []
        for item in hydrated:
            has_metadata = bool(str(getattr(item, "author", "") or "").strip() or str(getattr(item, "narrator", "") or "").strip())
            if not has_metadata or _matches_query(item.title, query, item.author, item.narrator):
                filtered.append(item)
        hydrated = filtered

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
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Поиск отменён пользователем")
    session = get_http_session()
    response = session.get(
        SEARCH_URL,
        params={"text": query},
        timeout=(10, 30),
        headers={"Referer": f"https://{AUDIOKNIGI_HOST}/"},
    )
    response.raise_for_status()
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Поиск отменён пользователем")
    html_text = bytes(getattr(response, "content", b"") or b"").decode("utf-8", errors="replace")
    if not html_text:
        html_text = str(getattr(response, "text", "") or "")
    return _group_audioknigi_recordings(
        parse_audioknigi_results(html_text, response.url, query=query),
        cancel_event=cancel_event,
        query=query,
    )

__all__ = ["SEARCH_URL", "parse_audioknigi_results", "search_audioknigi"]
