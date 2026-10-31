"""Conservative concurrent fetch of ordinary HLS VOD segments.

A network-only acceleration for authorized media: this does not interpret
secret site tokens, alter access permissions, or implement an HLS decryptor.
If the playlist is unfamiliar, return None and let standard FFmpeg handle it.
The original URLs are never stored in the user's book directory.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import ip_address
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import re
import threading

import requests
from ..core import get_http_session

_KEY_URI_RE = re.compile(r'URI="([^"]+)"', re.I)
_UNSUPPORTED = (
    "#EXT-X-BYTERANGE", "#EXT-X-MAP", "#EXT-X-PART", "#EXT-X-PRELOAD-HINT",
    "#EXT-X-STREAM-INF", "#EXT-X-I-FRAME-STREAM-INF", "#EXT-X-SESSION-KEY",
    "#EXT-X-I-FRAMES-ONLY", "#EXT-X-SKIP",
)


def _safe_http_url(url: str, *, allow_local_http: bool = False) -> bool:
    """Do not let media playlists point a downloader to local/internal services."""
    try:
        parts = urlsplit(url)
        if parts.scheme != "https" and not (allow_local_http and parts.scheme == "http"):
            return False
        if not parts.hostname or parts.username or parts.password:
            return False
        host = parts.hostname.lower().rstrip(".")
        if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal")):
            return bool(allow_local_http and host == "localhost")
        try:
            addr = ip_address(host)
            if not addr.is_global and not allow_local_http:
                return False
        except ValueError:
            pass
        return True
    except (ValueError, TypeError):
        return False



def _open_checked_response(url: str, headers, *, allow_local_http: bool = False):
    # A signed CDN URL may redirect. Inspect every redirect *before* sending
    # another request, so playlists cannot redirect the downloader to intranet.
    current = url
    for _ in range(5):
        if not _safe_http_url(current, allow_local_http=allow_local_http):
            raise ValueError("Недопустимый адрес HLS-ресурса")
        response = get_http_session().get(current, headers=headers, timeout=(10, 30),
                                stream=True, allow_redirects=False)
        if response.is_redirect:
            target = response.headers.get("Location")
            response.close()
            if not target:
                raise ValueError("HLS: перенаправление без адреса")
            current = urljoin(current, target)
            continue
        response.raise_for_status()
        return response
    raise ValueError("HLS: слишком много перенаправлений")


def _get_bytes(url: str, headers: dict[str, str], check_cancel,
               *, allow_local_http: bool = False, max_length: int | None = None) -> bytes:
    if not _safe_http_url(url, allow_local_http=allow_local_http):
        raise ValueError("Недопустимый адрес HLS-ресурса")
    check_cancel()
    with _open_checked_response(url, headers, allow_local_http=allow_local_http) as response:
        result = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            check_cancel()
            result.extend(chunk)
            if max_length and len(result) > max_length:
                raise ValueError("Превышен размер файла HLS")
    return bytes(result)


def _download_segment(index: int, url: str, dest: Path, headers,
                      check_cancel, stop_event: threading.Event,
                      *, allow_local_http: bool = False, throttle=None) -> tuple[int, int]:
    if not _safe_http_url(url, allow_local_http=allow_local_http):
        raise ValueError("Недопустимый адрес HLS-сегмента")
    for attempt in range(3):
        if stop_event.is_set():
            raise RuntimeError("Загрузка сегментов остановлена")
        check_cancel()
        try:
            with _open_checked_response(url, headers, allow_local_http=allow_local_http) as response:
                length = 0
                # Check the expected HTTP body size when the origin supplies
                # Content-Length. A short, clean EOF must not become a cached
                # "complete" segment. Compressed/chunked bodies are excluded:
                # requests may transparently decode them.
                response_headers = getattr(response, "headers", {}) or {}
                content_length = response_headers.get("Content-Length", "")
                content_encoding = str(response_headers.get("Content-Encoding", "") or "").lower()
                transfer_encoding = str(response_headers.get("Transfer-Encoding", "") or "").lower()
                expected_length = None
                if not content_encoding or content_encoding == "identity":
                    if "chunked" not in transfer_encoding:
                        try:
                            expected_length = int(content_length)
                        except (TypeError, ValueError):
                            pass
                with dest.open("wb") as out:
                    for chunk in response.iter_content(chunk_size=128 * 1024):
                        if stop_event.is_set():
                            raise RuntimeError("Загрузка сегментов остановлена")
                        check_cancel()
                        if throttle is not None:
                            throttle(len(chunk))
                        out.write(chunk)
                        length += len(chunk)
                if length <= 0:
                    raise IOError("Пустой HLS-сегмент")
                if expected_length is not None and expected_length >= 0 and length != expected_length:
                    raise IOError("Неполный HLS-сегмент: длина HTTP-ответа не совпала")
                return index, length
        except (requests.RequestException, OSError, IOError):
            dest.unlink(missing_ok=True)
            if attempt == 2 or stop_event.is_set():
                raise
            stop_event.wait(0.25 * (attempt + 1))
    raise RuntimeError("Сегмент не получен")


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reusable_segment(cache: Path, stage: Path) -> int | None:
    """Cache data are accepted only with a matching full SHA-256 checksum."""
    sidecar = cache.with_suffix(cache.suffix + ".sha256")
    try:
        if cache.is_symlink() or sidecar.is_symlink() or not cache.is_file() or not sidecar.is_file():
            return None
        expected = sidecar.read_text(encoding="ascii").strip()
        if not re.fullmatch(r"[a-f0-9]{64}", expected):
            return None
        if cache.stat().st_size <= 0 or _checksum(cache) != expected:
            return None
        if stage.exists():
            stage.unlink()
        try:
            os.link(cache, stage)
        except OSError:
            shutil.copyfile(cache, stage)
        return stage.stat().st_size
    except (OSError, ValueError):
        return None


def _persist_segment(stage: Path, cache: Path) -> None:
    """Publish completed segments atomically; never cache partial downloads."""
    cache.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=cache.parent, prefix=".seg-", delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        # On the same filesystem an OS hardlink avoids copying large media
        # segments a second time. NTFS/filesystems without hardlinks fall back
        # to a regular copy; FFmpeg only reads the staged file.
        temporary.unlink()
        try:
            os.link(stage, temporary)
        except OSError:
            shutil.copyfile(stage, temporary)
        checksum = _checksum(temporary)
        if temporary.stat().st_size <= 0:
            return
        os.replace(temporary, cache)
        # Sidecar is written last, so a crash cannot validate a partial file.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="ascii", dir=cache.parent,
            prefix=".sum-", delete=False,
        ) as sidecar_file:
            side_temp = Path(sidecar_file.name)
            sidecar_file.write(checksum)
        try:
            os.replace(side_temp, cache.with_suffix(cache.suffix + ".sha256"))
        finally:
            side_temp.unlink(missing_ok=True)
    finally:
        temporary.unlink(missing_ok=True)


def stage_hls_vod(url: str, staging_dir: Path, *, referer: str,
                  user_agent: str, check_cancel, on_progress,
                  max_workers: int = 6, allow_local_http: bool = False, throttle=None,
                  segment_cache_dir: Path | None = None, on_resume=None) -> Path | None:
    """Fetch a supported HLS VOD concurrently and emit a *local* .m3u8.

    No segmented download starts until the full manifest validates.
    ``None`` means unsupported playlist, not a truncated success.
    The caller exclusively owns and removes staging_dir.
    """
    if not _safe_http_url(url, allow_local_http=allow_local_http):
        return None
    staging_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": user_agent}
    if referer:
        headers["Referer"] = referer
    body = _get_bytes(url, headers, check_cancel, allow_local_http=allow_local_http, max_length=2_000_000)
    try:
        playlist = body.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    lines = playlist.splitlines()
    if not lines or lines[0].strip() != "#EXTM3U" or "#EXT-X-ENDLIST" not in playlist:
        return None
    for line in lines:
        if line.strip().upper().startswith(_UNSUPPORTED):
            return None

    updated = []
    segments: list[tuple[int, str, Path]] = []
    keys: dict[str, str] = {}
    awaiting_segment = False
    for line in lines:
        value = line.strip()
        if value.startswith("#EXT-X-KEY:"):
            if "METHOD=NONE" in value.upper():
                updated.append(value)
                continue
            if "METHOD=AES-128" not in value.upper():
                return None
            match = _KEY_URI_RE.search(value)
            if not match:
                return None
            key_url = urljoin(url, match.group(1))
            if not _safe_http_url(key_url, allow_local_http=allow_local_http):
                return None
            if key_url not in keys:
                keys[key_url] = f"key{len(keys):03d}.key"
            updated.append(value[:match.start(1)] + keys[key_url] + value[match.end(1):])
            continue
        if value.startswith("#EXTINF:"):
            awaiting_segment = True
            updated.append(value)
            continue
        if value and not value.startswith("#"):
            if not awaiting_segment:
                return None
            item_url = urljoin(url, value)
            if not _safe_http_url(item_url, allow_local_http=allow_local_http):
                return None
            index = len(segments)
            suffix = Path(urlsplit(item_url).path).suffix.lower()
            if suffix not in (".ts", ".aac", ".mp3", ".m4s"):
                suffix = ".ts"
            local_name = f"seq{index:06d}{suffix}"
            segments.append((index, item_url, staging_dir / local_name))
            updated.append(local_name)
            awaiting_segment = False
        else:
            updated.append(value)
    if awaiting_segment or not segments or len(segments) > 25000:
        return None

    # The fingerprint includes both the manifest bytes and its full, possibly
    # expiring URL. Never write source URLs or authentication tokens to disk.
    # If the signed manifest changes, no segments from the old one are reused.
    cache_subdir = None
    if segment_cache_dir is not None:
        fingerprint = hashlib.sha256(url.encode("utf-8") + b"\0" + body).hexdigest()
        cache_subdir = Path(segment_cache_dir) / fingerprint

    for remote_key, local_name in keys.items():
        raw = _get_bytes(remote_key, headers, check_cancel, allow_local_http=allow_local_http, max_length=128)
        if len(raw) != 16:
            raise ValueError("Некорректный AES-128 HLS-ключ")
        (staging_dir / local_name).write_bytes(raw)
    stop_event = threading.Event()
    finished = 0
    # Count only fresh network traffic in the throughput figure. Cached bytes
    # are completed work but were not transferred over the network this run.
    downloaded_bytes = 0
    reused_count = 0

    def fetch_or_reuse(index, remote, dest):
        if stop_event.is_set():
            raise RuntimeError("Загрузка сегментов остановлена")
        check_cancel()
        if cache_subdir is not None:
            cache_path = cache_subdir / dest.name
            cached_size = _reusable_segment(cache_path, dest)
            if cached_size is not None:
                check_cancel()
                return index, cached_size, True
        index, size = _download_segment(
            index, remote, dest, headers, check_cancel, stop_event,
            allow_local_http=allow_local_http, throttle=throttle,
        )
        if cache_subdir is not None:
            try:
                _persist_segment(dest, cache_subdir / dest.name)
            except OSError:
                # The cache is an optimization; inability to persist must not
                # invalidate a correctly downloaded segment.
                pass
        return index, size, False

    with ThreadPoolExecutor(max_workers=max(1, min(12, int(max_workers)))) as pool:
        futures = [pool.submit(fetch_or_reuse, i, remote, dest)
                   for i, remote, dest in segments]
        try:
            for task in as_completed(futures):
                check_cancel()
                _index, size, reused = task.result()
                finished += 1
                if reused:
                    reused_count += 1
                    if on_resume is not None:
                        on_resume(reused_count, len(segments))
                else:
                    downloaded_bytes += size
                on_progress(finished, len(segments), downloaded_bytes)
        except BaseException:
            # Set this while the pool is still open, rather than after its
            # context manager has already waited for all queued downloads.
            # The running response will stop at the next streamed chunk.
            stop_event.set()
            for future in futures:
                future.cancel()
            raise
    dest = staging_dir / "media.m3u8"
    dest.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return dest
