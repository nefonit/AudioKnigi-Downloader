from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import (
    DEFAULT_OUTPUT, SETTINGS_FILE, UI_SCALE_MIGRATION_KEY, load_json,
    migrate_ui_scale_settings, save_json, safe_float, safe_int,
    safe_normalization_mode,
)

CURRENT_SETTINGS_VERSION = 2

DEFAULT_SETTINGS: dict[str, Any] = {
    "settings_version": CURRENT_SETTINGS_VERSION,
    "language": "ru",
    "ui_mode": "easy",
    "output_dir": str(DEFAULT_OUTPUT),
    "theme": "system",
    "scale": 100,
    "large_mode": False,
    "hide_source": False,
    "minimize_to_tray": True,
    "clipboard_auto": True,
    "quality_preset": "standard",
    "naming_mode": "number",
    "audio_preset": "copy",
    "normalization_mode": "off",
    "embed_tags": True,
    "save_sidecars": True,
    "delete_source": True,
    "playwright_fallback_enabled": True,
    "parallel_single_source": False,
    "segment_count": "auto",
    "segment_threshold_mb": 16,
    "auto_chunk_min_kbytes_per_sec": 256,
    "bandwidth_limit": 0.0,
    "use_templates": False,
    "folder_template": "{Book_Title}",
    "track_template": "{Track_Number}.mp3",
    "abs_enabled": False,
    "abs_url": "",
    "abs_api_key": "",
    "abs_library_id": "",
    "event_sounds_enabled": True,
    "event_sound_volume": 100,
    "player_volume": 80,
    "player_rate": 1.0,
    "first_run_complete": False,
    "geometry": "",
}


def migrate_settings(payload: Mapping[str, Any] | None) -> tuple[dict[str, Any], bool]:
    """Return a normalized settings mapping and whether persistence is needed.

    Migrations are intentionally idempotent. Unknown keys are preserved so old
    installations and future plugins can coexist with this schema.
    """
    raw = dict(payload or {})
    original = dict(raw)

    # v1 -> v2: the historic key said "kbps" even though the UI and runtime
    # consistently used KB/s. Keep reading the old key, but persist the precise
    # name from now on.
    if "auto_chunk_min_kbytes_per_sec" not in raw and "auto_chunk_min_kbps" in raw:
        raw["auto_chunk_min_kbytes_per_sec"] = raw.get("auto_chunk_min_kbps")
    raw.pop("auto_chunk_min_kbps", None)

    # Older 4.x profiles used a boolean ``normalize_audio`` switch before the
    # explicit off/single/two_pass mode was introduced. Preserve that user
    # choice as the legacy one-pass mode when no canonical mode exists yet.
    if "normalization_mode" not in raw and bool(raw.get("normalize_audio", False)):
        raw["normalization_mode"] = "single"

    raw["settings_version"] = CURRENT_SETTINGS_VERSION

    for key, default in DEFAULT_SETTINGS.items():
        if key not in raw or raw[key] is None:
            raw[key] = default

    # Type/range normalization lives in one place rather than being duplicated
    # across the GUI and download engine.
    raw["scale"] = max(80, min(200, safe_int(raw.get("scale"), 100)))
    raw["event_sound_volume"] = max(0, min(100, safe_int(raw.get("event_sound_volume"), 100)))
    raw["player_volume"] = max(0, min(100, safe_int(raw.get("player_volume"), 80)))
    raw["player_rate"] = max(0.5, min(3.0, safe_float(raw.get("player_rate"), 1.0)))
    raw["segment_threshold_mb"] = max(1, safe_int(raw.get("segment_threshold_mb"), 16))
    raw["auto_chunk_min_kbytes_per_sec"] = max(1, safe_int(raw.get("auto_chunk_min_kbytes_per_sec"), 256))
    raw["bandwidth_limit"] = max(0.0, safe_float(raw.get("bandwidth_limit"), 0.0))
    raw["segment_count"] = str(raw.get("segment_count") or "auto")
    raw["normalization_mode"] = safe_normalization_mode(raw.get("normalization_mode"))
    raw["folder_template"] = str(raw.get("folder_template") or "{Book_Title}")
    raw["track_template"] = str(raw.get("track_template") or "{Track_Number}.mp3")
    raw["output_dir"] = str(raw.get("output_dir") or DEFAULT_OUTPUT)

    raw, ui_migrated = migrate_ui_scale_settings(raw)
    return raw, ui_migrated or raw != original


def normalize_settings(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    return migrate_settings(payload)[0]


@dataclass(eq=False)
class AppSettings(MutableMapping[str, Any]):
    """Dictionary-compatible settings object with a versioned schema."""

    _data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "AppSettings":
        return cls(normalize_settings(payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


def load_app_settings(path: Path = SETTINGS_FILE) -> AppSettings:
    payload = load_json(path, {})
    if not isinstance(payload, dict):
        payload = {}
    normalized, changed = migrate_settings(payload)
    if changed:
        save_json(path, normalized)
    return AppSettings(normalized)


def save_app_settings(settings: Mapping[str, Any], path: Path = SETTINGS_FILE) -> bool:
    # A save represents current user intent, not an old profile being loaded.
    # Mark the legacy 125% migration as completed before normalization so an
    # explicitly selected 125% value in a newly-created mapping is not reset.
    payload = dict(settings or {})
    payload.setdefault(UI_SCALE_MIGRATION_KEY, True)
    normalized = normalize_settings(payload)
    return bool(save_json(path, normalized))
