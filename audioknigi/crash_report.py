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
