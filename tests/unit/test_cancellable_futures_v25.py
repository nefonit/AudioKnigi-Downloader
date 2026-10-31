"""Regression coverage for shared cancellable future helpers (V25)."""
from concurrent.futures import Future
from threading import Event

import pytest

from audioknigi.core import Cancelled
from audioknigi.engine.concurrency import iter_completed_cancellable, shutdown_pool_now


def test_completed_futures_are_yielded_once_without_a_cancel_event():
    first, second = Future(), Future()
    first.set_result("one")
    second.set_result("two")
    assert set(iter_completed_cancellable([first, second])) == {first, second}


def test_pre_cancelled_request_cancels_pending_futures_and_preserves_error():
    pending = Future()
    cancel = Event()
    cancel.set()
    with pytest.raises(Cancelled, match="Операция отменена пользователем"):
        list(iter_completed_cancellable([pending], cancel))
    assert pending.cancelled()


def test_shutdown_cancels_only_pending_futures_and_never_waits():
    class Pool:
        call = None

        def shutdown(self, *, wait, cancel_futures):
            self.call = (wait, cancel_futures)

    pending, completed = Future(), Future()
    completed.set_result(42)
    pool = Pool()
    shutdown_pool_now(pool, [pending, completed])
    assert pending.cancelled()
    assert completed.result() == 42
    assert pool.call == (False, True)


def test_existing_parser_and_analysis_import_paths_reuse_shared_helpers():
    from audioknigi.parsers import knigavuhe, poleknig
    from audioknigi.services import book_analysis_service

    assert poleknig._iter_completed_cancellable is iter_completed_cancellable
    assert knigavuhe._iter_completed_cancellable is iter_completed_cancellable
    assert book_analysis_service._iter_completed_cancellable is iter_completed_cancellable
    assert poleknig._shutdown_pool_now is shutdown_pool_now
    assert knigavuhe._shutdown_pool_now is shutdown_pool_now
