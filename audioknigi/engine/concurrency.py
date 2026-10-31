"""GUI-neutral helpers for cancellable parallel source operations.

The same polling/cancellation loop was previously duplicated in the Poleknig
and Knigavuhe parsers and the book analysis service. Keep the polling interval,
exception type and shutdown semantics unchanged for existing callers.
"""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, wait

from ..core import Cancelled


def iter_completed_cancellable(futures, cancel_event=None):
    """Yield completed futures, polling for cancellation every 100 ms."""
    pending = set(futures)
    while pending:
        if cancel_event is not None and cancel_event.is_set():
            for future in pending:
                future.cancel()
            raise Cancelled("Операция отменена пользователем")
        done, pending = wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)
        for future in done:
            yield future


def shutdown_pool_now(pool, futures) -> None:
    """Cancel unfinished work and shut down without waiting for blocked I/O."""
    for future in futures:
        if not future.done():
            future.cancel()
    pool.shutdown(wait=False, cancel_futures=True)
