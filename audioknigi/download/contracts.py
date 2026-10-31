"""Stable callback, preflight and result data contracts for headless downloads."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from ..models import Book
from ..services.download_request import DownloadRequest

StatusCallback = Callable[[str], None]
StageCallback = Callable[[int, str], None]
ProgressCallback = Callable[[float], None]
LogCallback = Callable[[str], None]
TransferCallback = Callable[[float, int], None]
MissingMediaCallback = Callable[[list[int], str, bool], str]
HistoryCallback = Callable[[], None]
RequestChangedCallback = Callable[[DownloadRequest], None]


@dataclass(slots=True)
class DownloadCallbacks:
    status: StatusCallback | None = None
    stage: StageCallback | None = None
    progress: ProgressCallback | None = None
    log: LogCallback | None = None
    transfer: TransferCallback | None = None
    missing_media: MissingMediaCallback | None = None
    history_changed: HistoryCallback | None = None
    request_changed: RequestChangedCallback | None = None


@dataclass(slots=True)
class DownloadResult:
    folder: Path
    selected_indices: list[int]
    skipped_indices: list[int]
    target_file: Path | None = None
    book: Book | None = None


@dataclass(frozen=True, slots=True)
class DuplicatePreflight:
    exact_duplicate: bool
    folder: Path
    evidence: str = ""



