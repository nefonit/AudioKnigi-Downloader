from __future__ import annotations

import platform
import sys
import time
import traceback
from .core import CRASH_REPORT_FILE
from .metadata import APP_VERSION
from .brand import DISPLAY_NAME
from .logging_utils import app_logger, sanitize_log_text

def _sanitize(text: str) -> str:
    return sanitize_log_text(text)



def crash_report_is_current(path=None, *, version: str = APP_VERSION) -> bool:
    """Return True only when the persisted crash report belongs to this build.

    ``last_crash_report.txt`` intentionally survives process crashes, but it can
    also survive application upgrades.  Support bundles and the Help Center must
    not present an old-version crash as if it came from the current build.
    """
    report_path = CRASH_REPORT_FILE if path is None else path
    try:
        first_line = report_path.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
    except (OSError, IndexError):
        return False
    return first_line == f"{DISPLAY_NAME} {version}"


def read_current_crash_report(path=None, *, version: str = APP_VERSION) -> str:
    """Read the current-build crash report or return an empty string."""
    report_path = CRASH_REPORT_FILE if path is None else path
    if not crash_report_is_current(report_path, version=version):
        return ""
    try:
        return report_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def build_report(exc_type, exc, tb, component="application") -> str:
    try:
        stack = "".join(traceback.format_exception(exc_type, exc, tb))
    except Exception as format_error:
        # A RecursionError or a damaged traceback must never make crash
        # reporting fail recursively. Keep a minimal, bounded diagnostic.
        name = getattr(exc_type, "__name__", str(exc_type))
        try:
            message = str(exc)
        except Exception:
            message = "<exception text unavailable>"
        stack = f"{name}: {message}\n[traceback formatting failed: {type(format_error).__name__}]\n"
    report = (
        f"{DISPLAY_NAME} {APP_VERSION}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Component: {component}\n"
        f"OS: {platform.platform()}\n"
        f"Python: {sys.version.split()[0]}\n\n"
        f"{_sanitize(stack)}"
    )
    # Keep the single crash report bounded even if a traceback contains very large payloads.
    if len(report) > 200_000:
        report = report[:200_000] + "\n\n[report truncated]"
    try:
        CRASH_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        CRASH_REPORT_FILE.write_text(report, encoding='utf-8')
    except Exception:
        pass
    try:
        # The error-only rotating handler records the same crash in errors.log.
        # Keep the message compact; the full traceback remains in last_crash_report.
        if isinstance(exc, RecursionError):
            app_logger.error(
                "CRASH | component=%s | RecursionError: %s", component, exc
            )
        else:
            app_logger.error(
                "CRASH | component=%s | %s: %s",
                component, getattr(exc_type, "__name__", exc_type), exc,
                exc_info=(exc_type, exc, tb),
            )
    except Exception:
        pass
    return report
