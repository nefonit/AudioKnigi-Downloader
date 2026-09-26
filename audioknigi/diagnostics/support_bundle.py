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

_LOG_AUTH_HEADER_RE = re.compile(r"(?im)\b(authorization|proxy-authorization|cookie|set-cookie)\s*:\s*[^\r\n]*")
_LOG_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+\-/=]+")
_LOG_SECRET_VALUE_RE = re.compile(
    r"(?i)((?:[\"'])?\b(?:api[_-]?key|auth[_-]?token|access[_-]?token|refresh[_-]?token|token|password|secret|cookie|cookies)\b(?:[\"'])?\s*[=:]\s*)"
    r"(?:\"([^\"]*)\"|'([^']*)'|([^&\s,;]+))"
)

# Precompiled Windows-path patterns are used for every support-log line. Keep
# them at module scope so large diagnostic bundles do not rebuild regex state
# thousands of times. File-like paths get a first pass whose final component
# may contain spaces; this prevents names such as ``01. Введение.mp3`` from
# leaking while the ordinary fallback keeps concise trailing log text intact.
_WINDOWS_PATH_SEGMENT_RE = r"[^\\/|;\r\n\"']+"
_WINDOWS_PATH_FINAL_RE = r"[^\\/\s|;\r\n\"']+"
_WINDOWS_FILE_FINAL_RE = r"[^\\/|;\r\n\"']+\.[A-Za-z0-9]{1,16}"
_EMBEDDED_DRIVE_FILE_RE = re.compile(
    rf"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/])(?:{_WINDOWS_PATH_SEGMENT_RE}[\\/])*{_WINDOWS_FILE_FINAL_RE}"
)
_EMBEDDED_UNC_FILE_RE = re.compile(
    rf"(?:\\\\{_WINDOWS_PATH_SEGMENT_RE}[\\/](?:{_WINDOWS_PATH_SEGMENT_RE}[\\/])*{_WINDOWS_FILE_FINAL_RE}|"
    rf"(?<!:)//{_WINDOWS_PATH_SEGMENT_RE}/(?:{_WINDOWS_PATH_SEGMENT_RE}/)*{_WINDOWS_FILE_FINAL_RE})"
)
_EMBEDDED_DRIVE_PATH_RE = re.compile(
    rf"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/])(?:{_WINDOWS_PATH_SEGMENT_RE}[\\/])*(?:{_WINDOWS_PATH_FINAL_RE})?[\\/]?"
)
_EMBEDDED_UNC_PATH_RE = re.compile(
    rf"(?:\\\\{_WINDOWS_PATH_SEGMENT_RE}[\\/](?:{_WINDOWS_PATH_SEGMENT_RE}[\\/])*(?:{_WINDOWS_PATH_FINAL_RE})?[\\/]?|"
    rf"(?<!:)//{_WINDOWS_PATH_SEGMENT_RE}/(?:{_WINDOWS_PATH_SEGMENT_RE}/)*(?:{_WINDOWS_PATH_FINAL_RE})?/?)"
)



def _is_secret_key(key: str) -> bool:
    lowered = str(key or "").strip().casefold()
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    return (
        lowered in _SECRET_KEYS
        or lowered.endswith(_SECRET_SUFFIXES)
        or any(compact.endswith(suffix) for suffix in _SECRET_COMPACT_SUFFIXES)
    )


def _privacy_path(value: Any, *, collapse_whole_path: bool = True) -> Any:
    if isinstance(value, Path):
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        return value
    if not text:
        return text
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
        # Home discovery can fail in service/portable/sandbox contexts.  Keep
        # sanitizing drive/UNC paths below instead of returning the raw value.
        home_path = None

    # Windows settings may point outside %USERPROFILE% (D:\\... or UNC
    # shares). A diagnostics archive must not disclose those personal/server
    # paths. POSIX absolute paths keep their established diagnostic behavior.
    if collapse_whole_path and "\n" not in text and "\r" not in text and (
        re.match(r"^[A-Za-z]:[\\/]", text)
        or text.startswith("\\\\")
        or re.match(r"^//[^/\s\"']+/[^/\s\"']+", text)
    ):
        return "<configured-path>"

    # Error/status strings can contain an absolute path in the middle rather
    # than being a path themselves. Mask those too so another Windows username,
    # drive, or UNC share cannot leak into a support archive. Avoid matching the
    # ``s://`` portion of ordinary URLs. Paths can contain spaces, so stop only
    # at strong log-field delimiters rather than at whitespace.
    text = _EMBEDDED_DRIVE_FILE_RE.sub("<configured-path>", text)
    text = _EMBEDDED_UNC_FILE_RE.sub("<configured-path>", text)
    text = _EMBEDDED_DRIVE_PATH_RE.sub("<configured-path>", text)
    text = _EMBEDDED_UNC_PATH_RE.sub("<configured-path>", text)
    return text


def _sanitize_log_bytes(payload: bytes) -> bytes:
    """Redact paths and common credential forms before logs enter a support ZIP."""
    text = bytes(payload or b"").decode("utf-8", errors="replace")
    # A log tail is arbitrary multi-line diagnostic text, not one configured
    # path.  Never collapse the entire payload merely because the first line
    # happens to begin with ``C:\\`` or a UNC prefix.
    text = str(_privacy_path(text, collapse_whole_path=False))
    text = _LOG_AUTH_HEADER_RE.sub(lambda m: f"{m.group(1)}: <redacted>", text)
    text = _LOG_BEARER_RE.sub("Bearer <redacted>", text)
    def redact_secret_value(match):
        quote = '"' if match.group(2) is not None else "'" if match.group(3) is not None else ""
        return match.group(1) + quote + "<redacted>" + quote

    text = _LOG_SECRET_VALUE_RE.sub(redact_secret_value, text)
    return text.encode("utf-8")


def _sanitize_setting_value(key: str, value: Any) -> Any:
    lowered = str(key).casefold()
    if _is_secret_key(key):
        return "<redacted>" if value not in (None, "", [], {}, ()) else value
    if lowered in {"geometry"}:
        return "<window-geometry>" if value else value
    if lowered in {"abs_url"}:
        return "<configured-url>" if value else value
    if isinstance(value, Mapping):
        return {
            str(child_key): _sanitize_setting_value(str(child_key), child_value)
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_setting_value("", item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_setting_value("", item) for item in value)
    if isinstance(value, (str, Path)):
        if isinstance(value, Path):
            return _privacy_path(str(value))
        text = str(value)
        # Settings are normalized to JSON primitives, so configured paths are
        # usually plain strings rather than pathlib.Path objects.  Treat a
        # single Windows drive/UNC path as a configured path before feeding
        # arbitrary text through the log sanitizer; otherwise a path whose
        # final component contains spaces can be only partially redacted.
        if "\n" not in text and "\r" not in text and (
            re.match(r"^[A-Za-z]:[\\/]", text)
            or text.startswith("\\\\")
            or re.match(r"^//[^/\s\"']+/[^/\s\"']+", text)
        ):
            return _privacy_path(text, collapse_whole_path=True)
        # Nested plugin/header settings can contain credentials inside a string
        # even when the parent key itself is not named "token" or "password".
        return _sanitize_log_bytes(text.encode("utf-8")).decode("utf-8")
    return value


def sanitized_settings(settings: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        str(key): _sanitize_setting_value(str(key), value)
        for key, value in dict(settings or {}).items()
    }


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
                # If the byte window already starts immediately after a newline,
                # it begins on a clean line boundary and must not be trimmed.
                handle.seek(start - 1)
                starts_after_newline = handle.read(1) == b"\n"
                if not starts_after_newline:
                    newline = data.find(b"\n")
                    if newline >= 0:
                        data = data[newline + 1:]
            # Diagnostics are text. Trim any incomplete UTF-8 codepoint at a
            # byte-window boundary while keeping the archived tail valid UTF-8.
            return data.decode("utf-8", errors="ignore").encode("utf-8")
    except OSError:
        return b""


def create_support_bundle(destination: str | Path, *, settings: Mapping[str, Any] | None = None) -> Path:
    """Create a shareable support ZIP without API keys, cookies or book media."""
    raw_destination = str(destination)
    target = Path(destination).expanduser()
    explicit_directory = raw_destination.endswith(("/", "\\"))
    if explicit_directory and not target.exists():
        target.mkdir(parents=True, exist_ok=True)
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
                archive.writestr(
                    f"diagnostics/{name}",
                    _sanitize_log_bytes(_tail(target_path)),
                )
        queue_payload = load_json(QT_QUEUE_FILE, [])
        queue = queue_payload
        if isinstance(queue_payload, dict):
            queue = queue_payload.get("items", queue_payload.get("queue", []))
        if isinstance(queue, list):
            summary = []
            for position, item in enumerate(queue, 1):
                if not isinstance(item, dict):
                    continue
                request = item.get("request") if isinstance(item.get("request"), dict) else {}
                book = request.get("book") if isinstance(request.get("book"), dict) else {}
                raw_url = str(item.get("url") or book.get("url") or "")
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
