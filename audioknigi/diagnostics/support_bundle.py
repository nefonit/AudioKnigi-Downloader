from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ..core import CRASH_REPORT_FILE, SETTINGS_FILE, load_json
from ..metadata import APP_VERSION
from ..logging_utils import APP_LOG_FILE, ERROR_LOG_FILE
from ..services.queue_service import QT_QUEUE_FILE

_SECRET_KEYS = {"abs_api_key", "api_key", "authorization", "token", "password", "secret", "cookie", "cookies"}
_SECRET_SUFFIXES = ("_api_key", "_authorization", "_token", "_password", "_secret", "_cookie", "_cookies")
_SECRET_COMPACT_SUFFIXES = ("apikey", "authorization", "authtoken", "token", "password", "secret", "cookie", "cookies")


def _is_secret_key(key: str) -> bool:
    lowered = str(key or "").strip().casefold()
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    return (
        lowered in _SECRET_KEYS
        or lowered.endswith(_SECRET_SUFFIXES)
        or any(compact.endswith(suffix) for suffix in _SECRET_COMPACT_SUFFIXES)
    )


def _privacy_path(value: Any) -> Any:
    if not isinstance(value, str) or not value:
        return value
    text = value
    try:
        home_path = Path.home()
        home = str(home_path)
        is_root = home_path == Path(home_path.anchor) if home_path.anchor else False
        if home and not is_root:
            variants = {home, home.replace("\\", "/"), home.replace("/", "\\")}
            placeholder = "%USERPROFILE%" if os.name == "nt" else "~"
            for variant in sorted((item for item in variants if item), key=len, reverse=True):
                if os.name == "nt":
                    text = re.sub(re.escape(variant), lambda _match: placeholder, text, flags=re.IGNORECASE)
                else:
                    text = text.replace(variant, placeholder)
    except Exception:
        return value

    # Windows settings may point outside %USERPROFILE% (D:\\... or UNC
    # shares). A diagnostics archive must not disclose those personal/server
    # paths. POSIX absolute paths keep their established diagnostic behavior.
    if re.match(r"^[A-Za-z]:[\\/]", text) or text.startswith("\\\\") or re.match(r"^//[^/\s\"']+/[^/\s\"']+", text):
        return "<configured-path>"

    # Error/status strings can contain an absolute path in the middle rather
    # than being a path themselves. Mask those too so another Windows username,
    # drive, or UNC share cannot leak into a support archive. Avoid matching the
    # ``s://`` portion of ordinary URLs.
    embedded_drive = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/])[^\s\"']+")
    embedded_unc = re.compile(
        r"(?:\\\\[^\\/\s\"']+[\\/][^\\/\s\"']+|(?<!:)//[^/\s\"']+/[^/\s\"']+)[^\s\"']*"
    )
    text = embedded_drive.sub("<configured-path>", text)
    text = embedded_unc.sub("<configured-path>", text)
    return text


def sanitized_settings(settings: Mapping[str, Any] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in dict(settings or {}).items():
        lowered = str(key).casefold()
        if _is_secret_key(key):
            result[key] = "<redacted>" if value not in (None, "", [], {}) else value
        elif lowered in {"geometry"}:
            result[key] = "<window-geometry>" if value else value
        elif lowered in {"abs_url"}:
            result[key] = "<configured-url>" if value else value
        elif isinstance(value, str):
            result[key] = _privacy_path(value)
        else:
            result[key] = value
    return result


def _dependency_versions() -> dict[str, str]:
    names = ("PySide6", "requests", "playwright", "Pillow", "mutagen")
    import_names = {"Pillow": "PIL"}
    versions: dict[str, str] = {}
    for name in names:
        metadata_version = ""
        try:
            metadata_version = str(importlib.metadata.version(name))
        except Exception:
            # Frozen one-file applications may omit dist-info metadata even
            # though the dependency itself is imported and working.
            metadata_version = ""
        if metadata_version:
            versions[name] = metadata_version
            continue
        try:
            module = importlib.import_module(import_names.get(name, name))
            value = str(getattr(module, "__version__", "") or "").strip()
            versions[name] = value or "bundled (version metadata unavailable)"
        except Exception:
            versions[name] = "not installed"
    return versions


def _tail(path: Path, *, max_bytes: int = 512_000) -> bytes:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            start = max(0, size - max_bytes)
            handle.seek(start)
            data = handle.read()
            if start > 0:
                newline = data.find(b"\n")
                if 0 <= newline < len(data) - 1:
                    data = data[newline + 1:]
            # Diagnostics are text.  Trim any incomplete UTF-8 codepoint at
            # either edge of a byte-limited tail so every archived log remains
            # valid UTF-8 for standard editors and support tooling.
            return data.decode("utf-8", errors="ignore").encode("utf-8")
    except OSError:
        return b""


def create_support_bundle(destination: str | Path, *, settings: Mapping[str, Any] | None = None) -> Path:
    """Create a shareable support ZIP without API keys, cookies or book media."""
    target = Path(destination).expanduser()
    if target.is_dir():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target = target / f"support_bundle_{stamp}.zip"
    elif not target.name.casefold().endswith(".zip"):
        target = target.parent / f"{target.name}.zip"
    target.parent.mkdir(parents=True, exist_ok=True)

    current_settings = settings
    if current_settings is None:
        payload = load_json(SETTINGS_FILE, {})
        current_settings = payload if isinstance(payload, dict) else {}

    environment = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "app_version": APP_VERSION,
        "python": sys.version,
        "executable": Path(sys.executable).name,
        "frozen": bool(getattr(sys, "frozen", False)),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "dependencies": _dependency_versions(),
        "app_data_dir": "<app-data>",
    }

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostics/environment.json", json.dumps(environment, ensure_ascii=False, indent=2))
        archive.writestr(
            "diagnostics/settings.sanitized.json",
            json.dumps(sanitized_settings(current_settings), ensure_ascii=False, indent=2, default=str),
        )
        for name, path in (
            ("errors.log", ERROR_LOG_FILE),
            ("application.log", APP_LOG_FILE),
            ("last_crash_report.txt", CRASH_REPORT_FILE),
        ):
            target_path = Path(path)
            if target_path.is_file():
                archive.writestr(f"diagnostics/{name}", _tail(target_path))
        queue = load_json(QT_QUEUE_FILE, [])
        if isinstance(queue, list):
            summary = []
            for position, item in enumerate(queue, 1):
                if not isinstance(item, dict):
                    continue
                raw_url = str(item.get("url", "") or "")
                opaque_id = hashlib.sha256(raw_url.encode("utf-8", "replace")).hexdigest()[:12] if raw_url else f"row-{position}"
                summary.append({
                    "id": opaque_id,
                    "status": item.get("status", ""),
                    "status_code": item.get("status_code", ""),
                    "attempts": item.get("attempts", 0),
                })
            archive.writestr("diagnostics/queue.summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
        archive.writestr(
            "README.txt",
            "AudioKnigi Downloader support bundle. API keys, cookies, passwords and audiobook media are intentionally excluded.\n",
        )
    return target
