from __future__ import annotations

import json
import math
import re
import subprocess
import threading
import time
from collections.abc import Mapping
from pathlib import Path
try:
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TRCK
except ImportError:
    ID3 = APIC = TIT2 = TPE1 = TALB = TRCK = None
from ..models import normalize_cover_cache
from ..templates import track_number_width
from ..integrations import audiobookshelf_scan
from ..logging_utils import app_logger
from ..core import Cancelled, fmt_time, safe_int, safe_normalization_mode, resolve_executable, effective_track_duration, parse_time_seconds, hidden_subprocess_kwargs, save_json
from .common import atomic_write_bytes, atomic_write_text, close_subprocess_pipes as _close_subprocess_pipes

_AUDIO_INFO_CACHE_INIT_LOCK = threading.Lock()
_AUDIO_INFO_CACHE_MAX = 32

class MediaProcessingMixin:
    """Media subsystem for the downloader facade."""

    @staticmethod
    def _format_ffmpeg_command(cmd):
        """Format argv for diagnostics without changing how the process is run."""
        try:
            return subprocess.list2cmdline([str(part) for part in cmd])
        except Exception:
            return " ".join(str(part) for part in cmd)

    def _log_ffmpeg_failure(self, cmd, returncode, stderr):
        """Write complete FFmpeg diagnostics to app.log without flooding the UI log."""
        command_text = self._format_ffmpeg_command(cmd)
        stderr_text = str(stderr or "").rstrip()
        if not stderr_text:
            stderr_text = "(FFmpeg не передал текст stderr.)"
        try:
            app_logger.error(
                "FFmpeg failure | returncode=%s\nCommand: %s\nStderr:\n%s",
                returncode, command_text, stderr_text,
            )
        except Exception:
            pass

    def _run_ffmpeg(self, cmd, timeout=7200):
        """Run FFmpeg safely, preserve cancellation, and keep complete failure diagnostics."""
        self._check_cancel()
        started = time.monotonic()
        try:
            app_logger.info("FFmpeg command: %s", self._format_ffmpeg_command(cmd))
        except Exception:
            pass

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            shell=False,
            **hidden_subprocess_kwargs(),
        )
        self._register_active_subprocess(proc)
        stderr = ""
        try:
            while True:
                self._check_cancel()
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    proc.kill()
                    try:
                        _out, stderr = proc.communicate(timeout=5)
                    except Exception:
                        pass
                    self._log_ffmpeg_failure(cmd, proc.returncode, stderr)
                    raise RuntimeError(f"FFmpeg превысил лимит времени {timeout} секунд.")

                try:
                    _out, stderr = proc.communicate(timeout=min(0.25, remaining))
                    break
                except subprocess.TimeoutExpired:
                    cancel_event = getattr(self, "cancel_event", None)
                    if cancel_event is not None and cancel_event.is_set():
                        proc.kill()
                        try:
                            proc.communicate(timeout=5)
                        except Exception:
                            pass
                        raise Cancelled("Операция отменена пользователем.")

            if proc.returncode != 0:
                self._log_ffmpeg_failure(cmd, proc.returncode, stderr)
                detail = (stderr or "").strip()
                if not detail:
                    detail = f"FFmpeg не передал stderr (код возврата {proc.returncode}). Подробности сохранены в app.log."
                else:
                    detail = detail[-4000:]
                raise RuntimeError("FFmpeg завершился с ошибкой:\n" + detail)
            app_logger.debug(
                "FFmpeg success | returncode=0 | elapsed=%.3fs | command=%s",
                time.monotonic() - started, self._format_ffmpeg_command(cmd),
            )
        finally:
            if proc.poll() is None:
                try:
                    proc.kill()
                    proc.communicate(timeout=5)
                except Exception:
                    pass
            self._unregister_active_subprocess(proc)

    def _run_ffmpeg_capture(self, cmd, timeout=14400):
        """Run FFmpeg safely and return stderr while keeping cancel support."""
        self._check_cancel()
        started = time.monotonic()
        try:
            app_logger.info("FFmpeg command: %s", self._format_ffmpeg_command(cmd))
        except Exception:
            pass
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            shell=False,
            **hidden_subprocess_kwargs(),
        )
        self._register_active_subprocess(proc)
        stderr = ""
        try:
            while True:
                self._check_cancel()
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    proc.kill()
                    try:
                        _out, stderr = proc.communicate(timeout=5)
                    except Exception:
                        pass
                    self._log_ffmpeg_failure(cmd, proc.returncode, stderr)
                    raise RuntimeError(f"FFmpeg превысил лимит времени {timeout} секунд.")
                try:
                    _out, stderr = proc.communicate(timeout=min(0.25, remaining))
                    break
                except subprocess.TimeoutExpired:
                    cancel_event = getattr(self, "cancel_event", None)
                    if cancel_event is not None and cancel_event.is_set():
                        proc.kill()
                        try:
                            proc.communicate(timeout=5)
                        except Exception:
                            pass
                        raise Cancelled("Операция отменена пользователем.")

            if proc.returncode != 0:
                self._log_ffmpeg_failure(cmd, proc.returncode, stderr)
                detail = (stderr or "").strip()
                if not detail:
                    detail = f"FFmpeg не передал stderr (код возврата {proc.returncode}). Подробности сохранены в app.log."
                else:
                    detail = detail[-4000:]
                raise RuntimeError("FFmpeg завершился с ошибкой:\n" + detail)
            app_logger.debug(
                "FFmpeg success | returncode=0 | elapsed=%.3fs | command=%s",
                time.monotonic() - started, self._format_ffmpeg_command(cmd),
            )
            return stderr or ""
        finally:
            if proc.poll() is None:
                try:
                    proc.kill()
                    proc.communicate(timeout=5)
                except Exception:
                    pass
            self._unregister_active_subprocess(proc)

    def _probe_audio_info(self, file_path):
        ffprobe = resolve_executable("ffprobe")
        if not ffprobe:
            return {}
        proc = None
        try:
            proc = subprocess.Popen(
                [
                    ffprobe, "-v", "error", "-select_streams", "a:0",
                    "-show_entries", "stream=codec_name,bit_rate,sample_rate,channels:format=bit_rate,format_name",
                    "-of", "json", str(file_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                errors="replace",
                shell=False,
                **hidden_subprocess_kwargs(),
            )
            self._register_active_subprocess(proc)
            started = time.monotonic()
            while True:
                self._check_cancel()
                remaining = 30.0 - (time.monotonic() - started)
                if remaining <= 0:
                    proc.kill()
                    try:
                        proc.communicate(timeout=3)
                    except Exception:
                        pass
                    return {}
                try:
                    stdout, _stderr = proc.communicate(timeout=min(0.25, remaining))
                    break
                except subprocess.TimeoutExpired:
                    continue
            if proc.returncode != 0:
                return {}
            data = json.loads(stdout or "{}")
            streams = data.get("streams") if isinstance(data, dict) else None
            stream = streams[0] if isinstance(streams, list) and streams and isinstance(streams[0], dict) else {}

            def as_int(value):
                try:
                    return int(value)
                except Exception:
                    return 0
            format_info = data.get("format") if isinstance(data, dict) else None
            if not isinstance(format_info, dict):
                format_info = {}
            return {
                "codec": str(stream.get("codec_name") or ""),
                "bit_rate": as_int(stream.get("bit_rate")) or as_int(format_info.get("bit_rate")),
                "sample_rate": as_int(stream.get("sample_rate")),
                "channels": as_int(stream.get("channels")),
                "format_name": str(format_info.get("format_name") or ""),
            }
        except Cancelled:
            if proc is not None and proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
            raise
        except Exception:
            return {}
        finally:
            if proc is not None and proc.poll() is None:
                try:
                    proc.kill()
                    proc.communicate(timeout=3)
                except Exception:
                    pass
            if proc is not None:
                self._unregister_active_subprocess(proc)
                _close_subprocess_pipes(proc)

    def _cached_probe_audio_info(self, file_path):
        path = Path(file_path)

        lock = getattr(self, "_audio_info_lock", None)
        if lock is None:
            # DownloaderMixin can be embedded outside _DownloadEngine, so create
            # the per-instance lock lazily without racing two split workers.
            with _AUDIO_INFO_CACHE_INIT_LOCK:
                lock = getattr(self, "_audio_info_lock", None)
                if lock is None:
                    lock = threading.RLock()
                    self._audio_info_lock = lock

        while True:
            try:
                stat = path.stat()
                key = (str(path.resolve()), int(stat.st_size), int(stat.st_mtime_ns))
            except Exception:
                key = (str(path), 0, 0)

            with lock:
                cache = getattr(self, "_audio_info_cache", None)
                if cache is None:
                    cache = {}
                    self._audio_info_cache = cache
                cached = cache.get(key)
                if cached is not None:
                    return dict(cached)
                inflight = getattr(self, "_audio_info_inflight", None)
                if inflight is None:
                    inflight = {}
                    self._audio_info_inflight = inflight
                ready = inflight.get(key)
                owner = ready is None
                if owner:
                    ready = threading.Event()
                    inflight[key] = ready

            if owner:
                break

            # Wait only for another probe of the same source. Different source
            # files are free to probe concurrently because the shared cache lock
            # is not held while ffprobe runs.
            while not ready.wait(0.10):
                checker = getattr(self, "_check_cancel", None)
                if callable(checker):
                    checker()
            with lock:
                cached = getattr(self, "_audio_info_cache", {}).get(key)
            if cached is not None:
                return dict(cached)
            # The owner failed before publishing. Re-evaluate and compete for
            # ownership again without recursive stack growth.

        try:
            probed = dict(self._probe_audio_info(path) or {})
            with lock:
                cache = getattr(self, "_audio_info_cache", None)
                if cache is None:
                    cache = {}
                    self._audio_info_cache = cache
                for stale_key in [item for item in cache if item[0] == key[0] and item != key]:
                    cache.pop(stale_key, None)
                while len(cache) >= _AUDIO_INFO_CACHE_MAX:
                    oldest_key = next(iter(cache), None)
                    if oldest_key is None:
                        break
                    cache.pop(oldest_key, None)
                cache[key] = probed
            return dict(probed)
        finally:
            with lock:
                inflight = getattr(self, "_audio_info_inflight", {})
                event = inflight.pop(key, None)
                if event is not None:
                    event.set()

    @staticmethod
    def _preset_target(preset):
        return {
            "64k_mono": (64_000, 1),
            "96k_mono": (96_000, 1),
            "128k_stereo": (128_000, 2),
        }.get(str(preset or ""), (0, 0))

    def _effective_mp3_profile(self, source_path):
        preset = str(getattr(self, "runtime_audio_preset", "copy") or "copy")
        normalization = str(getattr(self, "runtime_normalization_mode", "off") or "off")
        info = self._cached_probe_audio_info(source_path)
        source_bps = int(info.get("bit_rate") or 0)
        source_channels = int(info.get("channels") or 0)
        target_bps, target_channels = self._preset_target(preset)

        if preset == "copy" and normalization == "off":
            if str(info.get("codec") or "").strip().lower() == "mp3":
                return True, None, None
            detected = str(info.get("codec") or "").strip() or "не определён"
            self.log(
                f"Оригинальный поток имеет кодек {detected}; для MP3 выполняю совместимое "
                "перекодирование вместо stream-copy."
            )
        if (
            normalization == "off" and target_bps and str(info.get("codec") or "").strip().lower() == "mp3"
            and source_bps and source_bps <= target_bps
            and source_channels and source_channels <= target_channels
        ):
            self.log(
                f"Smart Format: источник {source_bps//1000}k/{source_channels}ch уже не хуже выбранного "
                f"профиля {target_bps//1000}k/{target_channels}ch — использую copy."
            )
            return True, None, None

        if not target_bps:
            target_bps = source_bps or 96_000
        elif source_bps:
            target_bps = min(target_bps, source_bps)
        target_bps = max(48_000, target_bps)
        if not target_channels:
            target_channels = min(2, source_channels or 2)
        elif source_channels:
            target_channels = min(target_channels, source_channels)
        return False, f"{max(48, int(round(target_bps/1000)))}k", max(1, target_channels)

    def _measure_loudnorm(self, source_path, start=None, duration=None, filter_complex=None, map_label=None, extra_inputs=None):
        """First loudnorm pass; returns the measured second-pass filter string."""
        ffmpeg = resolve_executable("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("FFmpeg не найден. Установите FFmpeg или добавьте его в PATH.")
        base = "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json"
        if filter_complex:
            if not str(map_label or "").strip():
                raise ValueError("filter_complex требует явный map_label для измерения loudnorm")
            cmd = [ffmpeg, "-hide_banner", "-nostdin", "-nostats", "-y", "-i", str(source_path)]
            for path in (extra_inputs or []):
                cmd += ["-i", str(path)]
            input_label = str(map_label).strip()
            input_label = f"[{input_label.strip('[]')}]"
            output_label = "[audioknigi_loudnorm_measure]"
            clean_graph = str(filter_complex).strip().rstrip(";").rstrip()
            analysis_graph = f"{clean_graph};{input_label}{base}{output_label}"
            cmd += ["-filter_complex", analysis_graph, "-map", output_label, "-f", "null", "-"]
        else:
            cmd = [ffmpeg, "-hide_banner", "-nostdin", "-nostats", "-y"]
            if start is not None:
                cmd += ["-ss", str(start)]
            cmd += ["-i", str(source_path)]
            if duration is not None:
                cmd += ["-t", str(duration)]
            cmd += ["-map", "0:a:0", "-af", base, "-f", "null", "-"]
        stderr = self._run_ffmpeg_capture(cmd, timeout=14400)
        stats = None
        decoder = json.JSONDecoder()
        # loudnorm prints its JSON summary at the end of stderr.  Restrict the
        # structural scan to a bounded tail and walk braces backwards; this
        # avoids repeatedly slicing a multi-megabyte diagnostic stream when
        # metadata or decoder messages contain many ``{`` characters.
        # Decoder warnings can be extremely noisy on damaged long inputs.
        # Keep a larger bounded window so the final loudnorm JSON is not pushed
        # out by >128 KiB of warnings emitted around filter teardown.
        loudnorm_tail = str(stderr or "")[-524_288:]
        search_end = len(loudnorm_tail)
        for _attempt in range(64):
            brace = loudnorm_tail.rfind("{", 0, search_end)
            if brace < 0:
                break
            try:
                candidate, _end = decoder.raw_decode(loudnorm_tail[brace:])
            except (json.JSONDecodeError, TypeError):
                search_end = brace
                continue
            if isinstance(candidate, dict) and "input_i" in candidate:
                stats = candidate
                break
            search_end = brace
        if stats is None:
            raise RuntimeError("FFmpeg loudnorm не вернул статистику первого прохода.")
        required = ("input_i", "input_lra", "input_tp", "input_thresh", "target_offset")
        if any(key not in stats for key in required):
            self.log(
                "FFmpeg вернул неполную статистику loudnorm первого прохода; "
                "использую безопасную однопроходную нормализацию."
            )
            return base
        try:
            finite = all(math.isfinite(float(stats[key])) for key in required)
        except (TypeError, ValueError, OverflowError):
            finite = False
        if not finite:
            app_logger.info(
                "FFmpeg loudnorm returned non-finite first-pass statistics; "
                "falling back to single-pass normalization."
            )
            return base
        return (
            "loudnorm=I=-16:LRA=11:TP=-1.5:"
            f"measured_I={stats['input_i']}:measured_LRA={stats['input_lra']}:"
            f"measured_TP={stats['input_tp']}:measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}:linear=true:print_format=summary"
        )

    def _normalization_filter_for_track(self, source_path, start, duration):
        mode = safe_normalization_mode(getattr(self, "runtime_normalization_mode", "off"), "off")
        if mode == "two_pass":
            self.set_status("Качественная нормализация: анализ громкости…")
            return self._measure_loudnorm(source_path, start=start, duration=duration)
        if mode == "single":
            return "loudnorm=I=-16:LRA=11:TP=-1.5"
        return ""

    def _cover_bytes(self, book):
        cached = normalize_cover_cache(book.cover_cache)
        if cached:
            book.cover_cache = cached
            return cached

        url = book.cover_url
        if not url:
            return None

        value = normalize_cover_cache(self._fetch_cover_bytes(url, book.url))
        if value:
            book.cover_cache = value
        return value

    def _write_id3(self, file_path, book, track_index, total_tracks, cover, track=None):
        if not bool(getattr(self, "runtime_embed_tags", False)) or ID3 is None:
            return

        try:
            try:
                tags = ID3(file_path)
            except Exception:
                tags = ID3()

            book_title = str(book.title or "audiobook")
            normalized_track_index = max(0, safe_int(track_index, 0))
            normalized_total_tracks = max(0, safe_int(total_tracks, 0))
            title_value = track.get("title", "") if isinstance(track, Mapping) else getattr(track, "title", "")
            chapter_title = str(title_value or "").strip()
            if chapter_title:
                # Keep meaningful chapter names in players instead of replacing
                # every TIT2 tag with a generic "part NN" label.  Avoid
                # duplicating the book title when the source title already
                # contains it.
                if chapter_title.casefold().startswith(book_title.casefold()):
                    part_name = chapter_title
                else:
                    part_name = f"{book_title} — {chapter_title}"
            else:
                part_name = f"{book_title} — часть {normalized_track_index:02d}"

            tags.delall("TIT2")
            tags.delall("TPE1")
            tags.delall("TALB")
            tags.delall("TRCK")

            tags.add(TIT2(encoding=3, text=part_name))
            tags.add(TALB(encoding=3, text=book_title))
            tags.add(TRCK(encoding=3, text=f"{normalized_track_index}/{normalized_total_tracks}"))

            author = str(getattr(book, "author", "") or "").strip()
            if author and TPE1 is not None:
                tags.add(TPE1(encoding=3, text=author))

            normalized_cover = normalize_cover_cache(cover)
            if normalized_cover and APIC is not None:
                data, mime = normalized_cover
                tags.delall("APIC")
                tags.add(
                    APIC(
                        encoding=3,
                        mime=mime or "image/jpeg",
                        type=3,
                        desc="Cover",
                        data=data,
                    )
                )

            tags.save(file_path)
            app_logger.debug(
                "BOOK FLOW | event=id3_written | title=%s | narrator=%s | track=%s/%s | file=%s",
                str(getattr(book, "title", "") or "-"),
                str(getattr(book, "narrator", "") or "-"),
                normalized_track_index, normalized_total_tracks, Path(file_path).name,
            )

        except Exception as e:
            app_logger.warning("Не удалось записать ID3 в %s", Path(file_path).name, exc_info=True)
            self.log(f"Не удалось записать ID3 в {Path(file_path).name}: {e}")

    def _split_track(self, book, track, source_path):
        out = self._track_path(book, track)
        if out.exists():
            try:
                out.unlink()
            except Exception:
                pass

        start = parse_time_seconds(getattr(track, "start", None))
        end = parse_time_seconds(getattr(track, "end", None))
        duration = None
        if start is not None and end is not None and end > start:
            duration = end - start
        elif start is None and end is None:
            # One-file-per-chapter providers often expose only an approximate
            # metadata duration. Passing that rounded value as -t truncates the
            # physical file (and can cut the final word/fade). With no slicing
            # boundary, process the complete source to EOF.
            duration = None
        else:
            try:
                measured = effective_track_duration(track)
                duration = float(measured) if measured is not None and float(measured) > 0 else None
            except (TypeError, ValueError):
                duration = None
            # Some chapter manifests carry only start markers. Infer the end
            # from the next chapter when possible; only the final chapter may
            # intentionally run from its start to EOF.
            if duration is None and start is not None:
                tracks = list(getattr(book, "tracks", None) or [])
                track_index = safe_int(getattr(track, "index", None), -1)
                current_pos = next(
                    (
                        i
                        for i, item in enumerate(tracks)
                        if item is track
                        or (track_index >= 0 and safe_int(getattr(item, "index", None), -1) == track_index)
                    ),
                    -1,
                )
                if 0 <= current_pos < len(tracks) - 1:
                    next_track = tracks[current_pos + 1]
                    current_file = str(getattr(track, "file", "") or "").strip()
                    next_file = str(getattr(next_track, "file", "") or "").strip()
                    if current_file and next_file and current_file == next_file:
                        next_start = parse_time_seconds(getattr(next_track, "start", None))
                        inferred = next_start - start if next_start is not None else 0.0
                        if inferred > 0:
                            duration = inferred
                        elif duration is None:
                            self.log(
                                f"Предупреждение: для промежуточной части "
                                f"{safe_int(getattr(track, 'index', None), current_pos + 1)} "
                                "не удалось определить конец; FFmpeg будет читать "
                                "общий источник до EOF."
                            )
                            app_logger.warning(
                                "MEDIA | event=split_missing_middle_boundary | track=%s | start=%s | next_start=%s",
                                safe_int(getattr(track, "index", None), current_pos + 1),
                                start,
                                next_start,
                            )

        # Keep FFmpeg argv stable/readable for integral timestamps ("10"
        # rather than "10.0") while retaining sub-second precision when needed.
        if start is not None and float(start).is_integer():
            start = int(float(start))
        if duration is not None and float(duration).is_integer():
            duration = int(float(duration))

        copy_mode, bitrate, channels = self._effective_mp3_profile(source_path)

        def make_cmd(use_copy):
            normalization_filter = ""
            local_bitrate = bitrate
            local_channels = channels
            if not use_copy:
                normalization_filter = self._normalization_filter_for_track(
                    source_path, start, duration
                )
                if not local_bitrate:
                    info = self._cached_probe_audio_info(source_path)
                    source_bps = int(info.get("bit_rate") or 0)
                    local_bitrate = f"{max(48, int(round((source_bps or 96_000) / 1000)))}k"
                if not local_channels:
                    info = self._cached_probe_audio_info(source_path)
                    source_channels = int(info.get("channels") or 0)
                    local_channels = max(1, min(2, source_channels or 2))

            cmd = [resolve_executable("ffmpeg") or "ffmpeg", "-hide_banner", "-nostdin", "-y"]
            # Keep first- and second-pass loudnorm on the same time window.
            # For transcoding FFmpeg's accurate_seek is enabled by default, so
            # input-side -ss avoids decoding hours from the beginning while
            # still discarding frames before the requested timestamp.
            if start is not None:
                cmd += ["-ss", str(start)]
            cmd += ["-i", str(source_path)]
            if duration is not None:
                cmd += ["-t", str(duration)]
            cmd += ["-map", "0:a:0"]

            if use_copy:
                cmd += ["-c:a", "copy", "-avoid_negative_ts", "make_zero"]
            else:
                if normalization_filter:
                    cmd += ["-af", normalization_filter]
                cmd += ["-c:a", "libmp3lame"]
                if local_bitrate:
                    cmd += ["-b:a", local_bitrate]
                else:
                    cmd += ["-q:a", "4"]
                if local_channels:
                    cmd += ["-ac", str(local_channels)]
            cmd += [str(out)]
            return cmd

        try:
            self._run_ffmpeg(make_cmd(copy_mode))
        except RuntimeError as exc:
            if not copy_mode:
                raise
            # Some hosts serve a stream whose actual codec/container differs from
            # what ffprobe reported.  Preserve the user's "original quality" intent
            # where possible, but never fail just because stream-copy cannot be muxed
            # into an MP3 container. Retry this track with a compatible MP3 encode.
            try:
                out.unlink(missing_ok=True)
            except Exception:
                pass
            self.log(
                f"{out.name}: прямое копирование аудиопотока не удалось; "
                "повторяю с совместимым MP3-кодированием."
            )
            try:
                app_logger.info("FFmpeg stream-copy fallback triggered: %s", exc)
            except Exception:
                pass
            self._run_ffmpeg(make_cmd(False))
        return out

    def _save_book_sidecars(self, book, folder, tracks):
        """Save portable metadata sidecars for Audiobookshelf and archival workflows."""
        if not bool(getattr(self, "runtime_save_sidecars", True)):
            self._log_book_flow("sidecars_skipped", book, reason="disabled")
            return
        try:
            folder = Path(folder)
            title = str(book.title or "")
            author = str(book.author or "")
            narrator = str(book.narrator or "")
            genre = str(book.genre or "")
            year = str(book.year or "")
            description = str(book.description or "")
            source_url = str(book.url or "")
            cover_url = str(book.cover_url or "")
            playlist_url = str(book.playlist_url or "")
            genres = [x.strip() for x in re.split(r"[,;/]+", genre) if x.strip()]
            narrators = [x.strip() for x in re.split(r"[,;/]+", narrator) if x.strip()]
            authors = [x.strip() for x in re.split(r"[,;/]+", author) if x.strip()]

            chapter_rows = []
            cursor = 0.0
            for t in tracks:
                dur = float(effective_track_duration(t) or 0)
                chapter_title = str(t.title or "").strip() or f"Часть {int(t.index):02d}"
                chapter_rows.append({
                    "index": int(t.index),
                    "title": chapter_title,
                    "start": t.start,
                    "end": t.end,
                    "duration": dur if dur > 0 else None,
                    "timeline_start": cursor,
                    "timeline_end": cursor + dur,
                })
                cursor += dur

            # Keep the original friendly keys, plus Audiobookshelf-compatible aliases.
            payload = {
                "title": title,
                "author": author,
                "authors": authors,
                "narrator": narrator,
                "narrators": narrators,
                "genre": genre,
                "genres": genres,
                "year": year,
                "publishedYear": year,
                "description": description,
                "source_url": source_url,
                "cover_url": cover_url,
                "playlist_url": playlist_url,
                "durationSeconds": cursor,
                "tracks": chapter_rows,
            }
            # metadata.json participates in duplicate detection, so never
            # expose a partially written JSON file to a later app start.
            save_json(folder / "metadata.json", payload, raise_errors=True)

            lines = [
                f"Название: {title}",
                f"Автор: {author or '—'}",
                f"Диктор: {narrator or '—'}",
                f"Жанр: {genre or '—'}",
                f"Год: {year or '—'}",
                f"Источник: {source_url}",
                "",
                "Описание:", description or "—", "", "Главы:",
            ]
            width = track_number_width(book)
            for row in chapter_rows:
                lines.append(
                    f"{row['index']:0{width}d}. {fmt_time(row['timeline_start'])}–{fmt_time(row['timeline_end'])}  {row['title']}"
                )
            atomic_write_text(folder / "book_info.txt", "\n".join(lines) + "\n", encoding="utf-8")

            # Audiobookshelf documents NFO as a simple text metadata source.
            nfo_lines = [
                f"Title: {title}",
                f"Author: {author}",
                f"Read by: {narrator}",
                f"Genre: {genre}",
                f"Release Date: {year}",
                f"Source URL: {source_url}",
                "",
                "Book Description",
                "================",
                description,
                "",
            ]
            atomic_write_text(folder / "book.nfo", "\n".join(nfo_lines), encoding="utf-8")

            # Audiobookshelf also recognizes these simple sidecars directly.
            if description:
                atomic_write_text(folder / "desc.txt", description + "\n", encoding="utf-8")
            if narrator:
                atomic_write_text(folder / "reader.txt", narrator + "\n", encoding="utf-8")

            cover = self._cover_bytes(book)
            if cover:
                data, mime = cover
                mime_text = str(mime or "").lower()
                if "png" in mime_text:
                    ext = ".png"
                elif "webp" in mime_text:
                    ext = ".webp"
                else:
                    ext = ".jpg"
                for old_ext in (".jpg", ".jpeg", ".png", ".webp"):
                    if old_ext == ext:
                        continue
                    try:
                        (folder / ("cover" + old_ext)).unlink(missing_ok=True)
                    except OSError:
                        pass
                atomic_write_bytes(folder / ("cover" + ext), data)
            self._log_book_flow(
                "sidecars_saved", book, folder=folder, chapters=len(chapter_rows),
                cover_saved=bool(cover),
            )
        except Exception as e:
            app_logger.warning("Не удалось сохранить sidecar metadata/NFO", exc_info=True)
            self.log(f"Не удалось сохранить book_info/metadata/NFO: {e}")

    def _scan_audiobookshelf_after_book(self):
        if not bool(getattr(self, "runtime_abs_enabled", False)):
            return
        try:
            audiobookshelf_scan(
                getattr(self, "runtime_abs_url", ""),
                getattr(self, "runtime_abs_api_key", ""),
                getattr(self, "runtime_abs_library_id", ""),
            )
            self.log("Audiobookshelf: запущено сканирование библиотеки.")
        except Exception as e:
            # Integration failures must never invalidate a successfully downloaded book.
            app_logger.warning("Audiobookshelf scan failed", exc_info=True)
            self.log(f"Audiobookshelf: не удалось запустить scan: {e}")


__all__ = ["MediaProcessingMixin"]
