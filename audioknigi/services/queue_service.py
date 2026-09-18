from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import base64
import binascii
import re
import time
import uuid

from ..core import APP_DIR, DEFAULT_OUTPUT, load_json, parse_time_seconds, save_json
from ..models import Book, NarrationVariant, Track, normalize_cover_cache
from ..logging_utils import app_logger
from .download_request import DownloadRequest

QT_QUEUE_FILE = APP_DIR / "qt_queue.json"

FINAL_STATUSES = {"completed", "cancelled"}
RUNNABLE_STATUSES = {"pending", "retry", "interrupted"}
NON_RUNNABLE_ANALYSIS_STATUS = "needs_analysis"


@dataclass(slots=True)
class QueueTask:
    id: str
    request: DownloadRequest
    title: str
    status: str = "Ожидает"
    status_code: str = "pending"
    attempts: int = 0
    priority: bool = False
    paused: bool = False
    last_error: str = ""
    output_folder: str = ""
    download_mode: str = "selected"
    created_at: float = field(default_factory=time.time)

    @property
    def url(self) -> str:
        return self.request.book.url


def _track_from_dict(data: dict[str, Any]) -> Track:
    allowed = {k: data.get(k) for k in Track.__dataclass_fields__ if k in data}
    allowed.setdefault("index", 0)
    allowed.setdefault("title", "")
    allowed.setdefault("file", "")
    try:
        allowed["index"] = int(allowed.get("index", 0) or 0)
    except (TypeError, ValueError):
        allowed["index"] = 0
    # Queue files can outlive several application versions and may be edited by
    # hand. Keep malformed/legacy empty-string time fields from leaking into
    # Track where later float(...) operations would fail.
    for key in ("start", "end", "duration", "actual_duration"):
        if key not in allowed or allowed[key] in (None, ""):
            allowed[key] = None
            continue
        parsed = parse_time_seconds(allowed[key])
        allowed[key] = float(parsed) if parsed is not None else None
    return Track(**allowed)


def _variant_from_dict(data: dict[str, Any]) -> NarrationVariant:
    allowed = {k: data.get(k) for k in NarrationVariant.__dataclass_fields__ if k in data}
    allowed.setdefault("url", "")
    return NarrationVariant(**allowed)


def _item_to_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return dict(value)
    serializer = getattr(value, "to_dict", None)
    if callable(serializer):
        try:
            data = serializer()
            return dict(data) if isinstance(data, dict) else None
        except Exception:
            return None
    return None


def _book_to_dict(book: Book) -> dict[str, Any]:
    cover = normalize_cover_cache(book.cover_cache)
    tracks = [item for value in (book.tracks or []) if (item := _item_to_dict(value)) is not None]
    variants = [item for value in (book.narration_variants or []) if (item := _item_to_dict(value)) is not None]
    return {
        "url": book.url,
        "title": book.title,
        "author": book.author,
        "narrator": book.narrator,
        "description": book.description,
        "genre": book.genre,
        "year": book.year,
        "cover_url": book.cover_url,
        "playlist_url": book.playlist_url,
        "tracks": tracks,
        "narration_variants": variants,
        "restricted": bool(book.restricted),
        "remote_size": int(book.remote_size or 0),
        "cover_cache_b64": base64.b64encode(cover[0]).decode("ascii") if cover else "",
        "cover_cache_mime": cover[1] if cover else "",
    }


def _book_from_dict(data: dict[str, Any]) -> Book:
    fields = Book.__dataclass_fields__
    kwargs = {k: data.get(k) for k in fields if k in data and k not in {"tracks", "narration_variants", "cover_cache"}}
    kwargs.setdefault("url", "")
    kwargs.setdefault("title", "—")
    kwargs["tracks"] = [_track_from_dict(x) for x in data.get("tracks", []) if isinstance(x, dict)]
    kwargs["narration_variants"] = [
        _variant_from_dict(x) for x in data.get("narration_variants", []) if isinstance(x, dict)
    ]
    encoded = str(data.get("cover_cache_b64", "") or "")
    if encoded:
        try:
            payload = base64.b64decode(encoded.encode("ascii"), validate=True)
            mime = str(data.get("cover_cache_mime", "") or "image/jpeg")
            kwargs["cover_cache"] = normalize_cover_cache((payload, mime))
        except Exception:
            kwargs["cover_cache"] = None
    else:
        kwargs["cover_cache"] = None
    return Book(**kwargs)


def task_to_dict(task: QueueTask) -> dict[str, Any]:
    req = task.request
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "status_code": task.status_code,
        "attempts": task.attempts,
        "priority": task.priority,
        "paused": task.paused,
        "last_error": task.last_error,
        "output_folder": task.output_folder,
        "download_mode": task.download_mode,
        "created_at": task.created_at,
        "request": {
            "book": _book_to_dict(req.book),
            "selected_indices": None if req.selected_indices is None else list(req.selected_indices),
            "output_dir": str(req.output_dir),
            "naming_mode": req.naming_mode,
            "audio_preset": req.audio_preset,
            "normalization_mode": req.normalization_mode,
            "use_templates": req.use_templates,
            "folder_template": req.folder_template,
            "track_template": req.track_template,
        },
    }


def _parse_selected_indices_payload(payload) -> list[int] | None:
    """Parse queue-selected indices without dropping an otherwise recoverable task."""
    if payload is None:
        return None
    if isinstance(payload, str):
        value = payload.strip()
        if not value or value.casefold() in {"all", "*"}:
            return None
        payload = [part for part in re.split(r"[,;\s]+", value) if part]
    try:
        values = list(payload)
    except TypeError:
        values = [payload]

    result: list[int] = []
    for value in values:
        # bool is an int subclass in Python; JSON true/false must never become
        # selected track 1/0.
        if isinstance(value, bool):
            continue
        if value is None or not str(value).strip():
            continue
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number not in result:
            result.append(number)
    # ``None`` means "all tracks" in DownloadRequest.  An explicit empty
    # array is different: it means the user selected nothing and must remain
    # empty so validation cannot silently turn it into a full-book download.
    return result


def task_from_dict(data: dict[str, Any]) -> QueueTask:
    if not isinstance(data, dict):
        raise TypeError("Queue task must be a mapping")

    req_data = data.get("request")
    legacy_flat = not isinstance(req_data, dict)
    if legacy_flat:
        # Preserve pre-Qt flat QueueItem snapshots instead of silently dropping
        # them. They do not contain analyzed Track objects, so they are retained
        # as non-runnable entries that explicitly require re-analysis.
        url = str(data.get("url") or "").strip()
        if not url:
            raise ValueError("Legacy queue item has no URL")
        title = str(data.get("title") or url or "—")
        legacy_cover = data.get("cover_cache")
        cover_cache = normalize_cover_cache(legacy_cover)
        if cover_cache is None and isinstance(legacy_cover, str) and legacy_cover.strip():
            encoded_cover = legacy_cover.strip()
            if encoded_cover.lower().startswith("data:") and "," in encoded_cover:
                encoded_cover = encoded_cover.split(",", 1)[1].strip()
            try:
                decoded_cover = base64.b64decode(encoded_cover.encode("ascii"), validate=True)
            except (ValueError, UnicodeEncodeError, binascii.Error):
                decoded_cover = b""
            if decoded_cover:
                cover_cache = normalize_cover_cache(
                    (decoded_cover, str(data.get("cover_cache_mime", "") or "image/jpeg"))
                )
        book = Book(
            url=url,
            title=title,
            author=str(data.get("author") or ""),
            narrator=str(data.get("narrator") or ""),
            cover_url=str(data.get("cover_url") or ""),
            cover_cache=cover_cache,
        )
        selected_payload = data.get("selected_indices", None)
        request = DownloadRequest(
            book=book,
            selected_indices=_parse_selected_indices_payload(selected_payload),
            output_dir=Path(str(data.get("output_dir") or DEFAULT_OUTPUT)).expanduser(),
            naming_mode=str(data.get("naming_mode", "number") or "number"),
            audio_preset=str(data.get("audio_preset", "copy") or "copy"),
            normalization_mode=(
                str(data.get("normalization_mode") or "single")
                if (data.get("normalization_mode") or bool(data.get("normalize_audio", False)))
                else "off"
            ),
            use_templates=(None if "use_templates" not in data else bool(data.get("use_templates"))),
            folder_template=(None if "folder_template" not in data else str(data.get("folder_template") or "{Book_Title}")),
            track_template=(None if "track_template" not in data else str(data.get("track_template") or "{Track_Number}.mp3")),
        )
        return QueueTask(
            id=str(data.get("id") or uuid.uuid4().hex),
            request=request,
            title=title,
            status="Требуется повторный анализ",
            status_code="needs_analysis",
            attempts=max(0, int(data.get("attempts", 0) or 0)),
            priority=bool(data.get("priority", False)),
            paused=True,
            last_error="Очередь импортирована из старого формата; выберите задачу и нажмите «Повторить» для автоматического анализа.",
            output_folder=str(data.get("output_folder", "") or ""),
            download_mode=str(data.get("download_mode", "selected") or "selected"),
            created_at=float(data.get("created_at", time.time()) or time.time()),
        )

    book_data = req_data.get("book")
    if not isinstance(book_data, dict):
        raise ValueError("Queue request has no valid book snapshot")
    book = _book_from_dict(book_data)
    selected_payload = req_data.get("selected_indices", None)
    request = DownloadRequest(
        book=book,
        selected_indices=_parse_selected_indices_payload(selected_payload),
        output_dir=Path(str(req_data.get("output_dir") or DEFAULT_OUTPUT)).expanduser(),
        naming_mode=str(req_data.get("naming_mode", "number") or "number"),
        audio_preset=str(req_data.get("audio_preset", "copy") or "copy"),
        normalization_mode=str(req_data.get("normalization_mode", "off") or "off"),
        use_templates=(None if req_data.get("use_templates") is None else bool(req_data.get("use_templates"))),
        folder_template=(None if req_data.get("folder_template") is None else str(req_data.get("folder_template") or "{Book_Title}")),
        track_template=(None if req_data.get("track_template") is None else str(req_data.get("track_template") or "{Track_Number}.mp3")),
    )
    status_code = str(data.get("status_code", "pending") or "pending")
    stored_status = str(data.get("status", "Ожидает") or "Ожидает")
    if status_code == "running" or stored_status.strip() == "Скачивается":
        status_code = "interrupted"
        status = "Незавершено"
    else:
        status = stored_status
    return QueueTask(
        id=str(data.get("id") or uuid.uuid4().hex),
        request=request,
        title=str(data.get("title") or book.title or "—"),
        status=status,
        status_code=status_code,
        attempts=max(0, int(data.get("attempts", 0) or 0)),
        priority=bool(data.get("priority", False)),
        paused=bool(data.get("paused", False)),
        last_error=str(data.get("last_error", "") or ""),
        output_folder=str(data.get("output_folder", "") or ""),
        download_mode=str(data.get("download_mode", "selected") or "selected"),
        created_at=float(data.get("created_at", time.time()) or time.time()),
    )


class QueueStore:
    def __init__(self, path: Path = QT_QUEUE_FILE):
        self.path = Path(path)

    def load(self) -> list[QueueTask]:
        raw = load_json(self.path, [])
        if not isinstance(raw, list):
            return []
        result: list[QueueTask] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                result.append(task_from_dict(item))
            except Exception as exc:
                app_logger.warning("Skipping invalid queue item: %s", exc)
                continue
        return result

    def save(self, tasks: list[QueueTask]) -> bool:
        return bool(save_json(self.path, [task_to_dict(x) for x in tasks]))

    @staticmethod
    def new_task(
        request: DownloadRequest, *, priority: bool = False, download_mode: str = "selected"
    ) -> QueueTask:
        request.validate()
        mode = "full_mp3" if str(download_mode or "selected") == "full_mp3" else "selected"
        return QueueTask(
            id=uuid.uuid4().hex,
            request=request,
            title=request.book.title or request.book.url,
            priority=bool(priority),
            download_mode=mode,
        )


def task_requires_analysis(task: QueueTask) -> bool:
    return bool(
        task.status_code == NON_RUNNABLE_ANALYSIS_STATUS
        or not getattr(getattr(task.request, "book", None), "tracks", None)
    )


def next_runnable_index(tasks: list[QueueTask]) -> int | None:
    candidates = [
        (idx, task) for idx, task in enumerate(tasks)
        if task.status_code in RUNNABLE_STATUSES and not task.paused and not task_requires_analysis(task)
    ]
    if not candidates:
        return None
    priority = [pair for pair in candidates if pair[1].priority]
    return (priority or candidates)[0][0]


__all__ = [
    "QT_QUEUE_FILE",
    "QueueTask",
    "QueueStore",
    "next_runnable_index",
    "task_from_dict",
    "task_to_dict",
    "task_requires_analysis",
]
