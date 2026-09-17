from __future__ import annotations

import threading
import time
from pathlib import Path

from ..core import PLAYER_POSITIONS_FILE, load_json, save_json

_POSITION_CACHE_MAX = 2000


class PlayerPositionStore:
    """GUI-independent resume-position storage used by the Qt player.

    The JSON schema and key normalization preserve compatibility with existing
    ``PlayerMixin`` so either frontend can continue a file last played by the
    other one.
    """

    def __init__(self, path: str | Path = PLAYER_POSITIONS_FILE) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        data = load_json(self.path, {})
        self._positions: dict[str, object] = data if isinstance(data, dict) else {}
        self._prune_locked()


    def _prune_locked(self) -> None:
        """Bound stale resume records; completed tracks are already removed eagerly."""
        overflow = len(self._positions) - _POSITION_CACHE_MAX
        if overflow <= 0:
            return
        ranked = sorted(
            self._positions.items(),
            key=lambda item: str(item[1].get("updated", "") if isinstance(item[1], dict) else ""),
        )
        for key, _value in ranked[:overflow]:
            self._positions.pop(key, None)

    @staticmethod
    def key(file_path: str | Path) -> str:
        try:
            return str(Path(file_path).resolve()).lower()
        except Exception:
            return str(file_path).lower()

    @staticmethod
    def _resume_guard_seconds(duration: float) -> float:
        """Ignore only a small edge region on short tracks; keep 3 s for normal chapters."""
        value = max(0.0, float(duration or 0.0))
        if value <= 0:
            return 3.0
        return min(3.0, max(0.25, value * 0.10))

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                key: dict(value) if isinstance(value, dict) else value
                for key, value in self._positions.items()
            }

    def reload(self) -> None:
        """Reload persisted positions after backup restore or external replacement."""
        data = load_json(self.path, {})
        with self._lock:
            self._positions = data if isinstance(data, dict) else {}
            self._prune_locked()

    def saved_seconds(self, file_path: str | Path, *, duration: float = 0.0) -> float:
        with self._lock:
            raw = self._positions.get(self.key(file_path), {})
            record = dict(raw) if isinstance(raw, dict) else {}
        try:
            position = max(0.0, float(record.get("position", 0.0) or 0.0))
        except (TypeError, ValueError):
            position = 0.0
        try:
            duration_value = max(0.0, float(duration or 0.0))
        except (TypeError, ValueError):
            duration_value = 0.0
        if duration_value <= 0:
            try:
                duration_value = max(0.0, float(record.get("duration", 0.0) or 0.0))
            except (TypeError, ValueError):
                duration_value = 0.0
        guard = self._resume_guard_seconds(duration_value)
        if position < guard:
            return 0.0
        if duration_value > 0 and position >= max(0.0, duration_value - guard):
            return 0.0
        return position

    def update(
        self,
        file_path: str | Path,
        position: float,
        duration: float = 0.0,
        *,
        persist: bool = True,
    ) -> bool:
        path = Path(file_path)
        try:
            position_value = max(0.0, float(position or 0.0))
        except (TypeError, ValueError):
            position_value = 0.0
        try:
            duration_value = max(0.0, float(duration or 0.0))
        except (TypeError, ValueError):
            duration_value = 0.0

        key = self.key(path)
        guard = self._resume_guard_seconds(duration_value)
        with self._lock:
            if (duration_value > 0 and position_value >= max(0.0, duration_value - guard)) or position_value < guard:
                self._positions.pop(key, None)
            else:
                self._positions[key] = {
                    "position": position_value,
                    "duration": duration_value,
                    "file": path.name,
                    "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                self._prune_locked()
            snapshot = {
                item_key: dict(value) if isinstance(value, dict) else value
                for item_key, value in self._positions.items()
            }
        return bool(save_json(self.path, snapshot)) if persist else True

    def clear(self, file_path: str | Path, *, persist: bool = True) -> bool:
        key = self.key(file_path)
        with self._lock:
            self._positions.pop(key, None)
            snapshot = {
                item_key: dict(value) if isinstance(value, dict) else value
                for item_key, value in self._positions.items()
            }
        return bool(save_json(self.path, snapshot)) if persist else True


__all__ = ["PlayerPositionStore"]
