from __future__ import annotations

import csv
import json
import os
import time
import threading
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ..core import (
    APP_DIR,
    APP_TITLE,
    DEFAULT_OUTPUT,
    HISTORY_FILE,
    PLAYER_POSITIONS_FILE,
    SETTINGS_FILE,
    load_json,
    save_json,
)
from ..metadata import APP_VERSION
from .queue_service import QT_QUEUE_FILE


HISTORY_LOCK = threading.RLock()


BACKUP_MEMBERS = {
    "settings.json": SETTINGS_FILE,
    "history.json": HISTORY_FILE,
    "player_positions.json": PLAYER_POSITIONS_FILE,
    "qt_queue.json": QT_QUEUE_FILE,
}


@dataclass(slots=True)
class UnfinishedDownload:
    manifest_path: Path
    folder: Path
    url: str
    title: str
    selected_indices: list[int] | None
    naming_mode: str = "number"
    audio_preset: str = "copy"
    normalization_mode: str = "off"
    use_templates: bool = False
    folder_template: str = "{Book_Title}"
    track_template: str = "{Track_Number}.mp3"
    download_mode: str = "parts"
    updated_at: str = ""


def _history_rows(raw: Any, *, strict: bool = False, limit: int | None = 500) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        if strict:
            raise ValueError("history.json должен содержать список")
        return []
    rows: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            if strict:
                raise ValueError("history.json содержит некорректную запись")
            continue
        rows.append(dict(item))
    return rows if limit is None else rows[: max(0, int(limit))]


def load_history_records() -> list[dict[str, Any]]:
    with HISTORY_LOCK:
        return _history_rows(load_json(HISTORY_FILE, []))


def save_history_records(records: Iterable[dict[str, Any]]) -> bool:
    with HISTORY_LOCK:
        return bool(save_json(HISTORY_FILE, _history_rows(list(records))))


def _csv_safe_value(value: Any) -> Any:
    """Prevent spreadsheet formula execution while preserving ordinary values."""
    if not isinstance(value, str) or not value:
        return value
    stripped = value.lstrip(" \t\r\n")
    if value[:1] in {"\t", "\r", "\n"} or stripped[:1] in {"=", "+", "-", "@"}:
        return "'" + value
    return value

def export_history(records: Iterable[dict[str, Any]], path: Path, format_name: str) -> Path:
    with HISTORY_LOCK:
        rows = _history_rows(list(records), limit=None)
    if not rows:
        raise ValueError("История пуста — экспортировать нечего.")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = str(format_name or "json").lower()
    if fmt == "json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
    if fmt != "csv":
        raise ValueError(f"Неизвестный формат экспорта: {format_name}")
    fields = ("date", "title", "author", "narrator", "genre", "year", "parts", "folder", "url")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(
            {field: _csv_safe_value(row.get(field, "")) for field in fields}
            for row in rows
        )
    return path


def _read_backup_member(source: Path) -> bytes | None:
    """Read one backup member with short retries for transient Windows sharing errors."""
    for attempt in range(3):
        try:
            return source.read_bytes()
        except FileNotFoundError:
            return None
        except OSError:
            if attempt >= 2:
                raise
            time.sleep(0.05 * (attempt + 1))
    return None


def create_backup(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshots: dict[str, bytes] = {}
    for arcname, source in BACKUP_MEMBERS.items():
        if not source.exists():
            continue
        if source == HISTORY_FILE:
            with HISTORY_LOCK:
                payload = _read_backup_member(source)
        else:
            payload = _read_backup_member(source)
        if payload is not None:
            snapshots[arcname] = payload
    manifest = {
        "app": APP_TITLE,
        "version": APP_VERSION,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "format": 2,
        "includes": list(snapshots),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for arcname, payload in snapshots.items():
            archive.writestr(arcname, payload)
        archive.writestr(
            "backup_manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
    return path


def _validated_backup_payloads(path: Path) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        if not names.intersection(BACKUP_MEMBERS):
            raise ValueError("В ZIP нет данных AudioKnigi для восстановления.")
        for member in BACKUP_MEMBERS:
            if member not in names:
                continue
            data = json.loads(archive.read(member).decode("utf-8-sig"))
            if member == "settings.json" and not isinstance(data, dict):
                raise ValueError("settings.json должен содержать объект")
            if member == "history.json":
                data = _history_rows(data, strict=True)
            if member == "player_positions.json" and not isinstance(data, dict):
                raise ValueError("player_positions.json должен содержать объект")
            if member == "qt_queue.json" and not isinstance(data, list):
                raise ValueError("qt_queue.json должен содержать список")
            payloads[member] = data
    return payloads


def restore_backup(path: Path) -> list[str]:
    """Restore validated JSON members with best-effort rollback on partial failure."""
    payloads = _validated_backup_payloads(Path(path))
    APP_DIR.mkdir(parents=True, exist_ok=True)

    # A backup can contain several independent state files.  Snapshot the raw
    # originals before replacing any of them so a late disk/sharing failure does
    # not leave the application in a half-restored state (especially positions).
    originals: dict[str, tuple[bool, bytes | None]] = {}
    for member in payloads:
        target = BACKUP_MEMBERS[member]
        existed = target.exists()
        originals[member] = (existed, _read_backup_member(target) if existed else None)

    restored: list[str] = []
    try:
        for member, data in payloads.items():
            target = BACKUP_MEMBERS[member]
            if target == HISTORY_FILE:
                with HISTORY_LOCK:
                    save_json(target, data, raise_errors=True)
            else:
                save_json(target, data, raise_errors=True)
            restored.append(member)
    except Exception:
        for member in reversed(restored):
            target = BACKUP_MEMBERS[member]
            existed, raw = originals.get(member, (False, None))
            try:
                if existed and raw is not None:
                    # Parse the previous JSON and restore it through the same
                    # atomic save path used by normal application state writes.
                    previous = json.loads(raw.decode("utf-8-sig"))
                    if target == HISTORY_FILE:
                        with HISTORY_LOCK:
                            save_json(target, previous, raise_errors=True)
                    else:
                        save_json(target, previous, raise_errors=True)
                elif not existed:
                    target.unlink(missing_ok=True)
            except Exception:
                # Preserve the original restore exception; callers can retry from
                # the still-valid ZIP and the UI keeps persistence suspended.
                pass
        raise
    return restored


def clear_history() -> bool:
    with HISTORY_LOCK:
        return bool(save_json(HISTORY_FILE, []))


def scan_unfinished(output_dir: str | Path | None = None) -> list[UnfinishedDownload]:
    base = Path(output_dir or DEFAULT_OUTPUT).expanduser()
    if not base.exists() or not base.is_dir():
        return []
    manifests: list[UnfinishedDownload] = []
    try:
        walker = os.walk(base)
        base_is_filesystem_root = base.resolve() == Path(base.anchor).resolve() if base.anchor else False
        for root, dirs, files in walker:
            # Preserve arbitrarily deep user templates for a normal library
            # folder. If a filesystem root was selected accidentally, cap the
            # traversal depth so one refresh cannot walk an entire drive.
            if base_is_filesystem_root:
                try:
                    depth = len(Path(root).resolve().relative_to(base.resolve()).parts)
                except (OSError, ValueError):
                    depth = 0
                if depth >= 8:
                    dirs[:] = []
            dirs[:] = [name for name in dirs if not name.startswith(".")]
            skipped = {"node_modules", "__pycache__", "venv", ".venv"}
            dirs[:] = [name for name in dirs if name.casefold() not in skipped]
            if "resume.json" not in files:
                continue
            manifest_path = Path(root) / "resume.json"
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if not isinstance(raw, dict) or not str(raw.get("url", "")).strip():
                continue
            selected_payload = raw.get("selected_indices", None)
            indices: list[int] | None
            if selected_payload in (None, []):
                # Older manifests sometimes encoded whole-book selection as []
                # while the current request contract uses null/None. Preserve both.
                indices = None
            elif isinstance(selected_payload, str) and (
                not selected_payload.strip()
                or selected_payload.strip().casefold() in {"all", "*"}
            ):
                indices = None
            else:
                indices = []
                if isinstance(selected_payload, (str, bytes, bytearray)):
                    selected_values = [selected_payload]
                else:
                    try:
                        selected_values = list(selected_payload)
                    except TypeError:
                        selected_values = [selected_payload]
                for value in selected_values:
                    if isinstance(value, bool):
                        continue
                    try:
                        number = int(value)
                    except (TypeError, ValueError):
                        continue
                    if number >= 0 and number not in indices:
                        indices.append(number)
                if not indices:
                    continue
            manifests.append(
                UnfinishedDownload(
                    manifest_path=manifest_path,
                    folder=manifest_path.parent,
                    url=str(raw.get("url", "")).strip(),
                    title=str(raw.get("title", "") or manifest_path.parent.name),
                    selected_indices=indices,
                    naming_mode=str(raw.get("naming_mode", "number") or "number"),
                    audio_preset=str(raw.get("audio_preset", "copy") or "copy"),
                    normalization_mode=str(raw.get("normalization_mode", "off") or "off"),
                    use_templates=bool(raw.get("use_templates", False)),
                    folder_template=str(raw.get("folder_template", "{Book_Title}") or "{Book_Title}"),
                    track_template=str(raw.get("track_template", "{Track_Number}.mp3") or "{Track_Number}.mp3"),
                    download_mode="full_mp3" if str(raw.get("download_mode", "parts")) == "full_mp3" else "parts",
                    updated_at=str(raw.get("updated_at", "") or ""),
                )
            )
    except (OSError, PermissionError):
        return []
    manifests.sort(key=lambda item: (item.updated_at, str(item.manifest_path)), reverse=True)
    return manifests


__all__ = [
    "UnfinishedDownload",
    "load_history_records",
    "save_history_records",
    "export_history",
    "create_backup",
    "restore_backup",
    "clear_history",
    "scan_unfinished",
]
