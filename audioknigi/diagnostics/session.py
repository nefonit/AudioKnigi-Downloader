from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Any

from ..core import SESSION_STATE_FILE, save_json
from ..metadata import APP_VERSION
from ..logging_utils import app_logger


def write_session_state(
    *,
    running: bool,
    settings: Mapping[str, Any] | None = None,
    path: str | Path | None = None,
) -> bool:
    """Persist the current-build lifecycle marker used by support diagnostics."""
    current = settings or {}
    payload = {
        "running": bool(running),
        "version": APP_VERSION,
        "language": str(current.get("language", "ru") or "ru"),
        "ui_mode": str(current.get("ui_mode", "easy") or "easy"),
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    target = Path(path) if path is not None else SESSION_STATE_FILE
    ok = bool(save_json(target, payload))
    if not ok:
        app_logger.debug("Failed to update Qt session state")
    return ok


__all__ = ["write_session_state"]
