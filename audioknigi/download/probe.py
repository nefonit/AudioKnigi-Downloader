from __future__ import annotations

import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from urllib.parse import urlsplit
try:
    from mutagen.mp3 import MP3
except ImportError:
    MP3 = None
from ..models import normalize_track_status, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, TRACK_STATUS_DAMAGED
from ..templates import AUDIO_EXTENSIONS, render_folder, render_track_filename, track_number_width
from ..logging_utils import app_logger
from ..sources import normalize_supported_url, source_key
from ..network_dns import cloudflare_ffmpeg_input_args
from ..core import USER_AGENT, DEFAULT_OUTPUT, Cancelled, fmt_size, safe_name, resolve_executable, parse_time_seconds, effective_track_duration, hidden_subprocess_kwargs
from .common import close_subprocess_pipes as _close_subprocess_pipes

_DURATION_CACHE = {}
_DURATION_CACHE_LOCK = threading.Lock()
_DURATION_CACHE_MAX = 1024
_REMOTE_DURATION_CACHE = {}
_REMOTE_DURATION_CACHE_LOCK = threading.Lock()
_REMOTE_DURATION_CACHE_MAX = 2048

class ProbeMixin:
    """Probe subsystem for the downloader facade."""

    def _log_book_flow(self, event, book=None, *, level="info", **details):
        """Write a structured, privacy-sanitized lifecycle event to app.log only.

        The visible UI log intentionally stays concise.  Support diagnostics get
        stable ``BOOK FLOW`` records that describe every successful processing
        stage without exposing full URLs or the user's home path (the configured
        PrivacyFormatter sanitizes those values).
        """
        try:
            title = str(getattr(book, "title", "") or "") if book is not None else ""
            narrator = str(getattr(book, "narrator", "") or "") if book is not None else ""
            source_url = str(getattr(book, "url", "") or "") if book is not None else ""
            source = source_key(source_url) if source_url else ""
            total_tracks = len(list(getattr(book, "tracks", None) or [])) if book is not None else 0
            fields = [
                f"event={event}",
                f"title={title or '-'}",
                f"narrator={narrator or '-'}",
                f"source={source or '-'}",
                f"tracks={total_tracks}",
            ]
            for key, value in details.items():
                if value is None:
                    continue
                if isinstance(value, (list, tuple, set)):
                    value = ",".join(str(item) for item in value)
                fields.append(f"{key}={value}")
            message = "BOOK FLOW | " + " | ".join(fields)
            logger = getattr(app_logger, str(level or "info").lower(), app_logger.info)
            logger(message)
        except Exception:
            # Lifecycle logging must never affect a download.
            pass

    def _narration_folder_suffix(self, book):
        """Return a reader-aware suffix when one work has multiple recordings.

        Without this, downloading two narrations of the same title would reuse
        ``01.mp3``/``02.mp3`` in the same folder and could be mistaken for an
        already completed download. Custom folder templates stay fully under
        the user's control; this suffix applies only to the default layout.
        """
        variants = list(getattr(book, "narration_variants", None) or [])
        unique = []
        seen = set()
        for item in variants:
            url = normalize_supported_url(str(getattr(item, "url", "") or ""))
            if not url or url in seen:
                continue
            seen.add(url)
            unique.append(item)
        if len(unique) <= 1:
            return ""

        current_url = normalize_supported_url(str(getattr(book, "url", "") or ""))
        current_pos = 0
        current_item = None
        for pos, item in enumerate(unique, 1):
            url = normalize_supported_url(str(getattr(item, "url", "") or ""))
            if url == current_url or getattr(item, "current", False):
                current_item = item
                current_pos = pos
                if url == current_url:
                    break
        if current_item is None:
            current_item = unique[0]
            current_pos = 1

        narrator = str(getattr(current_item, "narrator", "") or getattr(book, "narrator", "") or "").strip()
        if not narrator:
            return f"Озвучка {current_pos}"

        same_reader = []
        narrator_key = narrator.casefold().replace("ё", "е")
        for item in unique:
            value = str(getattr(item, "narrator", "") or "").strip()
            if value.casefold().replace("ё", "е") == narrator_key:
                same_reader.append(item)
        if len(same_reader) > 1:
            reader_pos = 0
            for pos, item in enumerate(same_reader, 1):
                if item is current_item or normalize_supported_url(str(getattr(item, "url", "") or "")) == current_url:
                    reader_pos = pos
                    break
            narrator = f"{narrator} - вариант {reader_pos or 1}"
        return narrator

    def _book_folder(self, book, *, create=True):
        if bool(getattr(self, "runtime_use_templates", False)):
            return render_folder(
                getattr(self, "runtime_output_dir", DEFAULT_OUTPUT),
                getattr(self, "runtime_folder_template", "{Book_Title}"),
                book,
                create=create,
                language=getattr(self, "runtime_language", "ru"),
            )
        base = Path(getattr(self, "runtime_output_dir", DEFAULT_OUTPUT)).expanduser()
        folder_name = safe_name(book.title or "audiobook")
        variant_suffix = self._narration_folder_suffix(book)
        if variant_suffix:
            folder_name = f"{folder_name} [{safe_name(variant_suffix)}]"
        folder = base / folder_name
        if create:
            folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _track_filename(self, book, track, mode=None):
        if bool(getattr(self, "runtime_use_templates", False)):
            return render_track_filename(
                getattr(self, "runtime_track_template", "{Track_Number}.mp3"),
                book,
                track,
                ext=".mp3",
                language=getattr(self, "runtime_language", "ru"),
            )
        mode = mode or getattr(self, "runtime_naming_mode", "number") or "number"
        width = track_number_width(book)
        number = f"{int(track.index):0{width}d}"
        raw_title = str(track.title or number).strip()
        lowered_title = raw_title.casefold()
        for candidate in sorted(AUDIO_EXTENSIONS, key=len, reverse=True):
            if lowered_title.endswith(candidate):
                raw_title = raw_title[:-len(candidate)]
                break
        part_title = safe_name(raw_title) or number
        book_title = safe_name(book.title or "audiobook")
        if mode == "number_title":
            return f"{number} - {part_title}.mp3"
        if mode == "book_number":
            return f"{book_title} - {number}.mp3"
        return f"{number}.mp3"

    def _track_path(self, book, track, mode=None, *, create_folder=True):
        return self._book_folder(book, create=create_folder) / self._track_filename(book, track, mode)

    def _run_ffprobe_duration_command(self, cmd, timeout):
        """Run ffprobe cooperatively and parse a numeric duration result."""
        stdout = self._run_ffprobe_text_command(cmd, timeout)
        if stdout is None or not str(stdout).strip():
            return None
        try:
            return float(str(stdout).strip())
        except (TypeError, ValueError):
            return None

    def _run_ffprobe_text_command(self, cmd, timeout):
        """Run ffprobe cooperatively and return stdout, including an empty success result."""
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            errors="replace",
            shell=False,
            **hidden_subprocess_kwargs(),
        )
        self._register_active_subprocess(proc)
        started = time.monotonic()
        try:
            while True:
                cancel_event = getattr(self, "cancel_event", None)
                if cancel_event is not None and cancel_event.is_set():
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    try:
                        proc.communicate(timeout=3)
                    except Exception:
                        pass
                    raise Cancelled("Операция отменена пользователем.")
                remaining = float(timeout) - (time.monotonic() - started)
                if remaining <= 0:
                    try:
                        proc.kill()
                        proc.communicate(timeout=3)
                    except Exception:
                        pass
                    return None
                try:
                    stdout, _stderr = proc.communicate(timeout=min(0.25, remaining))
                    if proc.returncode == 0:
                        return str(stdout or "")
                    return None
                except subprocess.TimeoutExpired:
                    continue
        finally:
            if proc.poll() is None:
                try:
                    proc.kill()
                    proc.communicate(timeout=3)
                except Exception:
                    pass
            self._unregister_active_subprocess(proc)
            _close_subprocess_pipes(proc)

    def _local_audio_has_packets_near(self, file_path, timestamp, *, window=8.0):
        """Confirm real audio packets near ``timestamp`` instead of trusting MP3 headers.

        Truncated VBR/Xing MP3 files can retain the original duration in their
        metadata even though the media frames end much earlier.  ffprobe packet
        scanning near the final playlist coordinate catches that condition.
        ``None`` means the probe itself was unavailable; ``False`` means the
        probe succeeded but no packet reached the requested area.
        """
        path = Path(file_path)
        if not path.exists() or path.stat().st_size <= 0:
            return False
        ffprobe = resolve_executable("ffprobe")
        if not ffprobe:
            return None
        start = max(0.0, float(timestamp))
        span = max(1.0, float(window))
        cmd = [
            ffprobe,
            "-v", "error",
            "-select_streams", "a:0",
            "-read_intervals", f"{start:.3f}%+{span:.3f}",
            "-show_entries", "packet=pts_time,dts_time",
            "-of", "csv=p=0",
            str(path),
        ]
        try:
            stdout = self._run_ffprobe_text_command(cmd, timeout=12)
        except Cancelled:
            raise
        except Exception:
            return None
        if stdout is None:
            return None
        packet_times = []
        for raw in str(stdout).replace("\r", "\n").splitlines():
            raw = raw.strip().strip(',')
            if not raw:
                continue
            values = [part.strip() for part in raw.split(',')]
            parsed = None
            for candidate in values[:2]:
                try:
                    parsed = float(candidate)
                    break
                except (TypeError, ValueError):
                    continue
            if parsed is not None:
                packet_times.append(parsed)
        if not packet_times:
            return False
        # MP3 seeking can land slightly before the requested timestamp.  Allow
        # a small seek slop while still requiring packets close to the target.
        return max(packet_times) >= max(0.0, start - 2.0)

    def _probe_duration(self, file_path):
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()
            resolved_path = file_path.resolve()
        except OSError:
            return None

        if stat.st_size <= 0:
            return None

        key = (str(resolved_path), int(stat.st_size), int(stat.st_mtime_ns))

        with _DURATION_CACHE_LOCK:
            cached = _DURATION_CACHE.get(key)
        if cached is not None:
            return cached

        duration = None
        # Cheap in-process metadata first; FFprobe is the fallback.
        if MP3 is not None:
            try:
                duration = float(MP3(str(file_path)).info.length)
            except Exception:
                duration = None

        ffprobe = resolve_executable("ffprobe")
        if duration is None and ffprobe:
            try:
                duration = self._run_ffprobe_duration_command(
                    [
                        ffprobe,
                        "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(file_path),
                    ],
                    timeout=30,
                )
            except Cancelled:
                raise
            except Exception:
                duration = None

        if duration is not None:
            with _DURATION_CACHE_LOCK:
                if len(_DURATION_CACHE) >= _DURATION_CACHE_MAX:
                    # Simple bounded cache: remove the oldest inserted key.
                    try:
                        _DURATION_CACHE.pop(next(iter(_DURATION_CACHE)))
                    except Exception:
                        _DURATION_CACHE.clear()
                _DURATION_CACHE[key] = duration

        return duration

    def _probe_remote_duration(self, url, referer=""):
        """Ask ffprobe for a direct audio URL duration without downloading it.

        This is a best-effort analysis enhancement.  A failure never blocks the
        book: after download/local scan the UI can still use ``actual_duration``.
        """
        url = str(url or "").strip()
        if not url:
            return None

        with _REMOTE_DURATION_CACHE_LOCK:
            cached = _REMOTE_DURATION_CACHE.get(url)
        if cached is not None:
            return cached

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
            url,
        ]
        app_logger.debug(
            "NETWORK DNS | client=FFprobe | provider=Cloudflare | proxy=enabled | url_host=%s",
            urlsplit(url).hostname or "",
        )
        try:
            duration = self._run_ffprobe_duration_command(cmd, timeout=18)
            if duration is None or not (0 < duration < 30 * 24 * 3600):
                return None
        except Cancelled:
            raise
        except Exception:
            return None

        with _REMOTE_DURATION_CACHE_LOCK:
            if len(_REMOTE_DURATION_CACHE) >= _REMOTE_DURATION_CACHE_MAX:
                try:
                    _REMOTE_DURATION_CACHE.pop(next(iter(_REMOTE_DURATION_CACHE)))
                except Exception:
                    _REMOTE_DURATION_CACHE.clear()
            _REMOTE_DURATION_CACHE[url] = duration
        return duration

    def _populate_missing_track_durations(self, book):
        """Fill missing duration metadata for one-file-per-track playlists.

        Source ``start``/``end`` values are never synthesized here because they
        are trimming coordinates used by FFmpeg.  Only ``duration`` is filled,
        and only when a URL belongs to exactly one track, so a shared source
        cannot accidentally be treated as a full chapter multiple times.
        """
        tracks = list(getattr(book, "tracks", []) or [])
        if not tracks:
            return 0

        counts = {}
        for track in tracks:
            key = str(getattr(track, "file", "") or "")
            counts[key] = counts.get(key, 0) + 1

        candidates = [
            track for track in tracks
            if effective_track_duration(track) is None
            and getattr(track, "actual_duration", None) is None
            and counts.get(str(getattr(track, "file", "") or ""), 0) == 1
        ]
        if not candidates:
            return 0

        discovered = 0
        workers = min(6, len(candidates))
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="probe-duration")
        futures = {}
        try:
            futures = {
                pool.submit(self._probe_remote_duration, track.file, getattr(book, "url", "")): track
                for track in candidates
            }
            pending = set(futures)
            while pending:
                self._check_cancel()
                done, pending = wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)
                for future in done:
                    self._check_cancel()
                    track = futures[future]
                    try:
                        duration = future.result()
                    except Cancelled:
                        raise
                    except Exception:
                        duration = None
                    if duration is not None and duration > 0:
                        track.duration = float(duration)
                        discovered += 1
        finally:
            for future in futures:
                future.cancel()
            cancel_event = getattr(self, "cancel_event", None)
            if cancel_event is not None and cancel_event.is_set():
                cancel_active = getattr(self, "_cancel_active_subprocesses", None)
                if callable(cancel_active):
                    cancel_active()
            pool.shutdown(wait=True, cancel_futures=True)

        if discovered:
            self.log(f"Определена длительность частей: {discovered}/{len(candidates)}")
        return discovered

    def _verify_track_file(self, book, track, *, create_folder=True):
        path = self._track_path(book, track, create_folder=create_folder)

        if not path.exists() or path.stat().st_size <= 0:
            return TRACK_STATUS_MISSING, None, path

        expected = effective_track_duration(track)
        actual = self._probe_duration(path)

        if expected is None or actual is None:
            # We can at least confirm a non-empty file, but not duration.
            return TRACK_STATUS_PRESENT, actual, path

        # Public playlist metadata and the decoded MP3 stream can differ by a
        # few seconds (rounding, encoder delay/padding, VBR duration metadata).
        # Two seconds proved too strict for long chapter files and caused valid
        # downloads to be marked as damaged and rebuilt.  Keep the tolerance
        # small enough to catch a wrong/mismatched source while accepting normal
        # metadata drift.
        # Playlist durations are frequently rounded and MP3/VBR metadata adds
        # encoder delay. Scale the tolerance for long chapters, while capping it
        # tightly enough that a genuinely wrong source still fails validation.
        tolerance = max(5.0, min(15.0, float(expected) * 0.015))

        if abs(float(actual) - float(expected)) <= tolerance:
            return TRACK_STATUS_READY, actual, path

        return TRACK_STATUS_DAMAGED, actual, path

    def _scan_book_files(self, book, *, create_folder=True):
        ready = 0
        damaged = 0
        existing = 0

        for track in book.tracks:
            status, actual, path = self._verify_track_file(book, track, create_folder=create_folder)
            track.local_status = status
            track.actual_duration = actual
            track.local_path = str(path)

            if status == TRACK_STATUS_READY:
                ready += 1
                existing += 1
            elif status == TRACK_STATUS_PRESENT:
                existing += 1
            elif status == TRACK_STATUS_DAMAGED:
                damaged += 1

        return {
            "ready": ready,
            "existing": existing,
            "damaged": damaged,
            "total": len(book.tracks),
        }

    def _estimate_required_space(self, book, selected_indices=None):
        """Approximate peak extra disk use for source + selected output formats."""
        tracks = book.tracks
        if selected_indices is None:
            chosen = tracks
        else:
            wanted = set(int(x) for x in selected_indices)
            chosen = [t for t in tracks if t.index in wanted]

        want_mp3 = True
        remote_size = int(book.remote_size or 0)
        total_duration = sum(float(effective_track_duration(t) or 0) for t in tracks)
        missing = [t for t in chosen if normalize_track_status(t.local_status) not in (TRACK_STATUS_READY, TRACK_STATUS_PRESENT)]
        missing_duration = sum(float(effective_track_duration(t) or 0) for t in missing)

        folder = self._book_folder(book, create=False)
        need_source = bool(missing)
        source_remaining = 0
        if need_source and remote_size > 0:
            source_urls = list(dict.fromkeys(
                str(getattr(track, "file", "") or "")
                for track in missing
                if str(getattr(track, "file", "") or "")
            ))
            assignments = self._source_target_assignments(book, source_urls, folder)
            locally_present = 0
            all_complete = bool(assignments)
            for _slot, _url, source_target in assignments:
                source_target = Path(source_target)
                part_target = source_target.with_name(source_target.name + ".part")
                try:
                    if source_target.is_file() and source_target.stat().st_size > 0:
                        locally_present += int(source_target.stat().st_size)
                        continue
                    all_complete = False
                    if part_target.is_file() and part_target.stat().st_size > 0:
                        locally_present += int(part_target.stat().st_size)
                except OSError:
                    all_complete = False
            source_remaining = 0 if all_complete else max(0, remote_size - locally_present)

        outputs = 0
        preset = str(getattr(self, "runtime_audio_preset", "copy") or "copy")
        bitrate_map = {"64k_mono": 64_000, "96k_mono": 96_000, "128k_stereo": 128_000}
        fallback_bitrate = 128_000
        estimated_missing_bytes = int(missing_duration * fallback_bitrate / 8) if missing_duration > 0 else 0
        if need_source and remote_size <= 0 and estimated_missing_bytes > 0:
            source_remaining = estimated_missing_bytes

        if want_mp3:
            if preset in bitrate_map:
                outputs += int(missing_duration * bitrate_map[preset] / 8)
            elif remote_size > 0 and total_duration > 0:
                outputs += int(remote_size * (missing_duration / total_duration))
            elif estimated_missing_bytes > 0:
                outputs += estimated_missing_bytes

        # Safety margin for metadata, filesystem overhead and temporary muxing.
        return int((source_remaining + outputs) * 1.12)

    def _disk_free_for_path(self, target):
        """Return free bytes for target or its nearest existing parent.

        The final book directory may not exist yet.  Calling disk_usage() on a
        missing path raises FileNotFoundError on Windows; walking up to the
        nearest existing parent prevents that from silently bypassing the
        preflight space check.
        """
        try:
            path = Path(target).expanduser()
        except (TypeError, ValueError, OSError):
            return None

        try:
            while not path.exists() and path.parent != path:
                path = path.parent
            if not path.exists():
                return None
            return int(shutil.disk_usage(path).free)
        except Exception:
            return None

    def _disk_space_info(self, book, selected_indices=None):
        folder = self._book_folder(book, create=False)
        required = self._estimate_required_space(book, selected_indices)
        free = self._disk_free_for_path(folder)
        return required, free

    def _report_download_error(self, message):
        """GUI-neutral error hook used by preflight checks.

        Desktop frontends override this when they want a modal dialog.  Keeping
        the downloader core free of Tk/Qt imports lets the same engine run from
        Qt workers, tests and future CLI integrations.
        """
        self.log(str(message or ""))

    def _check_disk_space(self, book, selected_indices=None, show_warning=True):
        required, free = self._disk_space_info(book, selected_indices)

        if required > 0 and free is None:
            if show_warning:
                play_sound = getattr(self, "_play_event_sound", None)
                if callable(play_sound):
                    play_sound("error")
                self._report_download_error(
                    "Не удалось определить свободное место на диске.\n\n"
                    "Проверьте папку сохранения и доступ к диску, затем повторите загрузку."
                )
            return False

        if required > 0 and int(free or 0) < required:
            if show_warning:
                play_sound = getattr(self, "_play_event_sound", None)
                if callable(play_sound):
                    play_sound("error")
                self._report_download_error(
                    "Недостаточно свободного места.\n\n"
                    f"Нужно примерно: {fmt_size(required)}\n"
                    f"Свободно: {fmt_size(free)}"
                )
            return False

        return True

    @staticmethod
    def _identity_tokens(value):
        text = str(value or "").casefold().replace("ё", "е")
        return tuple(re.findall(r"[0-9a-zа-я]+", text, re.I))

    def _book_identity_hints(self, book):
        raw_title = str(getattr(book, "title", "") or "").strip()
        author = str(getattr(book, "author", "") or "").strip()
        narrator = str(getattr(book, "narrator", "") or "").strip()
        title = raw_title
        if " - " in raw_title:
            prefix, suffix = raw_title.split(" - ", 1)
            if suffix.strip() and len(prefix.split()) <= 5:
                title = suffix.strip()
                if not author:
                    author = prefix.strip()
        return title, author, narrator

    def _shared_source_timeline_issue(self, book, local_map=None):
        """Return details when a shared audio source ends before playlist cuts.

        ``audioknigi.com.ua`` sometimes serves one physical MP3 with chapter
        ``start``/``end`` coordinates.  A stale redirect can point to a shorter
        recording while the playlist itself still contains correct chapter
        boundaries.  Detect that before FFmpeg creates truncated chapters.
        """
        groups = {}
        for track in list(getattr(book, "tracks", []) or []):
            source = str(getattr(track, "file", "") or "").strip()
            if not source:
                continue
            groups.setdefault(source, []).append(track)

        for source, tracks in groups.items():
            if len(tracks) < 2:
                continue
            ends = [
                parse_time_seconds(getattr(track, "end", None))
                for track in tracks
            ]
            ends = [float(value) for value in ends if value is not None and float(value) > 0]
            if not ends:
                continue
            expected_end = max(ends)
            actual = None
            local_path = None
            if local_map is not None:
                path = local_map.get(source)
                if path is not None and Path(path).exists():
                    local_path = Path(path)
                    actual = self._probe_duration(local_path)
            else:
                actual = self._probe_remote_duration(source, getattr(book, "url", ""))
            tolerance = max(15.0, expected_end * 0.001)
            if actual is not None and actual > 0 and float(actual) + tolerance < expected_end:
                return {
                    "source": source,
                    "expected_end": expected_end,
                    "actual_duration": float(actual),
                    "track_indices": [int(getattr(track, "index", 0) or 0) for track in tracks],
                    "reason": "duration_short",
                }

            # A truncated VBR/Xing MP3 may still advertise the *original* full
            # duration.  For a downloaded/reused shared source, verify that real
            # audio packets exist close to the final playlist coordinate.
            if local_path is not None:
                probe_start = max(0.0, expected_end - tolerance)
                has_packets = self._local_audio_has_packets_near(
                    local_path, probe_start, window=max(6.0, tolerance)
                )
                if has_packets is False:
                    return {
                        "source": source,
                        "expected_end": expected_end,
                        "actual_duration": float(actual or 0.0),
                        "track_indices": [int(getattr(track, "index", 0) or 0) for track in tracks],
                        "reason": "no_packets_near_expected_end",
                        "probe_start": probe_start,
                    }
            elif actual is None or actual <= 0:
                app_logger.info(
                    "BOOK FLOW | event=shared_source_remote_validation_unavailable | "
                    "source=audioknigi | expected_end=%.3f | url_host=%s",
                    expected_end, urlsplit(source).hostname or "",
                )
        return None


__all__ = ["ProbeMixin"]
