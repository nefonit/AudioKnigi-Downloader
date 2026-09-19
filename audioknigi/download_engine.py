from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import json
import os
import shutil
import threading
import time
import weakref

from .core import (
    Cancelled,
    DEFAULT_OUTPUT,
    HISTORY_FILE,
    effective_track_duration,
    load_json,
    fmt_size,
    safe_float,
    safe_int,
    safe_name,
    safe_normalization_mode,
    resolve_executable,
    save_json,
)
from .downloader import DownloaderMixin
from .logging_utils import app_logger
from .i18n import tr as i18n_tr
from .models import Book, Track
from .sources import normalize_supported_url
from .services.download_request import DownloadRequest
from .services.library_service import HISTORY_LOCK
from .config.settings import normalize_settings
from .download.common import replace_with_retry, unlink_with_retry

try:
    from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
except ImportError:  # pragma: no cover - mutagen is a normal runtime dependency
    APIC = ID3 = TALB = TIT2 = TPE1 = None


StatusCallback = Callable[[str], None]
StageCallback = Callable[[int, str], None]
ProgressCallback = Callable[[float], None]
LogCallback = Callable[[str], None]
TransferCallback = Callable[[float, int], None]
MissingMediaCallback = Callable[[list[int], str, bool], str]
HistoryCallback = Callable[[], None]
RequestChangedCallback = Callable[[DownloadRequest], None]


@dataclass(slots=True)
class DownloadCallbacks:
    status: StatusCallback | None = None
    stage: StageCallback | None = None
    progress: ProgressCallback | None = None
    log: LogCallback | None = None
    transfer: TransferCallback | None = None
    missing_media: MissingMediaCallback | None = None
    history_changed: HistoryCallback | None = None
    request_changed: RequestChangedCallback | None = None


@dataclass(slots=True)
class DownloadResult:
    folder: Path
    selected_indices: list[int]
    skipped_indices: list[int]
    target_file: Path | None = None
    book: Book | None = None


@dataclass(frozen=True, slots=True)
class DuplicatePreflight:
    exact_duplicate: bool
    folder: Path
    evidence: str = ""



class _DownloadEngine(DownloaderMixin):
    """Headless adapter around the mature downloader core.

    All UI communication is exposed through callbacks.  The class deliberately
    does not inherit Tk mixins and never creates widgets, so it can run inside a
    Qt QThread, regular Python worker thread, tests, or a future CLI.
    """

    def __init__(
        self,
        request: DownloadRequest,
        settings: Mapping[str, object] | None,
        cancel_event: threading.Event,
        callbacks: DownloadCallbacks | None,
    ) -> None:
        self.request = request
        self.settings = normalize_settings(settings)
        self.cancel_event = cancel_event
        self.callbacks = callbacks or DownloadCallbacks()
        self._active_subprocesses = weakref.WeakSet()
        self._active_subprocess_lock = threading.RLock()
        self._active_network_responses = set()
        self._active_network_lock = threading.RLock()
        self._bandwidth_limiter = None
        self._history_lock = HISTORY_LOCK
        self._last_process_skipped_indices: list[int] = []
        self._apply_runtime_options()

    def _apply_runtime_options(self) -> None:
        data = self.settings
        req = self.request

        output_dir = str(req.output_dir or data.get("output_dir") or DEFAULT_OUTPUT)
        self.runtime_output_dir = output_dir
        self.runtime_delete_source = bool(data.get("delete_source", True))
        self.runtime_embed_tags = bool(data.get("embed_tags", True))
        self.runtime_naming_mode = str(req.naming_mode or data.get("naming_mode", "number") or "number")
        self.runtime_segment_count = str(data.get("segment_count", "auto") or "auto")
        self.runtime_segment_threshold_mb = max(1, safe_int(data.get("segment_threshold_mb", 16), 16))
        self.runtime_auto_chunk_min_kbytes_per_sec = max(1, safe_int(data.get("auto_chunk_min_kbytes_per_sec", 256), 256))
        # Temporary runtime alias for extension compatibility; remove after one major release.
        self.runtime_auto_chunk_min_kbps = self.runtime_auto_chunk_min_kbytes_per_sec
        self.runtime_bandwidth_limit = max(0.0, safe_float(data.get("bandwidth_limit", 0.0), 0.0))
        self.runtime_output_mode = "mp3"
        self.runtime_audio_preset = str(req.audio_preset or data.get("audio_preset", "copy") or "copy")
        self.runtime_normalization_mode = safe_normalization_mode(
            req.normalization_mode or data.get("normalization_mode", "off"), "off"
        )
        self.runtime_normalize_audio = self.runtime_normalization_mode != "off"
        self.runtime_parallel_single_source = bool(data.get("parallel_single_source", False))
        self.runtime_save_sidecars = bool(data.get("save_sidecars", True))
        self.runtime_use_templates = bool(
            data.get("use_templates", False) if req.use_templates is None else req.use_templates
        )
        self.runtime_folder_template = str(req.folder_template or data.get("folder_template") or "{Book_Title}")
        self.runtime_track_template = str(req.track_template or data.get("track_template") or "{Track_Number}.mp3")
        self.runtime_abs_enabled = bool(data.get("abs_enabled", False))
        self.runtime_abs_url = str(data.get("abs_url", "") or "").strip()
        self.runtime_abs_api_key = str(data.get("abs_api_key", "") or "").strip()
        self.runtime_abs_library_id = str(data.get("abs_library_id", "") or "").strip()
        self.runtime_playwright_fallback_enabled = bool(data.get("playwright_fallback_enabled", True))
        self.runtime_language = str(data.get("language", "ru") or "ru")

    def _check_cancel(self):
        if self.cancel_event.is_set():
            # Interrupt blocking I/O too; the lower-level helpers also poll the
            # event, but closing active responses/processes makes cancellation
            # much more responsive on slow or stalled servers.
            try:
                self._cancel_active_network_io()
            except Exception:
                pass
            try:
                self._cancel_active_subprocesses()
            except Exception:
                pass
            raise Cancelled("Операция отменена пользователем.")

    def ui(self, func):
        # The headless engine has no UI thread.  Core code only uses this hook
        # for optional refresh callbacks that are absent here.
        try:
            func()
        except Exception:
            app_logger.debug("Headless UI callback failed", exc_info=True)

    def log(self, text):
        message = str(text or "")
        app_logger.info(message)
        cb = self.callbacks.log
        if cb is not None:
            cb(message)

    def set_status(self, text):
        cb = self.callbacks.status
        if cb is not None:
            cb(str(text or ""))

    def set_stage(self, number, text):
        cb = self.callbacks.stage
        if cb is not None:
            cb(max(0, min(5, int(number))), str(text or ""))

    def set_progress(self, value):
        cb = self.callbacks.progress
        if cb is not None:
            cb(max(0.0, min(100.0, float(value or 0.0))))

    def record_transfer_metrics(self, speed_bytes_per_sec, active_segments=1):
        cb = self.callbacks.transfer
        if cb is not None:
            cb(max(0.0, float(speed_bytes_per_sec or 0.0)), max(0, int(active_segments or 0)))

    def _report_download_error(self, message):
        # Worker-safe equivalent of the Tk modal hook.  Fatal preflight errors
        # are still raised by _process_book_once and become Qt dialogs there.
        self.log(str(message or ""))

    def _ask_missing_media_action(self, track_indices, *, detail="", allow_skip=True):
        indices = sorted({int(x) for x in (track_indices or [])})
        cb = self.callbacks.missing_media
        if cb is None:
            return "stop"
        decision = str(cb(indices, str(detail or ""), bool(allow_skip)) or "stop").lower()
        return decision if decision in {"skip", "stop"} else "stop"

    def _resume_manifest_path(self, book, *, create=True):
        return self._book_folder(book, create=create) / "resume.json"

    def _write_resume_manifest(self, book, selected_indices, *, download_mode="parts"):
        manifest = {
            "url": book.url,
            "title": book.title,
            "selected_indices": list(selected_indices or []),
            "download_mode": "full_mp3" if str(download_mode) == "full_mp3" else "parts",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "naming_mode": self.runtime_naming_mode,
            "audio_preset": self.runtime_audio_preset,
            "normalization_mode": self.runtime_normalization_mode,
            "normalize_audio": bool(self.runtime_normalize_audio),
            "use_templates": bool(self.runtime_use_templates),
            "folder_template": self.runtime_folder_template,
            "track_template": self.runtime_track_template,
        }
        path = self._resume_manifest_path(book)
        if not save_json(path, manifest):
            app_logger.error("Could not write resume manifest: %s", path)
            raise OSError(f"Не удалось сохранить файл восстановления: {path}")

    def _remove_resume_manifest(self, book):
        try:
            path = self._resume_manifest_path(book, create=False)
            if path.exists():
                path.unlink()
        except Exception:
            app_logger.debug("Could not remove resume manifest", exc_info=True)

    @staticmethod
    def _book_field(book, name, default=""):
        if isinstance(book, Mapping):
            try:
                value = book.get(name, default)
                return default if value is None else value
            except Exception:
                return default
        try:
            value = getattr(book, name)
            return default if value is None else value
        except (AttributeError, TypeError):
            return default

    def _add_history(self, book, folder, parts):
        folder_text = str(folder or "").strip()
        cover_file = ""
        if folder_text:
            folder_path = Path(folder_text)
            for name in ("cover.jpg", "cover.jpeg", "cover.png", "cover.webp"):
                candidate = folder_path / name
                if candidate.is_file():
                    cover_file = str(candidate)
                    break

        entry = {
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "title": self._book_field(book, "title"),
            "author": self._book_field(book, "author"),
            "narrator": self._book_field(book, "narrator"),
            "genre": self._book_field(book, "genre"),
            "year": self._book_field(book, "year"),
            "description": self._book_field(book, "description"),
            "cover_url": self._book_field(book, "cover_url"),
            "cover_file": cover_file,
            "parts": max(0, safe_int(parts, 0)),
            "folder": folder_text,
            "url": self._book_field(book, "url"),
        }

        with HISTORY_LOCK:
            history = load_json(HISTORY_FILE, [])
            if not isinstance(history, list):
                history = []
            history = [x for x in history if isinstance(x, dict)]
            entry_url = normalize_supported_url(str(entry.get("url", "") or ""))
            entry_folder = os.path.normcase(os.path.abspath(str(entry.get("folder", "") or "")))
            history = [
                x for x in history
                if not (
                    normalize_supported_url(str(x.get("url", "") or "")) == entry_url
                    and os.path.normcase(os.path.abspath(str(x.get("folder", "") or ""))) == entry_folder
                )
            ]
            history.insert(0, entry)
            history_saved = bool(save_json(HISTORY_FILE, history[:500]))

        if not history_saved:
            app_logger.warning(
                "BOOK FLOW | event=history_save_failed | title=%s | folder=%s",
                entry.get("title") or "-",
                entry.get("folder") or "-",
            )
            return

        app_logger.info(
            "BOOK FLOW | event=history_saved | title=%s | narrator=%s | parts=%s | folder=%s",
            entry.get("title") or "-",
            entry.get("narrator") or "-",
            entry.get("parts", 0),
            entry.get("folder") or "-",
        )
        cb = self.callbacks.history_changed
        if cb is not None:
            self.ui(cb)

    @staticmethod
    def _duplicate_text(value) -> str:
        return " ".join(str(value or "").split()).strip()

    @staticmethod
    def _duplicate_float_equal(left, right, tolerance=0.05) -> bool:
        if left in (None, "") and right in (None, ""):
            return True
        try:
            return abs(float(left) - float(right)) <= float(tolerance)
        except (TypeError, ValueError):
            return False

    def _history_metadata_matches_book(self, book, folder: Path, *, expected_parts: int | None = None) -> bool:
        wanted_url = normalize_supported_url(str(self._book_field(book, "url", "") or ""))
        # Volatile presentation metadata (description/cover URL/genre text) may
        # change without changing the actual audiobook. Identity is anchored by
        # normalized source URL, folder, part count and stable bibliographic fields.
        fields = ("title", "author", "narrator")
        history = load_json(HISTORY_FILE, [])
        for record in history if isinstance(history, list) else []:
            if not isinstance(record, dict):
                continue
            if normalize_supported_url(str(record.get("url", "") or "")) != wanted_url:
                continue
            record_folder = os.path.normcase(os.path.abspath(str(record.get("folder", "") or "")))
            current_folder = os.path.normcase(os.path.abspath(str(folder)))
            if record_folder != current_folder:
                continue
            wanted_parts = len(list(self._book_field(book, "tracks", []) or [])) if expected_parts is None else max(0, int(expected_parts))
            if safe_int(record.get("parts", 0), 0) != wanted_parts:
                continue
            if all(self._duplicate_text(record.get(name, "")) == self._duplicate_text(self._book_field(book, name, "")) for name in fields):
                return True
        return False

    def _sidecar_metadata_matches_book(self, book, folder: Path):
        path = Path(folder) / "metadata.json"
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        if normalize_supported_url(str(payload.get("source_url", "") or "")) != normalize_supported_url(str(self._book_field(book, "url", "") or "")):
            return False
        for name in ("title", "author", "narrator"):
            if self._duplicate_text(payload.get(name, "")) != self._duplicate_text(self._book_field(book, name, "")):
                return False
        stored_tracks = list(payload.get("tracks", []) or [])
        current_tracks = list(self._book_field(book, "tracks", []) or [])
        if len(stored_tracks) != len(current_tracks):
            return False
        by_index = {}
        for row in stored_tracks:
            if not isinstance(row, dict):
                return False
            try:
                by_index[int(row.get("index"))] = row
            except (TypeError, ValueError):
                return False
        for track in current_tracks:
            try:
                track_index = self.request.track_index(self._book_field(track, "index", -1))
            except (TypeError, ValueError):
                return False
            row = by_index.get(track_index)
            if row is None:
                return False
            expected_title = str(self._book_field(track, "title", "") or "").strip() or f"Часть {track_index:02d}"
            if self._duplicate_text(row.get("title", "")) != self._duplicate_text(expected_title):
                return False
            if not self._duplicate_float_equal(row.get("start"), self._book_field(track, "start", None)):
                return False
            if not self._duplicate_float_equal(row.get("end"), self._book_field(track, "end", None)):
                return False
            stored_duration = row.get("duration")
            current_duration = effective_track_duration(track)
            if stored_duration not in (None, "") and current_duration not in (None, ""):
                if not self._duplicate_float_equal(stored_duration, current_duration, tolerance=5.0):
                    return False
        return True

    def _full_mp3_target(self, book: Book, folder: Path) -> Path:
        """Return the one-file output path used by run/preflight/delete alike."""
        folder = Path(folder)
        if bool(getattr(self, "runtime_use_templates", False)):
            # The default per-track template is intentionally just a track
            # number.  Reusing it for a whole-book file would produce the
            # surprising name ``01.mp3``.  Keep custom track templates working,
            # but give the one-file mode a book-shaped default filename.
            track_template = str(getattr(self, "runtime_track_template", "{Track_Number}.mp3") or "{Track_Number}.mp3").strip()
            normalized_track_template = track_template
            if normalized_track_template.casefold().endswith(".mp3"):
                normalized_track_template = normalized_track_template[:-4].rstrip(" .")
            if normalized_track_template == "{Track_Number}":
                title_name = safe_name(str(getattr(book, "title", "") or "audiobook"))
                return folder / f"{title_name}.mp3"
            synthetic = Track(
                index=1,
                title=str(getattr(book, "title", "") or "audiobook"),
                file="",
            )
            return folder / self._track_filename(book, synthetic)
        title_name = safe_name(str(getattr(book, "title", "") or "audiobook"))
        return folder / f"{title_name}.mp3"

    @staticmethod
    def _retained_source_suffix(source_url: str, probe_info) -> str:
        suffix = Path(urlsplit(str(source_url or ""))).suffix.lower()
        supported = {".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wav"}
        if suffix in supported:
            return suffix
        info = dict(probe_info or {})
        codec = str(info.get("codec") or "").strip().lower()
        fmt = str(info.get("format_name") or "").strip().lower()
        if any(name in fmt.split(",") for name in ("mov", "mp4", "m4a", "3gp", "3g2", "mj2")):
            return ".m4a"
        return {
            "mp3": ".mp3", "aac": ".aac", "flac": ".flac",
            "opus": ".opus", "vorbis": ".ogg", "wav": ".wav",
        }.get(codec, ".audio")

    @staticmethod
    def _retained_full_source_path(
        folder: Path, title_name: str, source_suffix: str, target: Path
    ) -> Path:
        """Return a visible source-copy path that never aliases the final output."""
        folder = Path(folder)
        target = Path(target)
        candidate = folder / f"{title_name} (исходник){source_suffix}"
        if candidate != target:
            return candidate
        # A custom whole-book template can itself resolve to the normal retained
        # source name. Preserve both the processed output and the original source.
        return folder / f"{title_name} (исходник, оригинал){source_suffix}"

    def duplicate_preflight(self, *, full_mp3: bool = False, probe_durations: bool = True) -> DuplicatePreflight:
        book = self.request.book
        folder = Path(self._book_folder(book, create=False))
        tracks = list(getattr(book, "tracks", []) or [])
        try:
            all_indices = {self.request.track_index(track) for track in tracks}
        except ValueError:
            return DuplicatePreflight(False, folder, "invalid-track-index")
        selected = set(self.request.resolved_selected_indices())
        if not tracks or selected != all_indices:
            return DuplicatePreflight(False, folder, "partial-selection")
        if full_mp3:
            target = self._full_mp3_target(book, folder)
            if not target.is_file() or target.stat().st_size <= 0:
                return DuplicatePreflight(False, folder, "full-mp3-missing")
            sidecar = self._sidecar_metadata_matches_book(book, folder)
            evidence = "metadata.json" if sidecar is not None else "history.json"
            matched = bool(sidecar if sidecar is not None else self._history_metadata_matches_book(book, folder, expected_parts=1))
            return DuplicatePreflight(matched, folder, evidence)
        if probe_durations:
            scan = self._scan_book_files(book, create_folder=False)
        else:
            total = len(tracks)
            existing = 0
            for track in tracks:
                try:
                    path = Path(self._track_path(book, track, create_folder=False))
                    if path.is_file() and path.stat().st_size > 0:
                        existing += 1
                except OSError:
                    pass
            scan = {"ready": 0, "existing": existing, "damaged": 0, "total": total}
        # Exact duplicate means every expected track was positively validated,
        # not merely that a non-empty file happened to exist at each path.
        strictly_ready = scan.get("ready", 0) == scan.get("total", 0)
        all_existing = scan.get("existing", 0) == scan.get("total", 0)
        complete = bool(
            scan.get("total", 0) > 0
            and scan.get("damaged", 0) == 0
            and (strictly_ready if probe_durations else all_existing)
        )
        if not complete:
            return DuplicatePreflight(False, folder, "files-incomplete")
        sidecar = self._sidecar_metadata_matches_book(book, folder)
        evidence = "metadata.json" if sidecar is not None else "history.json"
        matched = bool(sidecar if sidecar is not None else self._history_metadata_matches_book(book, folder))
        return DuplicatePreflight(matched, folder, evidence)

    def delete_existing_outputs(self, *, full_mp3: bool = False) -> int:
        count = 0
        if full_mp3:
            folder = Path(self._book_folder(self.request.book, create=False))
            target = self._full_mp3_target(self.request.book, folder)
            try:
                if target.exists():
                    unlink_with_retry(target, missing_ok=True)
                    count += 1
            except Exception:
                app_logger.debug("Could not delete existing full MP3 before redownload", exc_info=True)
            return count
        selected = set(self.request.resolved_selected_indices())
        for track in list(getattr(self.request.book, "tracks", []) or []):
            if self.request.track_index(track) not in selected:
                continue
            try:
                path = Path(self._track_path(self.request.book, track, create_folder=False))
                if path.exists():
                    unlink_with_retry(path, missing_ok=True)
                    count += 1
            except Exception:
                app_logger.debug("Could not delete existing track before redownload", exc_info=True)
        return count

    def run_full_mp3(self) -> DownloadResult:
        """Download a one-source book as a real MP3 with refresh/recovery support."""
        self.request.validate()
        self._check_cancel()
        book = self.request.book

        def shared_source_urls() -> tuple[str, str]:
            urls: list[str] = []
            fallback_urls: list[str] = []
            for track in list(getattr(book, "tracks", None) or []):
                url = str(getattr(track, "file", "") or "").strip()
                fallback = str(getattr(track, "fallback_file", "") or "").strip()
                if url and url not in urls:
                    urls.append(url)
                if fallback and fallback not in fallback_urls:
                    fallback_urls.append(fallback)
            if not urls:
                raise ValueError("У книги нет доступных аудиофайлов.")
            if len(urls) > 1:
                raise ValueError("У книги несколько исходных файлов. Используйте скачивание по частям.")
            # A one-file book can have one alternate CDN/media mirror.  If
            # metadata contains conflicting alternates, keep recovery
            # conservative and fall back to the normal page refresh instead.
            fallback_url = fallback_urls[0] if len(fallback_urls) == 1 else ""
            return urls[0], fallback_url

        source_url, fallback_url = shared_source_urls()
        full_indices = [self.request.track_index(track) for track in list(getattr(book, "tracks", None) or [])]
        self._write_resume_manifest(book, full_indices, download_mode="full_mp3")
        folder = Path(self._book_folder(book))
        title_name = safe_name(str(getattr(book, "title", "") or "audiobook"))
        target = self._full_mp3_target(book, folder)
        source_target = folder / f".{title_name}.full-source"
        required = max(0, safe_int(getattr(book, "remote_size", 0), 0))
        free = self._disk_free_for_path(folder)
        definite_transcode = bool(
            str(getattr(self, "runtime_audio_preset", "copy") or "copy") != "copy"
            or str(getattr(self, "runtime_normalization_mode", "off") or "off") != "off"
        )
        retains_source_copy = not bool(getattr(self, "runtime_delete_source", True))
        peak_required = required * 2 if required and (definite_transcode or retains_source_copy) else required
        if required and free is None:
            raise RuntimeError("Не удалось определить свободное место на диске. Проверьте папку сохранения и доступ к диску.")
        if peak_required and int(free or 0) < peak_required:
            raise RuntimeError(f"Недостаточно места. Нужно ~{fmt_size(peak_required)}, свободно {fmt_size(free)}.")

        self.set_stage(2, i18n_tr(self.runtime_language, "stage_full_mp3_download"))
        self.set_status("Скачиваю исходный аудиофайл книги…")
        self.set_progress(0)
        refreshed = False
        while True:
            try:
                self._download_source_with_fallback(
                    source_url,
                    fallback_url,
                    source_target,
                    str(getattr(book, "url", "") or ""),
                )
                break
            except Cancelled:
                raise
            except Exception as exc:
                if refreshed or not self._is_expired_media_error(exc):
                    raise
                refreshed = True
                self.log("Ссылка полного аудиофайла устарела. Обновляю страницу и плейлист один раз…")
                self._cleanup_partial_download(source_target)
                selected = [self.request.track_index(track) for track in list(getattr(book, "tracks", None) or [])]
                self._refresh_book_media_playlist(book, selected)
                source_url, fallback_url = shared_source_urls()
                title_name = safe_name(str(getattr(book, "title", "") or "audiobook"))
                target = self._full_mp3_target(book, folder)
                source_target = folder / f".{title_name}.full-source"
                req = getattr(self, "request", None)
                callback = getattr(getattr(self, "callbacks", None), "request_changed", None)
                if req is not None:
                    req.book = book
                    if callback is not None:
                        try:
                            callback(req)
                        except Exception:
                            app_logger.debug("Request-change callback failed", exc_info=True)

        self._check_cancel()
        self.set_stage(3, i18n_tr(self.runtime_language, "stage_full_mp3_processing"))
        info = self._cached_probe_audio_info(source_target)
        codec = str(info.get("codec") or "").strip().lower()
        copy_mode, bitrate, channels = self._effective_mp3_profile(source_target)
        try:
            unlink_with_retry(target, missing_ok=True)
        except OSError:
            pass
        if copy_mode:
            if self.runtime_delete_source:
                replace_with_retry(source_target, target)
            else:
                shutil.copy2(source_target, target)
                source_suffix = self._retained_source_suffix(source_url, info)
                retained = self._retained_full_source_path(folder, title_name, source_suffix, target)
                try:
                    unlink_with_retry(retained, missing_ok=True)
                except OSError:
                    pass
                replace_with_retry(source_target, retained)
        else:
            detected = codec or "не определён"
            self.log(
                f"Обрабатываю полный файл (исходный кодек: {detected}) с выбранным "
                "профилем качества и нормализацией."
            )
            ffmpeg = resolve_executable("ffmpeg")
            if ffmpeg is None:
                raise RuntimeError("FFmpeg не найден. Он необходим для обработки полного файла MP3.")

            # At this point the source is already on disk, so verify that there is
            # enough room for the second output file before starting a long encode.
            try:
                source_bytes = max(0, int(source_target.stat().st_size))
            except OSError:
                source_bytes = required
            estimated_output = source_bytes
            source_bps = max(0, safe_int(info.get("bit_rate"), 0))
            if bitrate and source_bps > 0:
                try:
                    target_bps = int(str(bitrate).rstrip("kK")) * 1000
                    estimated_output = max(1, int(source_bytes * target_bps / source_bps))
                except (TypeError, ValueError):
                    pass
            free_after_download = self._disk_free_for_path(folder)
            needed_output = int(max(estimated_output, 8 * 1024 * 1024) * 1.12)
            if free_after_download is not None and int(free_after_download) < needed_output:
                raise RuntimeError(
                    f"Недостаточно места для обработки полного MP3. Нужно ещё ~{fmt_size(needed_output)}, "
                    f"свободно {fmt_size(free_after_download)}."
                )

            normalization_filter = self._normalization_filter_for_track(source_target, None, None)
            cmd = [
                ffmpeg, "-hide_banner", "-nostdin", "-y",
                "-i", str(source_target), "-map", "0:a:0",
            ]
            if normalization_filter:
                cmd += ["-af", normalization_filter]
            cmd += ["-c:a", "libmp3lame"]
            if bitrate:
                cmd += ["-b:a", str(bitrate)]
            else:
                cmd += ["-q:a", "4"]
            if channels:
                cmd += ["-ac", str(channels)]
            cmd += [str(target)]
            self._run_ffmpeg(cmd)
            if self.runtime_delete_source:
                try:
                    source_target.unlink(missing_ok=True)
                except Exception:
                    pass
            else:
                # A retained source must be visible and playable.  Do not leave
                # a hidden extensionless ``.full-source`` file behind.
                source_suffix = self._retained_source_suffix(source_url, info)
                retained = self._retained_full_source_path(folder, title_name, source_suffix, target)
                if retained != target:
                    try:
                        unlink_with_retry(retained, missing_ok=True)
                    except OSError:
                        pass
                    replace_with_retry(source_target, retained)

        self._check_cancel()
        self.set_stage(4, i18n_tr(self.runtime_language, "stage_full_mp3_tags"))
        if self.runtime_embed_tags and ID3 is not None:
            try:
                try:
                    tags = ID3(target)
                except Exception:
                    tags = ID3()
                title = str(getattr(book, "title", "") or "audiobook")
                tags.delall("TIT2")
                tags.delall("TPE1")
                tags.delall("TALB")
                tags.add(TIT2(encoding=3, text=title))
                tags.add(TALB(encoding=3, text=title))
                author = str(getattr(book, "author", "") or "").strip()
                if author and TPE1 is not None:
                    tags.add(TPE1(encoding=3, text=author))
                cover = self._cover_bytes(book)
                if cover and APIC is not None:
                    data, mime = cover
                    tags.delall("APIC")
                    tags.add(APIC(encoding=3, mime=mime or "image/jpeg", type=3, desc="Cover", data=data))
                tags.save(str(target))
            except Exception as exc:
                self.log(f"Не удалось записать ID3 в полный MP3: {exc}")

        self._save_book_sidecars(book, folder, list(getattr(book, "tracks", None) or []))
        self._scan_audiobookshelf_after_book()
        self._add_history(book, folder, 1)
        self._remove_resume_manifest(book)
        self.set_progress(100)
        self.set_stage(5, i18n_tr(self.runtime_language, "status_done"))
        self.set_status("Полный MP3 готов.")
        return DownloadResult(
            folder=folder,
            selected_indices=self.request.resolved_selected_indices(),
            skipped_indices=[],
            target_file=target,
            book=self.request.book,
        )

    def run(self) -> DownloadResult:
        self.request.validate()
        self._check_cancel()
        folder = Path(
            self._process_book(
                self.request.book,
                selected_indices=self.request.selected_indices,
                status_callback=self.set_status,
            )
        )
        skipped_indices = list(getattr(self, "_last_process_skipped_indices", []) or [])
        skipped = {int(index) for index in skipped_indices}
        downloaded_indices = [
            int(index)
            for index in self.request.resolved_selected_indices()
            if int(index) not in skipped
        ]
        return DownloadResult(
            folder=folder,
            selected_indices=downloaded_indices,
            skipped_indices=skipped_indices,
            book=self.request.book,
        )


class DownloadService:
    """Public GUI-neutral façade for one book download."""

    def __init__(
        self,
        *,
        settings: Mapping[str, object] | None = None,
        cancel_event: threading.Event | None = None,
        callbacks: DownloadCallbacks | None = None,
    ) -> None:
        self.settings = normalize_settings(settings)
        self.cancel_event = cancel_event or threading.Event()
        self.callbacks = callbacks or DownloadCallbacks()

    def download(self, request: DownloadRequest) -> DownloadResult:
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.run()

    def download_full_mp3(self, request: DownloadRequest) -> DownloadResult:
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.run_full_mp3()

    def duplicate_preflight(
        self, request: DownloadRequest, *, full_mp3: bool = False, probe_durations: bool = True
    ) -> DuplicatePreflight:
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.duplicate_preflight(full_mp3=full_mp3, probe_durations=probe_durations)

    def delete_existing_outputs(self, request: DownloadRequest, *, full_mp3: bool = False) -> int:
        engine = _DownloadEngine(request, self.settings, self.cancel_event, self.callbacks)
        return engine.delete_existing_outputs(full_mp3=full_mp3)


__all__ = [
    "DownloadCallbacks",
    "DownloadResult",
    "DuplicatePreflight",
    "DownloadService",
]
