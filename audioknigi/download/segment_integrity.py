"""Persistent SHA-256 checkpoints for segmented downloads.

Digests detect *local* file modifications since the last checkpoint; they
cannot authenticate a CDN response. Missing, stale or malformed checkpoints
are never treated as proof of valid previously downloaded bytes.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from pathlib import Path

from .common import atomic_write_text


def file_digest(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    with open(path, "rb") as source:
        while chunk := source.read(1024 * 1024):
            count += len(chunk)
            digest.update(chunk)
    return count, digest.hexdigest()


class SegmentChecksums:
    """Thread-safe, atomic checkpoints tied to one source/range geometry."""

    def __init__(self, path, signature):
        self.path = Path(path)
        self.signature = signature
        self.lock = threading.Lock()
        self.entries = {}
        try:
            stored = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                isinstance(stored, dict)
                and stored.get("version") == 1
                and stored.get("signature") == signature
                and isinstance(stored.get("segments"), dict)
            ):
                self.entries = stored["segments"]
        except (FileNotFoundError, OSError, ValueError, UnicodeError, TypeError):
            pass

    def _save(self):
        atomic_write_text(
            self.path,
            json.dumps(
                {"version": 1, "signature": self.signature, "segments": self.entries},
                sort_keys=True, ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def expected(self, path):
        entry = self.entries.get(Path(path).name)
        if not isinstance(entry, dict):
            return None
        size, sha = entry.get("size"), entry.get("sha256")
        if (
            isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
            or not isinstance(sha, str)
            or re.fullmatch(r"[a-f0-9]{64}", sha) is None
        ):
            return None
        return size, sha

    def matches(self, path) -> bool:
        expected = self.expected(path)
        if expected is None:
            return False
        try:
            return file_digest(Path(path)) == expected
        except OSError:
            return False

    def record(self, path):
        path = Path(path)
        size, sha = file_digest(path)
        with self.lock:
            self.entries[path.name] = {"size": size, "sha256": sha}
            self._save()

    def forget(self, path):
        with self.lock:
            if self.entries.pop(Path(path).name, None) is not None:
                self._save()


def copy_verified_segment(source, output, *, expected_size: int, expected_sha256: str, name: str):
    """Verify each byte *as copied*, before the assembled file can be renamed."""
    digest = hashlib.sha256()
    copied = 0
    while chunk := source.read(1024 * 1024):
        copied += len(chunk)
        if copied > expected_size:
            raise RuntimeError(f"Range-сегмент {name} увеличился во время сборки.")
        digest.update(chunk)
        output.write(chunk)
    if copied != expected_size or digest.hexdigest() != expected_sha256:
        raise RuntimeError(f"Нарушена контрольная сумма Range-сегмента {name}.")


__all__ = ["SegmentChecksums", "file_digest", "copy_verified_segment"]
