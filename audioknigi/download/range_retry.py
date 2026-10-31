"""Bounded retry delay for transient HTTP Range failures.

This module contains no HTTP I/O. A server's Retry-After is a hint,
not permission to stall indefinitely or change the existing retry count.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math


MAX_RETRY_SECONDS = 1.0  # Preserve the existing maximum wait and cancellation latency.


def bounded_range_retry_delay(consecutive_no_progress: int, retry_after=None, *, now=None) -> float:
    """Back off as before, optionally honoring a short Retry-After hint.

    Accept delay-seconds and HTTP-date forms. Invalid, negative, non-finite
    and past dates fall back to the existing 0.15s..1.0s backoff.
    """
    baseline = min(MAX_RETRY_SECONDS, 0.15 * max(1, consecutive_no_progress))
    if retry_after is None:
        return baseline

    raw = str(retry_after).strip()
    if not raw:
        return baseline
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        try:
            when = parsedate_to_datetime(raw)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            current = now if now is not None else datetime.now(timezone.utc)
            seconds = (when - current).total_seconds()
        except (TypeError, ValueError, OverflowError, IndexError):
            return baseline

    if not math.isfinite(seconds) or seconds <= 0:
        return baseline
    return max(baseline, min(MAX_RETRY_SECONDS, seconds))
