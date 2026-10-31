"""Recover queue/history lists from a last-known-good local snapshot.

Only invalid JSON triggers recovery; a valid empty list is authoritative.
Snapshots are atomically saved and never replace the primary file on read.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..core import save_json
from ..logging_utils import app_logger


def last_good_path(path: Path) -> Path:
    path = Path(path)
    return path.with_name(f"{path.stem}.lastgood.json")


def _parse_list(raw: bytes) -> list:
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, list):
        raise ValueError("Stored state must be a list")
    return value


def _preserve_corrupt_bytes(path: Path, raw: bytes) -> None:
    digest = hashlib.sha256(raw).hexdigest()[:12]
    recovery = path.with_name(f"{path.stem}.corrupt-{digest}.json")
    if recovery.exists():
        return
    try:
        recovery.write_bytes(raw)
    except OSError:
        app_logger.warning("STATE | event=preserve_corrupt_failed | file=%s", path.name)


def load_recoverable_list(path: Path) -> list:
    """Prefer valid primary JSON; use the mirror only for a corrupted file."""
    path = Path(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []
    except OSError:
        app_logger.warning("STATE | event=read_failed | file=%s", path.name)
        return []

    try:
        return _parse_list(raw)
    except (ValueError, UnicodeError, TypeError) as exc:
        app_logger.warning("STATE | event=corrupt_json | file=%s | reason=%s", path.name, type(exc).__name__)
        _preserve_corrupt_bytes(path, raw)

    mirror = last_good_path(path)
    try:
        recovered = _parse_list(mirror.read_bytes())
    except (OSError, ValueError, UnicodeError, TypeError):
        app_logger.warning("STATE | event=no_valid_snapshot | file=%s", path.name)
        return []
    app_logger.warning("STATE | event=recovered_from_snapshot | file=%s | count=%s", path.name, len(recovered))
    return recovered


def save_recoverable_list(path: Path, rows: list) -> bool:
    """Commit the main JSON first; then refresh a best-effort valid snapshot."""
    path = Path(path)
    if not save_json(path, rows):
        return False
    try:
        if not save_json(last_good_path(path), rows):
            app_logger.warning("STATE | event=snapshot_write_failed | file=%s", path.name)
    except OSError:
        app_logger.warning("STATE | event=snapshot_write_failed | file=%s", path.name)
    return True
