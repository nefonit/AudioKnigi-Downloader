from __future__ import annotations

import html as html_lib
import json
import re
import subprocess
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Callable
from urllib.parse import unquote, urljoin, urlsplit

from ..cover_fetch import fetch_cover_bytes
from ..download.common import close_subprocess_pipes
from ..core import (
    Cancelled,
    SiteStructureChanged,
    USER_AGENT,
    extract_extended_metadata_from_html,
    extract_metadata_from_html,
    effective_track_duration,
    get_http_session,
    hidden_subprocess_kwargs,
    load_browser_context_profile,
    parse_time_seconds,
    persist_browser_session,
    resolve_executable,
)
from ..knigavuhe import fetch_book as fetch_knigavuhe_book, search as search_knigavuhe_books
from ..poleknig import fetch_book as fetch_poleknig_book
from ..logging_utils import app_logger
from ..models import Book, Track, normalize_cover_cache
from ..network_dns import cloudflare_ffmpeg_input_args, launch_playwright_chromium
from ..sources import normalize_supported_url, source_key

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional runtime dependency
    sync_playwright = None

ProgressCallback = Callable[[str], None]


def _iter_completed_cancellable(futures, cancel_event):
    pending = set(futures)
    while pending:
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Операция отменена пользователем")
        done, pending = wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)
        for future in done:
            yield future


def _playlist_track_title(raw_title, file_url: str, index: int, book_title: str, total: int) -> str:
    """Turn machine/file playlist labels into stable human-readable track titles."""
    text = re.sub(r"\s+", " ", html_lib.unescape(str(raw_title or ""))).strip()
    if text:
        comma_parts = [part.strip() for part in text.split(",") if part.strip()]
        if len(comma_parts) > 1 and all(part.casefold() == comma_parts[0].casefold() for part in comma_parts):
            text = comma_parts[0]

    path_name = unquote(urlsplit(str(file_url or "")).path.rsplit("/", 1)[-1])
    stem = path_name.rsplit(".", 1)[0] if "." in path_name else path_name

    def compact(value: str) -> str:
        return re.sub(r"[^0-9a-zа-яё]+", "", str(value or "").casefold())

    matches_file_stem = bool(text and stem and compact(text) == compact(stem))
    slug_like = bool(
        text
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", text)
        and ("_" in text or "-" in text)
        and re.search(r"(?:[_-]?\d+)$", text)
    )
    if not text or matches_file_stem or slug_like:
        clean_book = re.sub(r"\s+", " ", str(book_title or "")).strip()
        if clean_book:
            return clean_book if total <= 1 else f"{clean_book} — {index:02d}"
        return f"{index:02d}"
    return text


@dataclass(slots=True)
class AnalysisOptions:
    playwright_fallback_enabled: bool = True
    fetch_cover: bool = True
    fetch_remote_size: bool = True


class BookAnalysisService:
    """Analyze supported audiobook URLs without importing any GUI toolkit.

    Phase 2 deliberately keeps cancellation and progress reporting as plain
    Python callbacks/events.  Qt, CLI or tests can therefore consume the
    same service without fake StringVar/widgets or UI compatibility adapters.
    """

    def __init__(
        self,
        *,
        cancel_event: threading.Event | None = None,
        progress: ProgressCallback | None = None,
        options: AnalysisOptions | None = None,
    ):
        self.cancel_event = cancel_event or threading.Event()
        self.progress = progress
        self.options = options or AnalysisOptions()
        self._duration_probe_lock = threading.RLock()
        self._duration_probe_processes: set[subprocess.Popen] = set()

    def _emit(self, message: str) -> None:
        callback = self.progress
        if callback is not None:
            callback(str(message or ""))

    def _check_cancel(self) -> None:
        if self.cancel_event.is_set():
            raise Cancelled("Операция отменена пользователем")

    def _register_duration_probe_process(self, proc: subprocess.Popen) -> None:
        with self._duration_probe_lock:
            self._duration_probe_processes.add(proc)

    def _unregister_duration_probe_process(self, proc: subprocess.Popen | None) -> None:
        if proc is None:
            return
        with self._duration_probe_lock:
            self._duration_probe_processes.discard(proc)

    def _cancel_duration_probe_processes(self) -> None:
        with self._duration_probe_lock:
            processes = tuple(self._duration_probe_processes)
        for proc in processes:
            try:
                if proc.poll() is None:
                    proc.kill()
            except (OSError, ProcessLookupError):
                pass

    def _probe_remote_duration(self, url: str, referer: str = "") -> float | None:
        """Best-effort duration probe for a public direct audio URL.

        PoleKnig and Knigavuhe often expose one media URL per chapter without
        start/end metadata.  The download engine has always filled those
        durations later, but the Qt analysis service must do the same before
        the track table is rendered.  Failure is non-fatal: the book remains
        usable and duration can still be learned after download.
        """
        self._check_cancel()
        value = str(url or "").strip()
        if not value:
            return None
        ffprobe = resolve_executable("ffprobe")
        if not ffprobe:
            return None
        headers = f"User-Agent: {USER_AGENT}\r\n"
        if referer:
            headers += f"Referer: {referer}\r\n"
        cmd = [
            ffprobe,
            "-v", "error",
            *cloudflare_ffmpeg_input_args(),
            "-headers", headers,
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            value,
        ]
        app_logger.debug(
            "NETWORK DNS | client=Analysis/FFprobe | provider=Cloudflare | proxy=enabled | url_host=%s",
            urlsplit(value).hostname or "",
        )
        proc = None
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, errors="replace", shell=False,
                **hidden_subprocess_kwargs(),
            )
            self._register_duration_probe_process(proc)
            started = time.monotonic()
            while True:
                self._check_cancel()
                remaining = 18.0 - (time.monotonic() - started)
                if remaining <= 0:
                    try:
                        proc.kill()
                        proc.communicate(timeout=2)
                    except Exception:
                        pass
                    return None
                try:
                    stdout, _stderr = proc.communicate(timeout=min(0.25, remaining))
                except subprocess.TimeoutExpired:
                    continue
                if proc.returncode != 0:
                    return None
                try:
                    duration = float(str(stdout or "").strip())
                except (TypeError, ValueError):
                    return None
                return duration if 0 < duration < 30 * 24 * 3600 else None
        except Cancelled:
            if proc is not None and proc.poll() is None:
                try:
                    proc.kill()
                    proc.communicate(timeout=2)
                except Exception:
                    pass
            raise
        except Exception:
            return None
        finally:
            if proc is not None and proc.poll() is None:
                try:
                    proc.kill()
                    proc.communicate(timeout=2)
                except Exception:
                    pass
            self._unregister_duration_probe_process(proc)
            close_subprocess_pipes(proc)

    def _populate_missing_track_durations(self, book: Book) -> int:
        tracks = list(getattr(book, "tracks", []) or [])
        if not tracks:
            return 0
        source_counts: dict[str, int] = {}
        for track in tracks:
            key = str(getattr(track, "file", "") or "")
            source_counts[key] = source_counts.get(key, 0) + 1
        candidates = [
            track for track in tracks
            if effective_track_duration(track) is None
            and getattr(track, "actual_duration", None) is None
            and source_counts.get(str(getattr(track, "file", "") or ""), 0) == 1
        ]
        if not candidates:
            return 0
        self._emit(f"Определяю длительность частей: 0/{len(candidates)}")
        futures = {}
        workers = min(6, len(candidates))
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="analysis-duration")
        try:
            for track in candidates:
                futures[pool.submit(self._probe_remote_duration, track.file, getattr(book, "url", ""))] = track
            discovered = 0
            processed = 0
            for future in _iter_completed_cancellable(futures, self.cancel_event):
                track = futures[future]
                processed += 1
                try:
                    duration = future.result()
                except Cancelled:
                    raise
                except Exception:
                    duration = None
                if duration is not None and duration > 0:
                    track.duration = float(duration)
                    discovered += 1
                self._emit(f"Определяю длительность частей: {processed}/{len(candidates)}")
            return discovered
        finally:
            for future in futures:
                future.cancel()
            # Always terminate any still-registered ffprobe child before
            # releasing the executor. This also covers exceptions that are not
            # signalled through cancel_event and avoids an 18-second wait.
            self._cancel_duration_probe_processes()
            pool.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _identity_tokens(value: str) -> set[str]:
        normalized = str(value or "").casefold().replace("ё", "е")
        return {token for token in re.findall(r"[\wІіЇїЄє]+", normalized, re.UNICODE) if len(token) > 1}

    @staticmethod
    def _book_identity_hints(book: Book) -> tuple[str, str, str]:
        raw_title = str(getattr(book, "title", "") or "").strip()
        author = str(getattr(book, "author", "") or "").strip()
        narrator = str(getattr(book, "narrator", "") or "").strip()
        title = raw_title
        parts = re.split(r"\s+[–—-]\s+", raw_title, maxsplit=1)
        if len(parts) == 2:
            prefix, suffix = (part.strip() for part in parts)
            if suffix and len(prefix.split()) <= 5:
                title = suffix
                if not author:
                    author = prefix
        return title, author, narrator

    def _knigavuhe_fallback_candidate(self, book: Book) -> Book | None:
        title_hint, author_hint, narrator_hint = self._book_identity_hints(book)
        title_tokens = self._identity_tokens(title_hint)
        author_tokens = self._identity_tokens(author_hint)
        narrator_tokens = self._identity_tokens(narrator_hint)
        if not title_tokens:
            return None
        try:
            results = list(search_knigavuhe_books(title_hint, cancel_event=self.cancel_event) or [])
        except Cancelled:
            raise
        except Exception:
            app_logger.debug("Analysis fallback search failed", exc_info=True)
            return None
        candidates: list[tuple[float, str]] = []
        for result in results:
            rt = self._identity_tokens(getattr(result, "title", ""))
            if not rt:
                continue
            title_overlap = len(title_tokens & rt) / max(1, len(title_tokens | rt))
            if title_overlap < 0.60 and not (title_tokens <= rt or rt <= title_tokens):
                continue
            score = 6.0 + 4.0 * title_overlap
            ra = self._identity_tokens(getattr(result, "author", ""))
            if author_tokens and ra:
                author_overlap = len(author_tokens & ra) / max(1, len(author_tokens | ra))
                if author_overlap < 0.50:
                    continue
                score += 4.0 * author_overlap
            variants = [(getattr(result, "url", ""), getattr(result, "narrator", ""))]
            variants.extend((getattr(v, "url", ""), getattr(v, "narrator", "")) for v in list(getattr(result, "narration_variants", []) or []))
            for candidate_url, candidate_narrator in variants:
                candidate_url = str(candidate_url or "").strip()
                if not candidate_url:
                    continue
                ns = self._identity_tokens(candidate_narrator)
                candidate_score = score
                if narrator_tokens and ns:
                    narrator_overlap = len(narrator_tokens & ns) / max(1, len(narrator_tokens | ns))
                    candidate_score += 5.0 * narrator_overlap if narrator_overlap >= 0.50 else -2.0
                candidates.append((candidate_score, candidate_url))
        seen: set[str] = set()
        unknown_narrator_choice = None
        unknown_narrator_identity = None
        for _score, candidate_url in sorted(candidates, reverse=True)[:8]:
            if candidate_url in seen:
                continue
            seen.add(candidate_url)
            self._check_cancel()
            try:
                fallback = fetch_knigavuhe_book(candidate_url, cancel_event=self.cancel_event)
            except Cancelled:
                raise
            except Exception:
                continue
            ft = self._identity_tokens(getattr(fallback, "title", ""))
            if not ft:
                continue
            overlap = len(title_tokens & ft) / max(1, len(title_tokens | ft))
            if overlap < 0.60 and not (title_tokens <= ft or ft <= title_tokens):
                continue
            fa = self._identity_tokens(getattr(fallback, "author", ""))
            if author_tokens and fa and len(author_tokens & fa) / max(1, len(author_tokens | fa)) < 0.50:
                continue
            fn = self._identity_tokens(getattr(fallback, "narrator", ""))
            if narrator_tokens:
                if not fn:
                    if unknown_narrator_choice is None:
                        unknown_narrator_choice = fallback
                    continue
                if len(narrator_tokens & fn) / max(1, len(narrator_tokens | fn)) < 0.40:
                    continue
                return fallback
            narrator_identity = " ".join(str(getattr(fallback, "narrator", "") or "").casefold().split())
            identity = narrator_identity or ("url:" + candidate_url)
            if unknown_narrator_choice is None:
                unknown_narrator_choice = fallback
                unknown_narrator_identity = identity
            elif identity != unknown_narrator_identity:
                app_logger.info("Analysis fallback is ambiguous because the source narrator is unknown")
                return None
        return unknown_narrator_choice

    def _recover_short_audioknigi_source(self, book: Book) -> Book:
        tracks = list(getattr(book, "tracks", []) or [])
        sources = list(dict.fromkeys(str(getattr(track, "file", "") or "").strip() for track in tracks if str(getattr(track, "file", "") or "").strip()))
        ends = [
            parsed
            for track in tracks
            if (parsed := parse_time_seconds(getattr(track, "end", None))) is not None
        ]
        if len(sources) != 1 or not ends:
            return book
        expected_end = max(ends)
        if expected_end <= 0:
            return book
        actual = self._probe_remote_duration(sources[0], str(getattr(book, "url", "") or ""))
        tolerance = max(15.0, expected_end * 0.001)
        if actual is None or actual + tolerance >= expected_end:
            return book
        self._emit(
            f"Источник audioknigi.com.ua короче плейлиста ({int(actual)} с вместо {int(expected_end)} с). Ищу резервный источник…"
        )
        app_logger.warning(
            "BOOK FLOW | event=analysis_shared_source_timeline_mismatch | expected_end=%.3f | actual_duration=%.3f",
            expected_end, actual,
        )
        fallback = self._knigavuhe_fallback_candidate(book)
        if fallback is None:
            raise RuntimeError(
                "Аудиофайл audioknigi.com.ua оказался неполным, а исправный резервный источник knigavuhe.org не найден."
            )
        self._populate_missing_track_durations(fallback)
        self._emit("Найден исправный резервный источник knigavuhe.org.")
        return fallback

    def analyze(self, url: str) -> Book:
        self._check_cancel()
        normalized = normalize_supported_url(str(url or "").strip())
        provider = source_key(normalized)
        if provider == "knigavuhe":
            self._emit("Анализирую knigavuhe.org…")
            book = fetch_knigavuhe_book(normalized, cancel_event=self.cancel_event)
            self._check_cancel()
            self._populate_missing_track_durations(book)
            self._check_cancel()
            if self.options.fetch_cover and getattr(book, "cover_url", "") and not normalize_cover_cache(getattr(book, "cover_cache", None)):
                book.cover_cache = normalize_cover_cache(self._fetch_cover_bytes(book.cover_url, book.url))
            self._check_cancel()
            self._emit(f"Найдено частей: {len(book.tracks)}")
            return book
        if provider == "poleknig":
            self._emit("Анализирую poleknig.com…")
            book = fetch_poleknig_book(normalized, cancel_event=self.cancel_event)
            self._check_cancel()
            self._populate_missing_track_durations(book)
            self._check_cancel()
            if self.options.fetch_cover and getattr(book, "cover_url", "") and not normalize_cover_cache(getattr(book, "cover_cache", None)):
                book.cover_cache = normalize_cover_cache(self._fetch_cover_bytes(book.cover_url, book.url))
            self._check_cancel()
            self._emit(f"Найдено частей: {len(book.tracks)}")
            return book
        if provider != "audioknigi":
            raise RuntimeError("Неподдерживаемый источник аудиокниги.")

        self._emit("Анализирую audioknigi.com.ua быстрым HTTP-способом…")
        primary_error = None
        try:
            book = self._analyze_audioknigi_requests(normalized)
        except Cancelled:
            raise
        except Exception as exc:
            response = getattr(exc, "response", None)
            if getattr(response, "status_code", None) in (404, 410):
                raise
            primary_error = exc
            app_logger.warning(
                "Qt/headless requests analysis failed; trying Playwright fallback",
                exc_info=True,
            )

        if primary_error is not None and not self.options.playwright_fallback_enabled:
            raise RuntimeError(
                "Не удалось получить данные книги быстрым способом, а резервный "
                f"браузерный анализ отключён. Причина: {primary_error}"
            )
        if primary_error is not None and sync_playwright is None:
            raise RuntimeError(
                "Не удалось получить плейлист обычным HTTP-запросом, а Playwright "
                f"недоступен. Причина: {primary_error}"
            )

        if primary_error is not None:
            self._emit("HTTP-анализ не сработал. Пробую Playwright fallback…")
            book = self._analyze_audioknigi_playwright(normalized, primary_error)
        self._check_cancel()
        book = self._recover_short_audioknigi_source(book)
        self._check_cancel()
        self._emit(f"Найдено частей: {len(book.tracks)}")
        return book

    @staticmethod
    def _looks_like_protection(html_text: str, status_code: int) -> bool:
        lowered = (html_text or "").lower()
        markers = ("cf-chl-", "cloudflare", "just a moment", "checking your browser", "attention required", "captcha")
        if status_code in (403, 429, 503):
            return any(marker in lowered for marker in markers)
        if status_code == 200:
            # A phrase such as "just a moment" can legitimately occur in a book
            # description. Treat structural challenge markers anywhere as strong,
            # but only accept that generic phrase when it is the page title.
            strong_markers = ("cf-chl-", "checking your browser", "attention required", "turnstile")
            if any(marker in lowered for marker in strong_markers):
                return True
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text or "", re.I | re.S)
            if title_match:
                title_text = html_lib.unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).casefold()
                return "just a moment" in title_text
            return False
        return False

    @staticmethod
    def _extract_page_title(html_text: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html_text or "", re.I | re.S)
        if not match:
            return ""
        value = re.sub(r"<[^>]+>", "", match.group(1))
        return html_lib.unescape(value).strip()

    @staticmethod
    def _extract_playlist_url(html_text: str) -> str | None:
        normalized = (html_text or "").replace("\\/", "/")
        match = re.search(r'(?:https?:)?//[^"\'\s<>]+\.pl\.txt(?:\?[^"\'\s<>]*)?', normalized, re.I)
        if match:
            raw = match.group(0)
            return "https:" + raw if raw.startswith("//") else raw
        relative = re.search(r'(?<![A-Za-z0-9])(/[^"\'\s<>]+\.pl\.txt(?:\?[^"\'\s<>]*)?)', normalized, re.I)
        return relative.group(1) if relative else None

    def _parse_playlist_data(
        self,
        *,
        url: str,
        html_text: str,
        page_title: str,
        playlist_url: str,
        playlist_text: str,
    ) -> Book:
        normalized_html = (html_text or "").replace("\\/", "/")
        title_match = re.search(
            r'new\s+Playerjs\s*\(\s*\{.*?title\s*:\s*["\']([^"\']+)["\']',
            normalized_html,
            re.I | re.S,
        )
        if title_match:
            title = html_lib.unescape(title_match.group(1).strip())
        else:
            title = page_title or self._extract_page_title(normalized_html)
            title = re.sub(r"\s+аудиокнига.*$", "", title, flags=re.I).strip()

        title, author, cover_url = extract_metadata_from_html(normalized_html, title)
        if cover_url:
            cover_url = urljoin(url, cover_url)
        description, narrator, genre, year = extract_extended_metadata_from_html(normalized_html)
        try:
            normalized_playlist_text = str(playlist_text or "").strip().lstrip("\ufeff").lstrip()
            data = json.loads(normalized_playlist_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Неизвестный формат плейлиста: {exc}") from exc
        if not isinstance(data, list) or not data:
            raise RuntimeError("Плейлист пуст.")

        playlist_items = [
            item for item in data
            if isinstance(item, dict) and str(item.get("file", "") or "").strip()
        ]
        tracks: list[Track] = []
        for item in playlist_items:
            self._check_cancel()
            file_url = urljoin(playlist_url, str(item.get("file", "")).strip())
            start = parse_time_seconds(item.get("start"))
            end = parse_time_seconds(item.get("end"))
            duration = None
            for key in ("duration", "length", "time"):
                duration = parse_time_seconds(item.get(key))
                if duration is not None:
                    break
            # Explicit start/end markers are the most precise chapter boundary.
            # Prefer them over a rounded integer duration when both are present.
            if start is not None and end is not None and end > start:
                duration = end - start
            track_index = len(tracks) + 1
            raw_track_title = html_lib.unescape(
                str(item.get("title") or "").strip()
            ).strip()
            normalized_track_title = _playlist_track_title(
                raw_track_title, file_url, track_index, title, len(playlist_items)
            )
            # Legacy fallback shape was: title=raw_track_title or f"{track_index:02d}".
            # The normalized title now additionally filters machine/file labels.
            tracks.append(
                Track(
                    index=track_index,
                    title=normalized_track_title or f"{track_index:02d}",
                    file=file_url,
                    start=start,
                    end=end,
                    duration=duration,
                    selected=True,
                )
            )
        if not tracks:
            raise RuntimeError("В плейлисте нет аудиофайлов.")

        unique_files = list(dict.fromkeys(track.file for track in tracks if track.file))
        remote_size = 0
        cover_cache = None
        pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="book-analysis-meta")
        futures = {}
        try:
            if self.options.fetch_remote_size and len(unique_files) == 1:
                futures[pool.submit(self._remote_size, unique_files[0], url)] = "size"
            if self.options.fetch_cover and cover_url:
                futures[pool.submit(self._fetch_cover_bytes, cover_url, url)] = "cover"
            for future in _iter_completed_cancellable(futures, self.cancel_event):
                self._check_cancel()
                kind = futures[future]
                try:
                    value = future.result()
                except Cancelled:
                    raise
                except Exception:
                    value = None
                if kind == "size" and value:
                    remote_size = int(value)
                elif kind == "cover" and value:
                    cover_cache = normalize_cover_cache(value)
        finally:
            for future in futures:
                future.cancel()
            pool.shutdown(wait=False, cancel_futures=True)

        return Book(
            url=url,
            title=title,
            author=author,
            narrator=narrator,
            description=description,
            genre=genre,
            year=year,
            cover_url=cover_url,
            cover_cache=cover_cache,
            playlist_url=playlist_url,
            tracks=tracks,
            remote_size=remote_size,
        )

    def _analyze_audioknigi_requests(self, url: str) -> Book:
        session = get_http_session()
        response = session.get(url, timeout=(10, 30), allow_redirects=True)
        content = bytes(getattr(response, "content", b"") or b"")
        html_text = content.decode("utf-8-sig", errors="replace") if content else (response.text or "")
        if self._looks_like_protection(html_text, response.status_code):
            raise RuntimeError(f"Сайт вернул защитную страницу HTTP {response.status_code}")
        response.raise_for_status()
        self._check_cancel()
        playlist_url = self._extract_playlist_url(html_text)
        if playlist_url:
            playlist_url = urljoin(url, playlist_url)
        if not playlist_url:
            raise SiteStructureChanged("В HTML страницы не найден адрес .pl.txt")
        playlist_response = session.get(playlist_url, headers={"Referer": url}, timeout=(10, 30))
        playlist_response.raise_for_status()
        return self._parse_playlist_data(
            url=url,
            html_text=html_text,
            page_title=self._extract_page_title(html_text),
            playlist_url=playlist_url,
            playlist_text=(
                playlist_response.content.decode("utf-8-sig", errors="replace")
                if getattr(playlist_response, "content", None) is not None
                else playlist_response.text
            ),
        )

    def _analyze_audioknigi_playwright(self, url: str, primary_error=None) -> Book:
        self._check_cancel()
        if sync_playwright is None:
            raise RuntimeError("Playwright не установлен. Установите зависимость playwright и повторите попытку.")
        with sync_playwright() as playwright:
            browser = launch_playwright_chromium(playwright.chromium)
            context = None
            html_text = ""
            page_title = ""
            playlist_url = ""
            playlist_response = None
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
                            app_logger.debug("Failed to restore audioknigi cookie into Playwright context", exc_info=True)
                page = context.new_page()
                captured: list[str] = []
                browser_request_headers: dict[str, str] = {}

                def on_request(request):
                    request_url = request.url.replace("\\/", "/")
                    if ".pl.txt" in request_url:
                        captured.append(request_url)
                    if request.resource_type == "document" and not browser_request_headers:
                        try:
                            browser_request_headers.update(request.all_headers())
                        except Exception:
                            pass

                page.on("request", on_request)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                # Player initialization can happen after DOMContentLoaded,
                # especially while Cloudflare/Turnstile finishes a managed
                # challenge. Poll the captured requests for up to eight seconds
                # instead of assuming a fixed 1.5-second delay is sufficient.
                for _attempt in range(32):
                    self._check_cancel()
                    if captured:
                        break
                    page.wait_for_timeout(250)
                self._check_cancel()
                html_text = page.content()
                playlist_url = captured[-1] if captured else self._extract_playlist_url(html_text)
                if playlist_url:
                    playlist_url = urljoin(url, playlist_url)
                if not playlist_url:
                    extra = f"; HTTP fast-path: {primary_error}" if primary_error else ""
                    raise SiteStructureChanged("Playwright также не нашёл плейлист" + extra)
                try:
                    browser_cookies = context.cookies()
                    if not browser_request_headers:
                        profile = page.evaluate(
                            """() => ({
                                'User-Agent': navigator.userAgent || '',
                                'Accept-Language': (navigator.languages || [navigator.language || '']).join(',')
                            })"""
                        )
                        if isinstance(profile, dict):
                            browser_request_headers.update(profile)
                    persist_browser_session(browser_cookies, browser_request_headers)
                except Exception:
                    app_logger.debug("Could not persist Playwright HTTP profile", exc_info=True)
                page_title = page.title()
            finally:
                if context is not None:
                    try:
                        context.close()
                    except Exception:
                        pass
                try:
                    browser.close()
                except Exception:
                    pass
        self._check_cancel()
        session = get_http_session()
        playlist_response = session.get(playlist_url, headers={"Referer": url}, timeout=(10, 30))
        playlist_response.raise_for_status()
        self._check_cancel()
        return self._parse_playlist_data(
            url=url,
            html_text=html_text,
            page_title=page_title,
            playlist_url=playlist_url,
            playlist_text=(
                playlist_response.content.decode("utf-8-sig", errors="replace")
                if getattr(playlist_response, "content", None) is not None
                else playlist_response.text
            ),
        )

    def _remote_size(self, url: str, referer: str) -> int:
        try:
            session = get_http_session()
            with session.get(
                url,
                headers={"Referer": referer, "Range": "bytes=0-0", "Accept-Encoding": "identity"},
                stream=True,
                timeout=(10, 20),
            ) as response:
                response.raise_for_status()
                match = re.search(r"/(\d+)$", response.headers.get("content-range", ""))
                if match:
                    return int(match.group(1))
                length = response.headers.get("content-length")
                if length and response.status_code == 200:
                    return int(length)
        except Exception:
            pass
        return 0

    def _fetch_cover_bytes(self, url: str, referer: str):
        return fetch_cover_bytes(url, referer, cancel_event=self.cancel_event)


def analyze_book(
    url: str,
    *,
    cancel_event: threading.Event | None = None,
    progress: ProgressCallback | None = None,
    options: AnalysisOptions | None = None,
) -> Book:
    return BookAnalysisService(cancel_event=cancel_event, progress=progress, options=options).analyze(url)


__all__ = ["AnalysisOptions", "BookAnalysisService", "analyze_book"]
