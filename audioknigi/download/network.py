from __future__ import annotations

import json
import os
import subprocess
import tempfile
import queue
import re
import shutil
import threading
import time
import weakref
from collections import deque
from pathlib import Path
from urllib.parse import urlsplit

import requests

from ..core import Cancelled, USER_AGENT, fmt_size, fmt_time, get_http_session, resolve_executable, hidden_subprocess_kwargs
from ..cover_fetch import fetch_cover_bytes
from ..logging_utils import app_logger
from ..sources import source_name
from .common import atomic_write_text, replace_with_retry, unlink_with_retry
from .errors import RangeUnsupported
from .hls_parallel import stage_hls_vod

_ACTIVE_IO_INIT_LOCK = threading.Lock()


def _segment_files(part: Path) -> list[Path]:
    """Return literal numbered ``.segNNN`` siblings without glob ambiguity."""
    part = Path(part)
    prefix = part.name + ".seg"
    try:
        result = []
        for item in part.parent.iterdir():
            if not item.name.startswith(prefix):
                continue
            suffix = item.name[len(prefix) :]
            if suffix.isdigit():
                result.append(item)
        return result
    except OSError:
        return []


class BandwidthLimiter:
    """Aggregate token-bucket limiter shared by all HTTP workers."""

    def __init__(self, bytes_per_second=0):
        self.rate = max(0.0, float(bytes_per_second or 0))
        self.capacity = self._capacity(self.rate)
        self.tokens = self.capacity
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    @staticmethod
    def _capacity(rate):
        if rate <= 0:
            return 0.0
        return max(64 * 1024.0, min(rate * 0.35, 2 * 1024 * 1024.0))

    def set_rate(self, bytes_per_second):
        new_rate = max(0.0, float(bytes_per_second or 0))
        with self.lock:
            if abs(new_rate - self.rate) < 1.0:
                return
            self.rate = new_rate
            self.capacity = self._capacity(new_rate)
            self.tokens = min(self.tokens, self.capacity) if new_rate else 0.0
            self.updated = time.monotonic()

    def consume(self, amount, cancel_event):
        remaining = max(0, int(amount or 0))
        while remaining > 0:
            with self.lock:
                if self.rate <= 0:
                    return
                quantum = min(remaining, max(1, int(self.capacity)))
                now = time.monotonic()
                elapsed = max(0.0, now - self.updated)
                self.updated = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                if self.tokens >= quantum:
                    self.tokens -= quantum
                    remaining -= quantum
                    continue
                wait_for = max(0.005, min(0.15, (quantum - self.tokens) / self.rate))
            if cancel_event is not None:
                if cancel_event.wait(wait_for):
                    raise Cancelled("Операция отменена пользователем.")
            else:
                time.sleep(wait_for)


class AdaptiveRangeController:
    """Adjust Range concurrency from observed per-worker throughput."""

    def __init__(self, initial_workers, adaptive=True, min_per_worker=256 * 1024):
        self.initial_workers = max(1, int(initial_workers))
        self.target_workers = self.initial_workers
        self.adaptive = bool(adaptive)
        self.min_per_worker = float(min_per_worker)
        self.slow_samples = 0
        self.fast_samples = 0
        self.last_change = time.monotonic()
        self.lock = threading.Lock()

    def current_workers(self):
        with self.lock:
            return self.target_workers

    def observe(self, aggregate_speed):
        if not self.adaptive:
            return self.current_workers()
        with self.lock:
            target = self.target_workers
            per_worker = float(aggregate_speed or 0.0) / max(1, target)
            now = time.monotonic()
            if per_worker < self.min_per_worker:
                self.slow_samples += 1
                self.fast_samples = 0
            else:
                self.slow_samples = max(0, self.slow_samples - 1)
                if target < self.initial_workers and per_worker >= self.min_per_worker * 1.25:
                    self.fast_samples += 1
                else:
                    self.fast_samples = max(0, self.fast_samples - 1)
            if target > 2 and self.slow_samples >= 5 and now - self.last_change >= 3.0:
                self.target_workers = max(2, target // 2)
                self.slow_samples = 0
                self.fast_samples = 0
                self.last_change = now
            elif target < self.initial_workers and self.fast_samples >= 8 and now - self.last_change >= 4.0:
                self.target_workers = min(self.initial_workers, max(target + 1, target * 2))
                self.slow_samples = 0
                self.fast_samples = 0
                self.last_change = now
            return self.target_workers


class SlidingSpeedMeter:
    def __init__(self, window_seconds=5.0):
        self.window = float(window_seconds)
        self.samples = deque()
        self.lock = threading.Lock()

    def update(self, total_done):
        now = time.monotonic()
        current = int(total_done)
        with self.lock:
            # A resumed/restarted transfer can legitimately reset its aggregate
            # counter.  Do not mix samples from before and after that reset.
            if self.samples and current < self.samples[-1][1]:
                self.samples.clear()
            self.samples.append((now, current))
            cutoff = now - self.window
            while len(self.samples) > 2 and self.samples[0][0] < cutoff:
                self.samples.popleft()
            if len(self.samples) < 2:
                return 0.0
            t0, b0 = self.samples[0]
            t1, b1 = self.samples[-1]
            return max(0.0, (b1 - b0) / max(0.001, t1 - t0))


class NetworkDownloadMixin:
    """Network subsystem for the downloader facade."""

    def _fetch_cover_bytes(self, url: str, referer: str = ""):
        return fetch_cover_bytes(
            url, referer, cancel_event=getattr(self, "cancel_event", None)
        )

    def _register_active_subprocess(self, proc):
        if proc is None:
            return
        lock = getattr(self, "_active_subprocess_lock", None)
        if lock is None:
            with _ACTIVE_IO_INIT_LOCK:
                lock = getattr(self, "_active_subprocess_lock", None)
                if lock is None:
                    lock = threading.RLock()
                    self._active_subprocess_lock = lock
                if getattr(self, "_active_subprocesses", None) is None:
                    self._active_subprocesses = weakref.WeakSet()
        with lock:
            processes = getattr(self, "_active_subprocesses", None)
            if processes is None:
                processes = weakref.WeakSet()
                self._active_subprocesses = processes
            processes.add(proc)

    def _unregister_active_subprocess(self, proc):
        if proc is None:
            return
        lock = getattr(self, "_active_subprocess_lock", None)
        processes = getattr(self, "_active_subprocesses", None)
        if lock is None or processes is None:
            return
        with lock:
            try:
                processes.discard(proc)
            except Exception:
                pass

    def _cancel_active_subprocesses(self):
        """Terminate currently running FFmpeg/FFprobe processes on cancel/exit."""
        lock = getattr(self, "_active_subprocess_lock", None)
        processes = getattr(self, "_active_subprocesses", None)
        if lock is None or not processes:
            return 0
        with lock:
            active = list(processes)
            # Claim the snapshot before killing outside the lock. Multiple
            # download/split workers can observe the same cancel_event at once;
            # only one of them should issue kill() for a given Windows handle.
            try:
                processes.difference_update(active)
            except Exception:
                for proc in active:
                    processes.discard(proc)
        killed = 0
        for proc in active:
            try:
                if proc.poll() is None:
                    proc.kill()
                    killed += 1
            except Exception:
                app_logger.debug("Ошибка остановки subprocess при отмене", exc_info=True)
        return killed

    def _register_active_network_response(self, response):
        if response is None:
            return
        lock = getattr(self, "_active_network_lock", None)
        if lock is None:
            with _ACTIVE_IO_INIT_LOCK:
                lock = getattr(self, "_active_network_lock", None)
                if lock is None:
                    lock = threading.RLock()
                    self._active_network_lock = lock
                if getattr(self, "_active_network_responses", None) is None:
                    self._active_network_responses = set()
        with lock:
            responses = getattr(self, "_active_network_responses", None)
            if responses is None:
                responses = set()
                self._active_network_responses = responses
            responses.add(response)

    def _unregister_active_network_response(self, response):
        lock = getattr(self, "_active_network_lock", None)
        responses = getattr(self, "_active_network_responses", None)
        if lock is None or responses is None:
            return
        with lock:
            responses.discard(response)

    def _cancel_active_network_io(self):
        """Close currently streaming HTTP responses so Cancel is not held by a read timeout."""
        lock = getattr(self, "_active_network_lock", None)
        responses = getattr(self, "_active_network_responses", None)
        if lock is None or not responses:
            return 0
        with lock:
            active = list(responses)
            # Claim this snapshot before closing outside the lock. Several Range
            # workers can observe cancellation concurrently; without removing
            # these objects here they can all close the same urllib3 stream.
            responses.difference_update(active)
        closed = 0
        for response in active:
            try:
                response.close()
                closed += 1
            except Exception:
                app_logger.debug("Ошибка закрытия HTTP response при отмене", exc_info=True)
        if closed:
            app_logger.info("BOOK FLOW | event=cancel_network_interrupt | responses=%s", closed)
        return closed

    def _get_bandwidth_limiter(self):
        limit_mb_s = float(getattr(self, "runtime_bandwidth_limit", 0.0) or 0.0)
        rate = limit_mb_s * 1024 * 1024
        limiter = getattr(self, "_bandwidth_limiter", None)
        if limiter is None:
            limiter = BandwidthLimiter(rate)
            self._bandwidth_limiter = limiter
        else:
            limiter.set_rate(rate)
        return limiter

    def _range_info(self, url, referer):
        """Return (supports_ranges, total_size) using a one-byte request."""
        try:
            session = get_http_session()
            with session.get(
                url,
                headers={"Referer": referer, "Range": "bytes=0-0", "Accept-Encoding": "identity"},
                stream=True,
                timeout=(10, 20),
            ) as response:
                response.raise_for_status()
                content_range = response.headers.get("content-range", "")
                match = re.match(r"(?i)^bytes\s+0-0\s*/\s*(\d+)", content_range.strip())
                if response.status_code == 206 and match:
                    return True, int(match.group(1))
                length = int(response.headers.get("content-length", 0) or 0)
                return False, length if response.status_code == 200 else 0
        except Exception:
            return False, 0

    def _download_single(self, url, target, referer, *, _restart_after_416=False):
        self._check_cancel()
        target = Path(target)
        part = target.with_name(target.name + ".part")
        existing = part.stat().st_size if part.exists() else 0
        headers = {"Referer": referer, "Accept-Encoding": "identity"}
        if existing > 0:
            headers["Range"] = f"bytes={existing}-"

        limiter = self._get_bandwidth_limiter()
        meter = SlidingSpeedMeter(window_seconds=5.0)
        last_report = 0.0

        session = get_http_session()
        try:
            with session.get(url, headers=headers, stream=True, timeout=(20, 120)) as response:
                self._register_active_network_response(response)
                try:
                    # A retry after discarding a stale/oversized .part must be the
                    # final restart attempt. If a broken CDN/proxy answers 416 even
                    # to that zero-offset request, surface the HTTP failure instead
                    # of ever recursing again.
                    if _restart_after_416 and response.status_code == 416:
                        response.raise_for_status()

                    # A previous run may have downloaded the complete .part but
                    # exited before the final atomic rename.  Servers correctly
                    # answer Range: bytes=<total>- with 416; Content-Range tells us
                    # whether the local partial is already complete.
                    resume_already_complete = False
                    restart_from_zero = False
                    if existing > 0 and response.status_code == 416:
                        content_range = response.headers.get("content-range", "")
                        # RFC-compliant 416 responses normally use ``bytes */N``, but
                        # real CDNs also return ``bytes 0-(N-1)/N`` or even ``/N``.
                        # At status 416 the trailing total is sufficient to decide
                        # whether our local partial file is already complete.
                        complete_match = re.search(
                            r"(?:bytes\s+)?(?:\*|\d+\s*-\s*\d+)?\s*/\s*(\d+)\s*$",
                            content_range,
                            re.I,
                        )
                        if complete_match and existing == int(complete_match.group(1)):
                            resume_already_complete = True
                            if not bool(getattr(self, "_suppress_source_transfer_ui", False)):
                                self.set_progress(100)
                        else:
                            # A stale/oversized partial can never satisfy the same
                            # Range request. Close this response, discard the bad
                            # .part and retry exactly once from byte zero.
                            restart_from_zero = True
                    if not resume_already_complete and not restart_from_zero:
                        response.raise_for_status()
                        if existing > 0 and response.status_code != 206:
                            existing = 0
                            mode = "wb"
                        else:
                            mode = "ab" if existing > 0 else "wb"

                        content_range = response.headers.get("content-range", "")
                        match = re.search(r"/(\d+)$", content_range)
                        if match:
                            total = int(match.group(1))
                        else:
                            length = int(response.headers.get("content-length", 0) or 0)
                            total = existing + length if length else 0

                        done = existing
                        meter.update(done)
                        with open(part, mode) as file_obj:
                            for chunk in response.iter_content(chunk_size=512 * 1024):
                                self._check_cancel()
                                if not chunk:
                                    continue
                                limiter.consume(len(chunk), getattr(self, "cancel_event", None))
                                file_obj.write(chunk)
                                done += len(chunk)
                                speed = meter.update(done)
                                try:
                                    self.record_transfer_metrics(speed, 1)
                                except Exception:
                                    pass
                                now = time.monotonic()
                                if now - last_report >= 0.20:
                                    last_report = now
                                    speed_text = f"{fmt_size(speed)}/s" if speed > 0 else "—"
                                    if not bool(getattr(self, "_suppress_source_transfer_ui", False)):
                                        if total:
                                            self.set_progress(done * 100 / total)
                                            eta = (total - done) / speed if speed > 0 else None
                                            self.set_status(
                                                f"Скачано {fmt_size(done)} из {fmt_size(total)}  •  "
                                                f"{speed_text}  •  ETA {fmt_time(eta) if eta is not None else '—'}"
                                            )
                                        else:
                                            self.set_status(f"Скачано {fmt_size(done)}  •  {speed_text}")
                        if total and done < total:
                            raise RuntimeError(
                                f"Загрузка оборвалась: получено {fmt_size(done)} из {fmt_size(total)}."
                            )
                finally:
                    self._unregister_active_network_response(response)

            if restart_from_zero:
                try:
                    unlink_with_retry(part, missing_ok=True)
                except OSError as exc:
                    raise RuntimeError(
                        f"Не удалось удалить повреждённый временный файл {part.name}: {exc}"
                    ) from exc
                return self._download_single(url, target, referer, _restart_after_416=True)

            replace_with_retry(part, target)
            return target
        except Cancelled:
            raise
        except requests.RequestException as e:
            self._check_cancel()
            raise RuntimeError(f"Сетевая ошибка после автоматических повторов: {e}") from e
        finally:
            # Reset UI/telemetry even when the final Windows rename fails (for
            # example because an antivirus temporarily holds the target file).
            try:
                self.record_transfer_metrics(0, 0)
            except Exception:
                pass

    def _download_segment(self, url, seg_path, start_byte, end_byte, referer, progress_cb, peer_abort_event=None):
        """Download one logical Range segment, tolerating server-side response caps.

        Some CDNs/proxies accept a large Range request but intentionally return only a
        smaller 206 slice (for example exactly 3 MiB).  Such a response is valid as
        long as Content-Range starts at the requested byte.  Keep requesting from the
        first missing byte until the complete logical segment is present.
        """
        self._check_cancel()
        seg_path = Path(seg_path)
        segment_size = end_byte - start_byte + 1
        existing = seg_path.stat().st_size if seg_path.exists() else 0
        if existing > segment_size:
            unlink_with_retry(seg_path, missing_ok=True)
            existing = 0
        if existing == segment_size:
            progress_cb(0, force=True)
            return segment_size

        limiter = self._get_bandwidth_limiter()
        consecutive_no_progress = 0
        subrequest_count = 0

        def peer_aborted() -> bool:
            return peer_abort_event is not None and peer_abort_event.is_set()

        def wait_before_retry() -> bool:
            delay = min(1.0, 0.15 * max(1, consecutive_no_progress))
            if peer_abort_event is not None and peer_abort_event.wait(delay):
                return True
            cancel_event = getattr(self, "cancel_event", None)
            if cancel_event is not None:
                if cancel_event.wait(0 if peer_abort_event is not None else delay):
                    self._check_cancel()
            elif peer_abort_event is None:
                time.sleep(delay)
            return peer_aborted()

        while existing < segment_size:
            self._check_cancel()
            if peer_aborted():
                return existing
            request_start = start_byte + existing
            headers = {
                "Referer": referer,
                "Range": f"bytes={request_start}-{end_byte}",
                "Accept-Encoding": "identity",
            }
            before_request = existing
            subrequest_count += 1
            if subrequest_count > 512:
                raise RuntimeError("Слишком много повторных Range-запросов для одного сегмента.")

            try:
                session = get_http_session()
                with session.get(url, headers=headers, stream=True, timeout=(20, 120)) as response:
                    self._register_active_network_response(response)
                    try:
                        status = int(response.status_code)
                        if status == 200:
                            raise RangeUnsupported("Сервер проигнорировал Range и вернул HTTP 200")
                        if status == 416:
                            raise RangeUnsupported("Сервер отклонил запрошенный Range: HTTP 416")
                        # Retry/transport policy may return a final transient HTTP
                        # response instead of raising. Preserve completed segments and
                        # treat 429/5xx as a network failure, never as lack of Range.
                        if status == 429 or 500 <= status <= 599:
                            raise requests.HTTPError(
                                f"Временная ошибка Range HTTP {status}", response=response
                            )
                        if status != 206:
                            response.raise_for_status()
                            raise RuntimeError(f"Неожиданный HTTP-статус Range: {status}")
                        cr = response.headers.get("content-range", "")
                        match = re.match(r"(?i)^bytes\s+(\d+)-(\d+)/(\d+|\*)$", cr.strip())
                        if not match:
                            raise RangeUnsupported(f"Некорректный Content-Range: {cr}")
                        actual_start = int(match.group(1))
                        actual_end = int(match.group(2))
                        if actual_start != request_start or actual_end < actual_start:
                            raise RangeUnsupported(f"Некорректный Content-Range: {cr}")
                        if actual_end > end_byte:
                            raise RangeUnsupported(
                                f"Сервер вернул диапазон за пределами запрошенного сегмента: {cr}"
                            )
    
                        expected_this_response = actual_end - actual_start + 1
                        received_this_response = 0
                        with open(seg_path, "ab" if existing else "wb") as file_obj:
                            for chunk in response.iter_content(chunk_size=512 * 1024):
                                self._check_cancel()
                                if peer_aborted():
                                    return existing
                                if not chunk:
                                    continue
                                remaining = segment_size - existing
                                if remaining <= 0:
                                    break
                                if len(chunk) > remaining:
                                    chunk = chunk[:remaining]
                                limiter.consume(len(chunk), getattr(self, "cancel_event", None))
                                file_obj.write(chunk)
                                existing += len(chunk)
                                received_this_response += len(chunk)
                                progress_cb(len(chunk))
    
                        # A clean short 206 response is not an error: many CDNs cap the
                        # amount returned per request. The outer loop resumes from the
                        # first byte that is still missing.
                        if received_this_response > 0:
                            consecutive_no_progress = 0
    
                        if received_this_response < expected_this_response:
                            self.log(
                                f"Range-ответ оборвался после {fmt_size(received_this_response)}; "
                                f"продолжаю сегмент с байта {start_byte + existing}."
                            )
                        elif actual_end < end_byte:
                            self.log(
                                f"Сервер ограничил Range-ответ до {fmt_size(received_this_response)}; "
                                f"автоматически продолжаю сегмент."
                            )
                    finally:
                        self._unregister_active_network_response(response)

            except requests.RequestException as exc:
                self._check_cancel()
                if peer_aborted():
                    return existing
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status in (404, 410):
                    # A vanished media URL will not recover by retrying the same
                    # Range request. Bubble it up immediately so the book-level
                    # refresh logic can fetch a fresh playlist.
                    raise
                # iter_content may raise after part of a response was already written.
                # Preserve those bytes and retry from the new file offset.
                current_size = seg_path.stat().st_size if seg_path.exists() else 0
                current_size = min(current_size, segment_size)
                made_progress = current_size > before_request
                existing = current_size
                if made_progress:
                    consecutive_no_progress = 0
                    self.log(
                        f"Соединение прервалось, но {fmt_size(existing)} сегмента уже сохранено; "
                        "продолжаю с места остановки."
                    )
                    continue
                consecutive_no_progress += 1
                if consecutive_no_progress >= 5:
                    raise RuntimeError(
                        f"Сетевая ошибка Range после повторов: {exc}"
                    ) from exc
                self.log(
                    f"Range-запрос временно не удался ({consecutive_no_progress}/5); "
                    "повторяю с того же байта."
                )
                if wait_before_retry():
                    return existing
                continue
            except OSError:
                # Closing a streamed response from the coordinator can surface as a
                # raw socket/file OSError.  A peer failure is not a user cancellation:
                # stop this worker quietly and preserve the first/root exception.
                self._check_cancel()
                if peer_aborted():
                    return existing
                raise

            if existing <= before_request:
                consecutive_no_progress += 1
            if consecutive_no_progress >= 5:
                raise RuntimeError(
                    f"Сегмент не продвигается: {existing} из {segment_size} байт."
                )
            if existing <= before_request and wait_before_retry():
                return existing

        final_size = seg_path.stat().st_size
        if final_size != segment_size:
            raise RuntimeError(
                f"Сегмент скачан не полностью: {final_size} вместо {segment_size} байт"
            )
        return final_size

    def _choose_segment_count(self, total_size):
        mode = str(getattr(self, "runtime_segment_count", "auto") or "auto").lower()
        if mode != "auto":
            try:
                return max(1, min(8, int(mode)))
            except Exception:
                return 1
        mb = float(total_size or 0) / (1024 * 1024)
        if mb < 50:
            return 2
        if mb <= 300:
            return 4
        return 8

    def _download_segmented(self, url, target, referer, total_size, segment_count):
        """Download a file as resumable byte-range chunks with adaptive concurrency."""
        self._check_cancel()
        total_size = int(total_size or 0)
        if total_size <= 0:
            raise RangeUnsupported("Неизвестен положительный размер файла для Range-загрузки")
        target = Path(target)
        part = target.with_name(target.name + ".part")
        initial_workers = max(2, min(8, int(segment_count)))

        # Use more range tasks than workers. That allows the controller to lower
        # concurrency between chunks without aborting already-open requests.
        min_chunk = 4 * 1024 * 1024
        desired_tasks = max(initial_workers, initial_workers * 3)
        max_tasks_by_size = max(1, total_size // min_chunk)
        task_count = max(
            1,
            min(total_size, max(initial_workers, min(32, desired_tasks, max_tasks_by_size))),
        )

        ranges = []
        base = total_size // task_count
        offset = 0
        for idx in range(task_count):
            start = offset
            end = total_size - 1 if idx == task_count - 1 else (start + base - 1)
            seg = Path(str(part) + f".seg{idx:03d}")
            ranges.append((idx, start, end, seg))
            offset = end + 1

        # Segment files from a previous run are safe to resume only when they
        # belong to the same remote object geometry. Without this small sidecar,
        # a refreshed CDN URL/size could accidentally assemble old and new
        # chunks that happen to share .segNNN filenames.
        segment_meta = part.with_name(part.name + ".segments.json")
        segment_signature = {
            "version": 1,
            "url": str(url or ""),
            "total_size": int(total_size),
            "task_count": int(task_count),
            "ranges": [[int(start), int(end)] for _idx, start, end, _seg in ranges],
        }
        existing_signature = None
        try:
            if segment_meta.is_file():
                parsed_signature = json.loads(segment_meta.read_text(encoding="utf-8"))
                if isinstance(parsed_signature, dict):
                    existing_signature = parsed_signature
        except (OSError, json.JSONDecodeError, UnicodeError):
            existing_signature = None
        existing_segments = _segment_files(part)
        if existing_segments and existing_signature != segment_signature:
            for stale_segment in existing_segments:
                try:
                    unlink_with_retry(stale_segment, missing_ok=True)
                except OSError:
                    pass
            try:
                unlink_with_retry(part.with_name(part.name + ".assembling"), missing_ok=True)
            except OSError:
                pass
        atomic_write_text(
            segment_meta,
            json.dumps(segment_signature, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

        # Drop oversized/corrupted resume segments before seeding aggregate
        # progress. Otherwise their capped size is counted here, then the worker
        # deletes them and downloads the same bytes again, making progress exceed
        # total_size.
        aggregate = 0
        for _idx, start, end, seg in ranges:
            if not seg.exists():
                continue
            segment_size = end - start + 1
            existing = seg.stat().st_size
            if existing > segment_size:
                unlink_with_retry(seg, missing_ok=True)
                continue
            aggregate += existing
        progress_lock = threading.Lock()
        meter = SlidingSpeedMeter(window_seconds=5.0)
        meter.update(aggregate)
        last_report = [0.0]
        adaptive = (
            str(getattr(self, "runtime_segment_count", "auto")).lower() == "auto"
            and float(getattr(self, "runtime_bandwidth_limit", 0.0) or 0.0) <= 0
        )
        # ``runtime_auto_chunk_min_kbps`` remains only as a runtime compatibility
        # alias for old callers; persisted settings migrated to KB/s in schema v2.
        min_worker_kbytes_per_sec = float(
            getattr(self, "runtime_auto_chunk_min_kbytes_per_sec",
                    getattr(self, "runtime_auto_chunk_min_kbps", 256)) or 256
        )
        controller = AdaptiveRangeController(
            initial_workers,
            adaptive=adaptive,
            min_per_worker=max(64.0, min_worker_kbytes_per_sec) * 1024.0,
        )
        last_target = [initial_workers]
        last_observe = [0.0]

        def report(delta, force=False):
            nonlocal aggregate
            with progress_lock:
                aggregate += int(delta)
                speed = meter.update(aggregate)
                now = time.monotonic()
                if not force and now - last_report[0] < 0.20:
                    return
                last_report[0] = now
                done = aggregate
                should_observe = now - last_observe[0] >= 0.20
                if should_observe:
                    last_observe[0] = now
            # Multiple Range workers can force a progress flush at nearly the
            # same instant. Sample the adaptive controller at most once per
            # reporting interval so one throughput observation cannot count as
            # several consecutive slow/fast samples.
            target_workers = controller.observe(speed) if should_observe else controller.current_workers()
            previous = None
            with progress_lock:
                if target_workers != last_target[0]:
                    previous = last_target[0]
                    last_target[0] = target_workers
            if previous is not None:
                if target_workers < previous:
                    self.log(
                        f"Auto-Chunker: снижаю активные Range-потоки "
                        f"{previous} → {target_workers} из-за низкой скорости на поток."
                    )
                else:
                    self.log(
                        f"Auto-Chunker: увеличиваю активные Range-потоки "
                        f"{previous} → {target_workers}: скорость восстановилась."
                    )
            if not bool(getattr(self, "_suppress_source_transfer_ui", False)):
                self.set_progress(done * 100 / total_size)
                eta = (total_size - done) / speed if speed > 0 else None
                self.set_status(
                    f"Range {target_workers}/{initial_workers} • {fmt_size(done)} из {fmt_size(total_size)} • "
                    f"{fmt_size(speed) + '/s' if speed > 0 else '—'} • "
                    f"ETA {fmt_time(eta) if eta is not None else '—'}"
                )
            try:
                self.record_transfer_metrics(speed, target_workers)
            except Exception:
                pass

        jobs = queue.Queue()
        for item in ranges:
            _idx, start, end, seg = item
            expected = end - start + 1
            if not seg.exists() or seg.stat().st_size != expected:
                jobs.put(item)

        errors = []
        errors_lock = threading.Lock()
        peer_abort_event = threading.Event()

        def worker(worker_id):
            cancel_event = getattr(self, "cancel_event", None)
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    return
                with errors_lock:
                    if errors:
                        return
                if worker_id >= controller.current_workers():
                    # The Range job queue is populated once and never receives
                    # new items. Once it is empty, a parked worker can terminate
                    # safely; otherwise reduced workers could sleep forever after
                    # active peers consume the final jobs.
                    if jobs.empty():
                        return
                    # Adaptive workers are parked rather than destroyed while
                    # queued work remains. If the link recovers, the controller
                    # can raise the target again and they resume taking jobs.
                    if cancel_event is not None:
                        if cancel_event.wait(0.10):
                            return
                    else:
                        time.sleep(0.10)
                    continue
                try:
                    _idx, start, end, seg = jobs.get_nowait()
                except queue.Empty:
                    return
                try:
                    self._download_segment(
                        url, seg, start, end, referer, report,
                        peer_abort_event=peer_abort_event,
                    )
                except Exception as exc:
                    with errors_lock:
                        # Preserve the first failure. Signal peers immediately so
                        # their internal retry loops stop before the coordinator
                        # closes active responses. Secondary socket errors must not
                        # replace RangeUnsupported/HTTP root causes.
                        if not errors:
                            errors.append(exc)
                            peer_abort_event.set()
                    return
                finally:
                    jobs.task_done()

        self.log(
            f"Сегментированная загрузка: {initial_workers} поток(а/ов), "
            f"{task_count} Range-задач."
        )
        threads = [
            threading.Thread(target=worker, args=(i,), daemon=True)
            for i in range(initial_workers)
        ]
        for thread in threads:
            thread.start()
        cancelled_peers_for_error = False
        try:
            for thread in threads:
                while thread.is_alive():
                    self._check_cancel()
                    with errors_lock:
                        has_error = bool(errors)
                    if has_error and not cancelled_peers_for_error:
                        self._cancel_active_network_io()
                        cancelled_peers_for_error = True
                    thread.join(0.20)
        finally:
            # Cancellation can raise from _check_cancel() before the ordinary
            # error path gets a chance to close registered response sockets.
            # Close sockets first, then give worker threads a bounded grace
            # period to release .seg/.part file handles before cleanup runs on
            # Windows (otherwise unlink can hit WinError 32).
            if any(thread.is_alive() for thread in threads):
                self._cancel_active_network_io()
            deadline = time.monotonic() + 2.0
            for thread in threads:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                thread.join(timeout=min(1.0, remaining))
            lingering = sum(1 for thread in threads if thread.is_alive())
            if lingering:
                app_logger.warning("NETWORK | event=segmented_cancel_workers_lingering | count=%d", lingering)

        if errors:
            err = errors[0]
            if isinstance(err, RangeUnsupported):
                for _idx, _start, _end, seg in ranges:
                    try:
                        unlink_with_retry(seg, missing_ok=True)
                    except OSError:
                        pass
                try:
                    unlink_with_retry(segment_meta, missing_ok=True)
                except OSError:
                    pass
                try:
                    unlink_with_retry(part.with_name(part.name + ".assembling"), missing_ok=True)
                except OSError:
                    pass
            raise err
        if not jobs.empty():
            raise RuntimeError("Auto-Chunker остановился до завершения всех Range-задач.")

        assembling = part.with_name(part.name + ".assembling")
        try:
            with open(assembling, "wb") as out:
                for _idx, start, end, seg in ranges:
                    self._check_cancel()
                    expected = end - start + 1
                    if not seg.exists() or seg.stat().st_size != expected:
                        raise RuntimeError(f"Не готов Range-сегмент {seg.name}.")
                    with open(seg, "rb") as inp:
                        shutil.copyfileobj(inp, out, length=1024 * 1024)
            if assembling.stat().st_size != total_size:
                raise RuntimeError("Ошибка объединения сегментов: итоговый размер не совпадает.")
            replace_with_retry(assembling, target)
        except Exception:
            try:
                unlink_with_retry(assembling, missing_ok=True)
            except Exception:
                pass
            raise
        try:
            unlink_with_retry(part, missing_ok=True)
        except OSError:
            pass
        for _idx, _start, _end, seg in ranges:
            try:
                unlink_with_retry(seg, missing_ok=True)
            except OSError:
                pass
        try:
            unlink_with_retry(segment_meta, missing_ok=True)
        except OSError:
            pass
        if not bool(getattr(self, "_suppress_source_transfer_ui", False)):
            self.set_progress(100)
        try:
            self.record_transfer_metrics(0, 0)
        except Exception:
            pass
        return target

    def _cleanup_partial_download(self, target):
        target = Path(target)
        part = target.with_name(target.name + ".part")
        candidates = [
            target,
            part,
            part.with_name(part.name + ".assembling"),
            part.with_name(part.name + ".segments.json"),
        ]
        try:
            candidates.extend(_segment_files(part))
        except Exception:
            pass
        for candidate in candidates:
            try:
                unlink_with_retry(Path(candidate), missing_ok=True)
            except Exception:
                pass

    def _download_source_with_fallback(self, primary_url, fallback_url, target, referer):
        urls = []
        for raw_url in (primary_url, fallback_url):
            candidate = str(raw_url or "").strip()
            if candidate and candidate not in urls:
                urls.append(candidate)
        last_error = None
        for pos, url in enumerate(urls, 1):
            if not url:
                continue
            try:
                return self._download_with_resume(url, target, referer)
            except Cancelled:
                raise
            except Exception as exc:
                last_error = exc
                if pos >= len(urls):
                    raise
                source_label = (
                    "Основной аудиоисточник"
                    if pos == 1
                    else f"Резервный источник ({source_name(url)})"
                )
                self.log(
                    f"{source_label} недоступен: {exc}. "
                    f"Пробую резервный источник {source_name(urls[pos])}."
                )
                self._cleanup_partial_download(target)
        if last_error is not None:
            raise last_error
        raise RuntimeError("Не указан адрес аудиофайла.")

    def _run_hls_ffmpeg(self, url, target, referer, *, start=None,
                        duration=None, expected_duration=None, chapter_label="",
                        progress_offset=0.0, progress_span=100.0):
        """Download/remux HLS with measured FFmpeg media-time progress.

        HLS is not ordinary MP3 HTTP Range: do not advertise network speed,
        resumability, or packet-level progress. Every attempt exclusively owns
        a unique temporary path; a Windows-locked old .part is untouched.
        """
        self._check_cancel()
        ffmpeg = resolve_executable("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("Для HLS источника необходим FFmpeg.")
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{target.stem}.hls-", suffix=".mp3", dir=str(target.parent),
        )
        os.close(fd)
        temp = Path(temp_name)
        headers = f"User-Agent: {USER_AGENT}\r\n"
        if referer:
            headers += f"Referer: {referer}\r\n"
        # Stream-copy into MP3 is lossless and very quick when the HLS codec
        # is MP3. AAC cannot be put in an MP3 container: only in that case
        # retry once with libmp3lame. For chapter seeks, decode accurately:
        # stream-copy would preserve the nearest HLS segment boundary instead.
        allow_copy = start is None and (
            str(getattr(self, "runtime_audio_preset", "copy") or "copy") == "copy"
            and str(getattr(self, "runtime_normalization_mode", "off") or "off") == "off"
        )
        preset = str(getattr(self, "runtime_audio_preset", "copy") or "copy")
        profile = {
            "64k_mono": ("64k", "1"),
            "96k_mono": ("96k", "1"),
            "128k_stereo": ("128k", "2"),
        }.get(preset)

        def command(copy_mode):
            cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
                   "-nostats", "-stats_period", "0.5", "-progress", "pipe:1", "-y"]
            if start is not None:
                # Input-side -ss uses the HLS VOD index, avoiding the download
                # of all earlier segments on seekable playlists.
                cmd += ["-ss", str(start)]
            if urlsplit(working_url).scheme in ("http", "https"):
                cmd += ["-headers", headers]
            if is_parallel:
                # The staged AES-128 key uses a .key extension; FFmpeg does not
                # allow that by default. The local manifest and its files were
                # validated and written by this app in a private temp directory.
                cmd += ["-allowed_extensions", "ALL"]
            cmd += ["-i", working_url]
            if duration is not None:
                cmd += ["-t", str(duration)]
            cmd += ["-map", "0:a:0", "-vn", "-c:a", "copy" if copy_mode else "libmp3lame"]
            if not copy_mode:
                cmd += ["-b:a", profile[0] if profile else "160k"]
                if profile:
                    cmd += ["-ac", profile[1]]
            cmd += ["-f", "mp3", str(temp)]
            return cmd

        # The old FFmpeg-only mode remains a fallback for unsupported HLS
        # playlists or servers that decline parallel requests. Stage only a
        # *whole* source; individual selected chapters already use FFmpeg seek.
        staged_hls = None
        # Completed HLS segments can survive cancellation and be reused if
        # and only if the signed manifest remains identical on the next try.
        segment_cache_dir = target.parent / f".{target.stem}.hls-cache"
        working_url = str(url)
        if (start is None and urlsplit(working_url).scheme == "https"
                and bool(getattr(self, "runtime_hls_parallel_enabled", False))):
            staged_hls = tempfile.TemporaryDirectory(prefix=".akniga-hls-", dir=str(target.parent))
            try:
                last_reported = [0.0]
                parallel_started = time.monotonic()
                resumed = [0]
                def parallel_resumed(reused, _total):
                    resumed[0] = reused
                def parallel_progress(done, count, transferred):
                    self._check_cancel()
                    now = time.monotonic()
                    if now - last_reported[0] > 0.4 or done == count:
                        pct = 70.0 * done / count
                        self.set_progress(progress_offset + progress_span * pct / 100.0)
                        elapsed = max(0.01, now - parallel_started)
                        avg_speed = transferred / elapsed
                        restored = f", из кэша {resumed[0]}" if resumed[0] else ""
                        self.set_status(
                            f"HLS: готово {done} из {count} сегментов{restored}; "
                            f"по сети {fmt_size(transferred)}, {fmt_size(avg_speed)}/с"
                        )
                        if transferred and callable(getattr(self, "record_transfer_metrics", None)):
                            self.record_transfer_metrics(avg_speed, workers)
                        last_reported[0] = now
                mode = str(getattr(self, "runtime_segment_count", "auto") or "auto")
                try:
                    workers = 6 if mode == "auto" else max(1, min(8, int(mode)))
                except (ValueError, TypeError):
                    workers = 6
                limit_mb = float(getattr(self, "runtime_bandwidth_limit", 0.0) or 0.0)
                limiter = BandwidthLimiter(limit_mb * 1024 * 1024) if limit_mb > 0 else None
                throttle = None
                if limiter is not None:
                    throttle = lambda n: limiter.consume(n, getattr(self, "cancel_event", None))
                candidate = stage_hls_vod(
                    working_url, Path(staged_hls.name), referer=referer,
                    user_agent=USER_AGENT, check_cancel=self._check_cancel,
                    on_progress=parallel_progress, max_workers=workers,
                    throttle=throttle, segment_cache_dir=segment_cache_dir,
                    on_resume=parallel_resumed,
                )
                if candidate is not None:
                    working_url = str(candidate)
                    if resumed[0]:
                        self.log(f"HLS: восстановлено {resumed[0]} готовых сегментов из кэша.")
                    self.log("HLS: сегменты загружены параллельно, собираю аудио локально.")
                else:
                    staged_hls.cleanup()
                    staged_hls = None
            except Cancelled:
                staged_hls.cleanup()
                unlink_with_retry(temp, missing_ok=True)
                raise
            except Exception as concurrent_exc:
                staged_hls.cleanup()
                staged_hls = None
                app_logger.debug("HLS parallel fallback, exception class: %s", type(concurrent_exc).__name__)
                self.log("HLS: параллельная загрузка недоступна; пробую обычный FFmpeg-поток.")
        progress_seconds = {"value": 0.0, "speed": ""}
        proc = None
        title = chapter_label or "HLS-аудиопоток"
        is_parallel = working_url != str(url)
        last_update = 0.0
        self.set_status(f"Получаю {title} через FFmpeg…")
        try:
            source_candidates = ([working_url, str(url)] if is_parallel else [str(url)])
            for candidate_number, candidate_url in enumerate(source_candidates):
                working_url = candidate_url
                is_parallel = candidate_number == 0 and len(source_candidates) > 1
                if candidate_number:
                    self.log("HLS: локальная сборка не удалась; повторяю через обычный FFmpeg-поток.")
                try:
                    for use_copy in ([True, False] if allow_copy else [False]):
                        self._check_cancel()
                        # Same uniquely owned staging path; not a shared .part.
                        progress_seconds.update(value=0.0, speed="")
                        with tempfile.TemporaryFile(mode="w+b") as err_file:
                            proc = subprocess.Popen(
                                command(use_copy), stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=err_file, shell=False,
                                **hidden_subprocess_kwargs(),
                            )
                            self._register_active_subprocess(proc)
                            def consume_progress():
                                stream = getattr(proc, "stdout", None)
                                if stream is None:
                                    return
                                try:
                                    for raw in stream:
                                        if b"=" not in raw:
                                            continue
                                        key, value = raw.decode("utf-8", "replace").strip().split("=", 1)
                                        if key in ("out_time_us", "out_time_ms"):
                                            try:
                                                progress_seconds["value"] = max(0.0, int(value) / 1_000_000)
                                            except ValueError:
                                                pass
                                        elif key == "speed":
                                            progress_seconds["speed"] = value.strip()
                                except (OSError, ValueError):
                                    pass
                                finally:
                                    try:
                                        stream.close()
                                    except OSError:
                                        pass
                            consumer = None
                            if getattr(proc, "stdout", None) is not None:
                                consumer = threading.Thread(target=consume_progress, daemon=True)
                                consumer.start()
                            try:
                                while proc.poll() is None:
                                    self._check_cancel()
                                    now = time.monotonic()
                                    if now - last_update >= 0.7:
                                        seconds = progress_seconds["value"]
                                        if expected_duration and expected_duration > 0:
                                            pct = min(99.5, seconds * 100.0 / expected_duration)
                                            self.set_progress(progress_offset + progress_span * (70.0 + pct * 0.30 if is_parallel else pct) / 100.0)
                                            state = f"{pct:.0f}% ({fmt_time(seconds)} / {fmt_time(expected_duration)})"
                                        else:
                                            state = f"обработано {fmt_time(seconds)}"
                                        speed = progress_seconds["speed"]
                                        self.set_status(
                                            f"HLS {title}: {state}"
                                            + (f", обработка {speed}" if speed else "")
                                        )
                                        last_update = now
                                    try:
                                        proc.wait(timeout=0.2)
                                    except subprocess.TimeoutExpired:
                                        pass
                                if consumer is not None:
                                    consumer.join(timeout=1.0)
                                self._check_cancel()
                                if proc.returncode == 0 and temp.exists() and temp.stat().st_size:
                                    # FFmpeg can exit 0 for a prematurely ended HLS
                                    # playlist. Do not replace a complete existing
                                    # source with a short, seemingly valid MP3.
                                    # The downloader's existing post-download
                                    # timeline verification remains in place too.
                                    if expected_duration and expected_duration > 0:
                                        probe = getattr(self, "_probe_duration", None)
                                        actual = probe(temp) if callable(probe) else None
                                        if actual is not None and (
                                            float(actual) + max(8.0, float(expected_duration) * 0.01)
                                            < float(expected_duration)
                                        ):
                                            raise RuntimeError(
                                                "HLS: получен неполный аудиофайл; "
                                                "попытка не будет сохранена."
                                            )
                                    replace_with_retry(temp, target)
                                    # Complete verified MP3 supersedes staged
                                    # segments. On cancellation/failure keep them.
                                    if segment_cache_dir.is_dir():
                                        try:
                                            shutil.rmtree(segment_cache_dir)
                                        except OSError:
                                            pass
                                    progress_cb = getattr(self, "set_progress", None)
                                    if callable(progress_cb):
                                        progress_cb(progress_offset + progress_span)
                                    return target
                                err_file.seek(0)
                                detail = err_file.read()[-4000:].decode("utf-8", "replace")
                                if use_copy and any(token in detail.lower() for token in (
                                    "not supported in container", "codec not currently supported",
                                    "invalid audio stream", "could not write header",
                                    "codec type or id mismatches", "unsupported codec",
                                )):
                                    self.log("HLS: кодек не подходит для прямого MP3-копирования; перекодирую один раз.")
                                    continue
                                raise RuntimeError("FFmpeg не смог прочитать HLS: " + (detail.strip() or str(proc.returncode)))
                            finally:
                                if proc.poll() is None:
                                    proc.kill()
                                    proc.wait()
                                if consumer is not None and consumer.is_alive():
                                    consumer.join(timeout=1.0)
                                self._unregister_active_subprocess(proc)
                    raise RuntimeError("HLS: исходный кодек нельзя сохранить в MP3 без преобразования.")
                except RuntimeError:
                    if candidate_number + 1 == len(source_candidates):
                        raise
                    # Do not keep a broken output when using the remote fallback.
                    unlink_with_retry(temp, missing_ok=True)
        finally:
            try:
                unlink_with_retry(temp, missing_ok=True)
            except OSError as cleanup_exc:
                app_logger.warning("Failed cleaning HLS temp %s: %s", temp, cleanup_exc)
            if staged_hls is not None:
                staged_hls.cleanup()
            if callable(getattr(self, "record_transfer_metrics", None)):
                self.record_transfer_metrics(0, 0)

    def _download_hls_to_mp3(self, url, target, referer):
        expected = (getattr(self, "_hls_expected_durations", None) or {}).get(str(url))
        return NetworkDownloadMixin._run_hls_ffmpeg(
            self, url, target, referer, expected_duration=expected,
        )

    def _download_hls_chapter(self, book, track, *, chapter_number=1, total_chapters=1):
        """Seek and decode one selected chapter, without downloading whole book."""
        start = float(track.start)
        end = float(track.end)
        if start < 0 or end <= start:
            raise ValueError("Некорректные временные границы главы.")
        url = str(track.file or "")
        if not urlsplit(url).path.casefold().endswith(".m3u8"):
            raise ValueError("Источник главы не является HLS.")
        dest = self._track_path(book, track)
        return self._run_hls_ffmpeg(
            url, dest, book.url, start=start, duration=end - start,
            expected_duration=end - start,
            chapter_label=f"главу {chapter_number}/{total_chapters}",
            progress_offset=(chapter_number - 1) * 100.0 / total_chapters,
            progress_span=100.0 / total_chapters,
        )

    def _download_with_resume(self, url, target, referer):
        """Resume-capable download with adaptive HTTP Range chunking."""
        if urlsplit(str(url)).path.casefold().endswith(".m3u8"):
            return self._download_hls_to_mp3(url, target, referer)
        target = Path(target)
        part = target.with_name(target.name + ".part")
        has_segments = bool(_segment_files(part))
        supports, total = self._range_info(url, referer)
        segment_count = self._choose_segment_count(total)
        threshold_mb = int(getattr(self, "runtime_segment_threshold_mb", 16) or 16)

        # An existing ordinary .part continues in the single-stream resume path.
        # Existing Range chunks continue through the Range path.
        if segment_count > 1 and supports and total >= threshold_mb * 1024 * 1024 and (not part.exists() or has_segments):
            try:
                return self._download_segmented(url, target, referer, total, segment_count)
            except RangeUnsupported as e:
                self.log(f"Range недоступен, переключаюсь на обычную загрузку: {e}")
                # A segmented attempt never owns the ordinary ``.part`` file.
                # If one exists here, it is stale state from an older single-
                # stream attempt and must not be resumed against a server that
                # has just rejected Range semantics.
                try:
                    unlink_with_retry(part, missing_ok=True)
                except OSError as cleanup_exc:
                    raise RuntimeError(
                        f"Не удалось удалить устаревший временный файл {part.name}: {cleanup_exc}"
                    ) from cleanup_exc
            except Cancelled:
                raise

        return self._download_single(url, target, referer)


__all__ = ["NetworkDownloadMixin", "BandwidthLimiter", "AdaptiveRangeController", "SlidingSpeedMeter"]
