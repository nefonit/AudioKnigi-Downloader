from __future__ import annotations

"""Non-invasive focus tracing for Windows NVDA/JAWS acceptance sessions.

The tracer observes Qt's existing ``QApplication.focusChanged`` signal and writes
small JSON-lines records.  It never installs an event filter, calls ``setFocus``
or changes widget state, so enabling diagnostics cannot create a second focus
management system like the legacy Tk accessibility bridge.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, TextIO

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QWidget


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _identifier(widget: QWidget | None) -> str:
    if widget is None:
        return ""
    try:
        getter = getattr(widget, "accessibleIdentifier", None)
        if callable(getter):
            value = str(getter() or "").strip()
            if value:
                return value
    except Exception:
        pass
    try:
        return str(widget.objectName() or "").strip()
    except Exception:
        return ""


def _describe(widget: QWidget | None) -> dict[str, Any] | None:
    if widget is None:
        return None
    try:
        window = widget.window()
    except Exception:
        window = None
    data: dict[str, Any] = {
        "id": _identifier(widget),
        "class": type(widget).__name__,
        "window_id": _identifier(window) if isinstance(window, QWidget) else "",
    }
    # State is useful for diagnosing invisible/disabled focus destinations, while
    # deliberately excluding editor values, book titles, URLs and accessible text.
    for key, getter_name in (
        ("enabled", "isEnabled"),
        ("visible", "isVisible"),
    ):
        try:
            getter = getattr(widget, getter_name)
            data[key] = bool(getter())
        except Exception:
            data[key] = None
    return data


class AccessibilityFocusTracer(QObject):
    """Append privacy-minimized focus transitions to a JSONL file."""

    def __init__(self, app: QApplication, path: str | Path, parent: QObject | None = None):
        super().__init__(parent or app)
        self.app = app
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream: TextIO | None = self.path.open("a", encoding="utf-8", newline="\n")
        self._closed = False
        self._write({
            "event": "trace_started",
            "python": sys.version.split()[0],
            "platform": sys.platform,
        })
        app.focusChanged.connect(self._focus_changed)
        app.aboutToQuit.connect(self.close)

    def _write(self, payload: dict[str, Any]) -> None:
        if self._closed or self._stream is None:
            return
        try:
            record = {"time_utc": _utc_now(), **payload}
            self._stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            self._stream.flush()
        except (OSError, ValueError):
            # Diagnostics must never make the application less reliable.
            return

    def _focus_changed(self, old: QWidget | None, new: QWidget | None) -> None:
        self._write({
            "event": "focus_changed",
            "old": _describe(old),
            "new": _describe(new),
        })

    def marker(self, name: str) -> None:
        """Write an explicit test-session marker without recording user content."""
        label = str(name or "").strip()[:80]
        if label:
            self._write({"event": "marker", "name": label})

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._write({"event": "trace_stopped"})
        finally:
            self._closed = True
            stream, self._stream = self._stream, None
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    pass


def extract_focus_trace_argument(argv: list[str]) -> tuple[list[str], Path | None]:
    """Remove the application-only focus-trace option before Qt parses argv."""
    cleaned: list[str] = []
    trace: Path | None = None
    index = 0
    while index < len(argv):
        arg = str(argv[index])
        if arg.startswith("--qt-focus-trace="):
            value = arg.split("=", 1)[1].strip()
            if not value:
                raise ValueError("--qt-focus-trace требует непустой путь к файлу журнала")
            trace = Path(value)
            index += 1
            continue
        if arg == "--qt-focus-trace":
            if index + 1 >= len(argv) or str(argv[index + 1]).startswith("--"):
                raise ValueError("--qt-focus-trace требует путь к файлу журнала")
            value = str(argv[index + 1]).strip()
            if not value:
                raise ValueError("--qt-focus-trace требует непустой путь к файлу журнала")
            trace = Path(value)
            index += 2
            continue
        cleaned.append(arg)
        index += 1
    return cleaned, trace


def install_focus_trace(app: QApplication, path: str | Path | None) -> AccessibilityFocusTracer | None:
    if path is None:
        return None
    return AccessibilityFocusTracer(app, path)


__all__ = [
    "AccessibilityFocusTracer",
    "extract_focus_trace_argument",
    "install_focus_trace",
]
