from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator
from collections.abc import Mapping


@lru_cache(maxsize=128)
def _dataclass_field_names(cls: type) -> tuple[str, ...]:
    try:
        return tuple(item.name for item in fields(cls))
    except TypeError:
        # MappingDataclass itself is intentionally not a dataclass. Returning an
        # empty field set keeps the adapter safe for intermediate subclasses too.
        return ()


class MappingDataclass(Mapping[str, Any]):
    """Read-compatible mapping adapter for typed dataclasses.

    Runtime code should prefer attribute access. Mapping access remains available
    for old manifests/tests, but only real dataclass fields are exposed. Class
    methods/properties such as ``to_dict`` are intentionally *not* mapping keys.
    """

    __slots__ = ()

    def _field_names(self):
        return _dataclass_field_names(type(self))

    def __getitem__(self, key: str) -> Any:
        if key not in self._field_names():
            raise KeyError(key)
        return getattr(self, key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._field_names())

    def __len__(self) -> int:
        return len(self._field_names())

    def get(self, key: str, default: Any = None) -> Any:
        if key not in self._field_names():
            return default
        return getattr(self, key)

    @staticmethod
    def _plain_value(value: Any) -> Any:
        """Convert nested model values without deepcopying native image objects.

        ``dataclasses.asdict`` deep-copies every field, which is unsafe for
        Native GUI/image objects occasionally stored in ``cover_cache``.
        Byte cover payloads remain intact; non-serializable native image objects
        are represented as ``None`` instead of being copied.
        """
        if isinstance(value, MappingDataclass):
            return value.to_dict()
        if is_dataclass(value) and not isinstance(value, type):
            return {f.name: MappingDataclass._plain_value(getattr(value, f.name)) for f in fields(value)}
        if isinstance(value, list):
            return [MappingDataclass._plain_value(v) for v in value]
        if isinstance(value, tuple):
            return tuple(MappingDataclass._plain_value(v) for v in value)
        if isinstance(value, (set, frozenset)):
            return [MappingDataclass._plain_value(v) for v in value]
        if isinstance(value, dict):
            return {k: MappingDataclass._plain_value(v) for k, v in value.items()}
        if isinstance(value, (str, int, float, bool, bytes, type(None))):
            return value
        if isinstance(value, (bytearray, memoryview)):
            return bytes(value)
        # Paths and similar harmless values are useful in diagnostics/manifests.
        if isinstance(value, Path):
            return str(value)
        # GUI/image/native objects are deliberately not copied.
        return None

    def to_dict(self) -> dict[str, Any]:
        if not is_dataclass(self):
            return {}
        return {f.name: self._plain_value(getattr(self, f.name)) for f in fields(self)}


def normalize_cover_cache(value: Any) -> tuple[bytes, str] | None:
    """Return the canonical ``(image_bytes, mime_type)`` cover-cache form.

    Older queue snapshots may contain bare bytes while network analysis returns
    ``(bytes, mime)``.  Normalizing at the model boundary keeps the downloader,
    Qt preview and queue persistence consistent.
    """
    data = None
    mime = "image/jpeg"
    if isinstance(value, (tuple, list)) and value:
        data = value[0]
        if len(value) > 1 and value[1]:
            mime = str(value[1])
    elif isinstance(value, (bytes, bytearray, memoryview)):
        data = value
    if not isinstance(data, (bytes, bytearray, memoryview)):
        return None
    payload = bytes(data)
    if not payload:
        return None
    mime = str(mime or "image/jpeg").split(";", 1)[0].strip() or "image/jpeg"
    return payload, mime


def cover_cache_bytes(value: Any) -> bytes | None:
    normalized = normalize_cover_cache(value)
    return normalized[0] if normalized else None

TRACK_STATUS_MISSING = "missing"
TRACK_STATUS_PRESENT = "present"
TRACK_STATUS_READY = "ready"
TRACK_STATUS_DAMAGED = "damaged"
_TRACK_STATUS_ALIASES = {
    "": TRACK_STATUS_MISSING,
    "нет": TRACK_STATUS_MISSING,
    "missing": TRACK_STATUS_MISSING,
    "есть": TRACK_STATUS_PRESENT,
    "present": TRACK_STATUS_PRESENT,
    "готово": TRACK_STATUS_READY,
    "ready": TRACK_STATUS_READY,
    "повреждён": TRACK_STATUS_DAMAGED,
    "поврежден": TRACK_STATUS_DAMAGED,
    "damaged": TRACK_STATUS_DAMAGED,
    # Localized UI values can appear in old queue/history snapshots.  Keep the
    # model language-neutral by normalizing them back to canonical statuses.
    "немає": TRACK_STATUS_MISSING,
    "fehlt": TRACK_STATUS_MISSING,
    "є": TRACK_STATUS_PRESENT,
    "vorhanden": TRACK_STATUS_PRESENT,
    "fertig": TRACK_STATUS_READY,
    "пошкоджено": TRACK_STATUS_DAMAGED,
    "beschädigt": TRACK_STATUS_DAMAGED,
}

def normalize_track_status(value: Any) -> str:
    key = str(value or "").strip().casefold()
    return _TRACK_STATUS_ALIASES.get(key, key or TRACK_STATUS_MISSING)



@dataclass(slots=True)
class Track(MappingDataclass):
    index: int
    title: str
    file: str
    start: float | int | None = None
    end: float | int | None = None
    duration: float | None = None
    selected: bool = True
    local_status: str = TRACK_STATUS_MISSING
    actual_duration: float | None = None
    local_path: str = ""
    fallback_file: str = ""

    def __post_init__(self) -> None:
        self.local_status = normalize_track_status(self.local_status)


@dataclass(slots=True)
class NarrationVariant(MappingDataclass):
    url: str
    narrator: str = ""
    title: str = ""
    current: bool = False
    available: bool | None = None


@dataclass(slots=True)
class Book(MappingDataclass):
    url: str
    title: str
    author: str = ""
    narrator: str = ""
    description: str = ""
    genre: str = ""
    year: str = ""
    cover_url: str = ""
    playlist_url: str = ""
    tracks: list[Track] = field(default_factory=list)
    narration_variants: list[NarrationVariant] = field(default_factory=list)
    restricted: bool = False
    remote_size: int = 0
    cover_cache: Any = None


@dataclass(slots=True)
class QueueItem(MappingDataclass):
    url: str
    title: str = "—"
    status: str = "Ожидает"
    status_code: str = "pending"
    attempts: int = 0
    selected_indices: list[int] | None = None
    naming_mode: str = "number"
    audio_preset: str = "copy"
    normalization_mode: str = "off"
    normalize_audio: bool = False  # backwards compatibility with 4.3.x manifests
    last_error: str = ""
    transient: bool = False
    paused: bool = False
    status_before_pause: str = ""
    status_code_before_pause: str = ""
    priority: bool = False
    priority_restore_index: int | None = None
    cover_url: str = ""
    cover_cache: Any = None
    use_templates: bool = False
    folder_template: str = "{Book_Title}"
    track_template: str = "{Track_Number}.mp3"
    # Local completion snapshot for queue revalidation. These paths are
    # populated only after this queue item successfully finishes. They let a
    # later Start detect that the user deleted the downloaded book without a
    # network request or localized-status parsing.
    output_folder: str = ""
    completed_files: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SearchResult(MappingDataclass):
    title: str
    url: str
    source: str = "audioknigi.com.ua"
    author: str = ""
    narrator: str = ""
    variant_count: int = 1
    narration_variants: list[NarrationVariant] = field(default_factory=list)
    availability: str = ""
