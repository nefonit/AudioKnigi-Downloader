from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core import DEFAULT_OUTPUT, safe_int
from ..models import Book
from ..config.settings import normalize_settings


@dataclass(slots=True)
class DownloadRequest:
    """GUI-neutral description of one requested book download.

    The Qt frontend consumes this GUI-neutral contract through the shared
    download engine, keeping selected-track state explicit and testable.
    """

    book: Book
    selected_indices: list[int] | None
    output_dir: Path
    naming_mode: str = "number"
    audio_preset: str = "copy"
    normalization_mode: str = "off"
    use_templates: bool | None = None
    folder_template: str | None = None
    track_template: str | None = None

    @staticmethod
    def track_index(value) -> int:
        """Return a validated numeric track index from a Track, mapping or raw scalar."""
        if isinstance(value, (int, str)):
            raw = value
        elif isinstance(value, Mapping):
            raw = value.get("index", -1)
        else:
            raw = getattr(value, "index", value)
        number = safe_int(raw, -1)
        if number < 0:
            raise ValueError(f"Некорректный индекс части: {raw!r}")
        return number

    @staticmethod
    def _track_index(value) -> int:
        """Backward-compatible alias retained for older callers/tests."""
        return DownloadRequest.track_index(value)

    def resolved_selected_indices(self) -> list[int]:
        """Return explicit track indices; ``None`` means the whole book."""
        tracks = list(getattr(self.book, "tracks", None) or [])
        if self.selected_indices is None:
            return [self.track_index(track) for track in tracks]
        return [self.track_index(index) for index in self.selected_indices]

    def validate(self) -> None:
        if self.book is not None and bool(getattr(self.book, "restricted", False)):
            raise ValueError("Аудиокнига недоступна для скачивания по ограничению правообладателя.")
        if not self.book or not getattr(self.book, "tracks", None):
            raise ValueError("Сначала проанализируйте книгу.")
        valid = {self.track_index(track) for track in self.book.tracks}
        selected = set(self.resolved_selected_indices())
        if self.selected_indices is not None and not selected:
            raise ValueError("Не выбрана ни одна часть для скачивания.")
        unknown = sorted(selected - valid)
        if unknown:
            raise ValueError("Выбраны неизвестные части: " + ", ".join(map(str, unknown)))
        if not str(self.output_dir).strip():
            raise ValueError("Не указана папка для скачивания.")


def build_download_request(
    book: Book, settings: Mapping[str, Any] | None, selected_indices: list[int] | None
) -> DownloadRequest:
    data = normalize_settings(settings)
    request = DownloadRequest(
        book=book,
        selected_indices=(
            None if selected_indices is None
            else sorted({int(index) for index in selected_indices})
        ),
        output_dir=Path(str(data.get("output_dir") or DEFAULT_OUTPUT)).expanduser(),
        naming_mode=str(data.get("naming_mode", "number") or "number"),
        audio_preset=str(data.get("audio_preset", "copy") or "copy"),
        normalization_mode=str(data.get("normalization_mode", "off") or "off"),
        use_templates=bool(data.get("use_templates", False)),
        folder_template=str(data.get("folder_template", "{Book_Title}") or "{Book_Title}"),
        track_template=str(data.get("track_template", "{Track_Number}.mp3") or "{Track_Number}.mp3"),
    )
    request.validate()
    return request


__all__ = ["DownloadRequest", "build_download_request"]
