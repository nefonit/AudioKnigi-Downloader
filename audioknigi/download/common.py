"""Small filesystem/subprocess helpers used by downloader subsystems."""
from __future__ import annotations
import os
import threading
import time
from pathlib import Path

def close_subprocess_pipes(proc) -> None:
    if proc is None:
        return
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(proc, name, None)
        if stream is None:
            continue
        try:
            stream.close()
        except Exception:
            pass

def _is_transient_windows_file_error(exc: OSError) -> bool:
    return isinstance(exc, PermissionError) or getattr(exc, "winerror", None) in {5, 32}

def replace_with_retry(source, target, *, attempts=5):
    """Replace ``target`` with ``source`` while tolerating short Windows AV locks."""
    source_path = Path(source)
    target_path = Path(target)
    for attempt in range(max(1, int(attempts))):
        try:
            source_path.replace(target_path)
            return target_path
        except OSError as exc:
            if attempt >= max(1, int(attempts)) - 1 or not _is_transient_windows_file_error(exc):
                raise
            time.sleep(0.025 * (2**attempt))
    return target_path

def unlink_with_retry(path, *, missing_ok=True, attempts=5):
    """Unlink a file with the same short sharing-violation retry policy."""
    target = Path(path)
    for attempt in range(max(1, int(attempts))):
        try:
            target.unlink(missing_ok=missing_ok)
            return True
        except FileNotFoundError:
            if missing_ok:
                return True
            raise
        except OSError as exc:
            if attempt >= max(1, int(attempts)) - 1 or not _is_transient_windows_file_error(exc):
                raise
            time.sleep(0.025 * (2**attempt))
    return False

def atomic_write_text(path, text, *, encoding="utf-8"):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.{os.getpid()}.{threading.get_ident()}.{time.monotonic_ns()}.tmp")
    try:
        temp.write_text(text, encoding=encoding)
        replace_with_retry(temp, target, attempts=4)
    finally:
        try:
            if temp.exists():
                unlink_with_retry(temp, missing_ok=True, attempts=2)
        except OSError:
            pass

def atomic_write_bytes(path, data):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.{os.getpid()}.{threading.get_ident()}.{time.monotonic_ns()}.tmp")
    try:
        temp.write_bytes(bytes(data or b""))
        replace_with_retry(temp, target, attempts=4)
    finally:
        try:
            if temp.exists():
                unlink_with_retry(temp, missing_ok=True, attempts=2)
        except OSError:
            pass

__all__ = [
    "close_subprocess_pipes", "atomic_write_bytes", "atomic_write_text", "replace_with_retry", "unlink_with_retry",
]
