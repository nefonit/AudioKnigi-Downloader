from __future__ import annotations

import logging
import os
import platform
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .core import APP_DIR

APP_LOG_FILE = APP_DIR / "app.log"
ERROR_LOG_FILE = APP_DIR / "errors.log"


def sanitize_log_text(value: object) -> str:
    text = str(value) if value is not None else ""

    # Hide explicit secrets before replacing URLs so non-URL occurrences are
    # still sanitized and the rules remain independently testable.
    text = re.sub(
        r"(?i)\b((?:[a-z0-9]+[_-])*(?:api[_ -]?key|token|authorization|cookie|cookies|password|secret))\s*[:=]\s*\S+",
        r"\1=<hidden>",
        text,
    )
    text = re.sub(r"(?i)Bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer <hidden>", text)

    # URLs may contain book IDs, query strings or credentials: mask them whole,
    # while preserving punctuation that belongs to the surrounding sentence.
    def _mask_url(match):
        raw = match.group(0)
        suffix = ""
        while raw and raw[-1] in ".,;:!?)]}":
            suffix = raw[-1] + suffix
            raw = raw[:-1]
        return "<URL>" + suffix

    text = re.sub(r"https?://[^\s<>\"']+", _mask_url, text, flags=re.I)

    try:
        home_path = Path.home()
        home = str(home_path)
        # Never replace a filesystem root such as '/' or 'C:\\' because doing so
        # would corrupt every path separator in the log.
        is_root = home_path == Path(home_path.anchor) if home_path.anchor else False
        if home and not is_root:
            variants = {home, home.replace("\\", "/"), home.replace("/", "\\")}
            placeholder = "%USERPROFILE%" if os.name == "nt" else "~"
            for variant in sorted((v for v in variants if v), key=len, reverse=True):
                if os.name == "nt":
                    text = re.sub(re.escape(variant), lambda _match: placeholder, text, flags=re.IGNORECASE)
                else:
                    text = text.replace(variant, placeholder)
    except Exception:
        pass
    return text


class PrivacyFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return sanitize_log_text(super().format(record))


def get_app_logger() -> logging.Logger:
    logger = logging.getLogger("audioknigi")
    if getattr(logger, "_audioknigi_configured", False):
        return logger

    formatter = PrivacyFormatter(
        "%(asctime)s | %(levelname)s | %(threadName)s | "
        "%(module)s.%(funcName)s:%(lineno)d | %(message)s"
    )
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Keep a compact error-only log for support.  Touching the file at startup
        # guarantees that Help > Diagnostics > Open error log always has a stable
        # target even on a session with no failures.
        try:
            ERROR_LOG_FILE.touch(exist_ok=True)
            error_handler = RotatingFileHandler(
                ERROR_LOG_FILE,
                maxBytes=1_500_000,
                backupCount=3,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
        except Exception:
            pass
    except Exception:
        # Diagnostics are optional. A read-only/broken APPDATA must never make
        # importing the package or starting the GUI fail.
        fallback = logging.NullHandler()
        logger.addHandler(fallback)
    # DEBUG is intentionally file-only. It gives support enough context to
    # diagnose fallbacks without making the visible UI log noisy.
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger._audioknigi_configured = True
    return logger


app_logger = get_app_logger()

def log_runtime_context(*, version: str, language: str = "", ui_mode: str = "") -> None:
    """Write one privacy-sanitized session header for support diagnostics."""
    try:
        app_logger.info(
            "SESSION START | app=%s | python=%s | os=%s | frozen=%s | pid=%s | language=%s | ui_mode=%s",
            version,
            sys.version.replace("\n", " "),
            platform.platform(),
            bool(getattr(sys, "frozen", False)),
            os.getpid(),
            language or "?",
            ui_mode or "?",
        )
    except Exception:
        # Logging must never prevent application startup.
        pass


def log_exception(context: str, exc_info=None, *, level: int = logging.ERROR) -> None:
    """Record a full traceback with a short support-friendly context label.

    RecursionError is deliberately logged without traceback formatting: trying
    to stringify a deep traceback while the interpreter is already at its
    recursion limit can turn diagnostics into a second failure.
    """
    try:
        if exc_info is None or exc_info is True:
            exc_info = sys.exc_info()
        err_obj = exc_info[1] if isinstance(exc_info, tuple) and len(exc_info) >= 2 else exc_info
        if isinstance(err_obj, RecursionError):
            app_logger.log(level, "UNHANDLED EXCEPTION | %s | RecursionError: %s", context, err_obj)
            return
        app_logger.log(level, "UNHANDLED EXCEPTION | %s", context, exc_info=exc_info)
    except Exception:
        pass



def tail_error_log(max_lines: int = 200) -> str:
    """Return the newest privacy-sanitized error log lines for support reports."""
    try:
        if not ERROR_LOG_FILE.is_file():
            return ""
        lines = ERROR_LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-max(1, int(max_lines)):])
    except Exception:
        return ""


__all__ = [
    "APP_LOG_FILE", "ERROR_LOG_FILE", "PrivacyFormatter", "app_logger",
    "get_app_logger", "log_exception", "log_runtime_context",
    "sanitize_log_text", "tail_error_log",
]
