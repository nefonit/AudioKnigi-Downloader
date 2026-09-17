from __future__ import annotations

"""Runtime boundary definition for the PySide6 frontend.

This module deliberately depends only on the Python standard library.  It is
safe to import from source tests, build preflight tools and frozen self-tests
without constructing a QApplication.
"""

from dataclasses import dataclass
import sys
from typing import Iterable


# Project modules that belong exclusively to the retired legacy frontend.  Reaching
# one of these from audioknigi_qt.py means the migration boundary regressed.
FORBIDDEN_PROJECT_PREFIXES: tuple[str, ...] = (
    "audioknigi.accessibility",
    "audioknigi.actions",
    "audioknigi.app",
    "audioknigi.dnd",
    "audioknigi.event_bus",
    "audioknigi.event_sounds",
    "audioknigi.help_center",
    "audioknigi.library_visuals",
    "audioknigi.onboarding",
    "audioknigi.player",
    "audioknigi.queue_manager",
    "audioknigi.search",
    "audioknigi.storage",
    "audioknigi.notifications",
    "audioknigi.tray",
    "audioknigi.ui_state",
    "audioknigi.visuals",
    "audioknigi.ui",
    "audioknigi.ui_kit",
)

# Third-party packages that are used only by the retired legacy frontend.  They must
# not be loaded by the Qt process and are explicitly excluded from the Qt EXE.
FORBIDDEN_EXTERNAL_PREFIXES: tuple[str, ...] = (
    "pygame",
    "plyer",
    "prism",
    "pystray",
    "tk_uia",
    "tkinter",
    "tkinterdnd2",
    "ttkbootstrap",
)

# Runtime distributions directly required by the Qt entry/import graph.  This
# list is also used by the build audit to keep requirements-qt.txt honest.
QT_RUNTIME_DISTRIBUTIONS: tuple[str, ...] = (
    "PySide6",
    "requests",
    "playwright",
    "Pillow",
    "mutagen",
)


@dataclass(frozen=True, slots=True)
class RuntimeAuditResult:
    forbidden_loaded: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not self.forbidden_loaded


def _matches_prefix(name: str, prefixes: Iterable[str]) -> bool:
    value = str(name or "")
    return any(value == prefix or value.startswith(prefix + ".") for prefix in prefixes)


def find_forbidden_loaded(module_names: Iterable[str] | None = None) -> tuple[str, ...]:
    names = list(sys.modules.keys()) if module_names is None else module_names
    forbidden = tuple(sorted({
        str(name)
        for name in names
        if _matches_prefix(str(name), FORBIDDEN_PROJECT_PREFIXES)
        or _matches_prefix(str(name), FORBIDDEN_EXTERNAL_PREFIXES)
    }))
    return forbidden


def audit_loaded_runtime(module_names: Iterable[str] | None = None) -> RuntimeAuditResult:
    return RuntimeAuditResult(forbidden_loaded=find_forbidden_loaded(module_names))


def assert_qt_runtime_clean(module_names: Iterable[str] | None = None) -> None:
    result = audit_loaded_runtime(module_names)
    if not result.clean:
        joined = ", ".join(result.forbidden_loaded)
        raise RuntimeError(f"Qt runtime loaded legacy-only modules: {joined}")


__all__ = [
    "FORBIDDEN_EXTERNAL_PREFIXES",
    "FORBIDDEN_PROJECT_PREFIXES",
    "QT_RUNTIME_DISTRIBUTIONS",
    "RuntimeAuditResult",
    "assert_qt_runtime_clean",
    "audit_loaded_runtime",
    "find_forbidden_loaded",
]
