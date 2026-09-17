from __future__ import annotations

import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import audioknigi.event_bus as event_bus_module
from audioknigi.downloader import DownloaderMixin, MissingMediaSourceError
from audioknigi.event_bus import UIEventBus
from audioknigi.models import Book, QueueItem, Track
from audioknigi.queue_manager import QueueMixin


class _FakeRoot:
    def __init__(self):
        self.after_calls = []
        self.cancelled = []

    def after(self, interval, callback):
        token = f"after-{len(self.after_calls) + 1}"
        self.after_calls.append((interval, callback, token))
        return token

    def after_cancel(self, token):
        self.cancelled.append(token)


def test_event_bus_logs_callback_failure_and_keeps_pumping(monkeypatch):
    root = _FakeRoot()
    bus = UIEventBus(root, interval_ms=25, max_batch=10)
    seen = []
    logged = []

    def bad_callback():
        raise RuntimeError("boom from queued UI callback")

    def good_callback():
        seen.append("good")

    def fake_log_exception(context, exc_info=None, **_kwargs):
        logged.append((context, exc_info[1] if isinstance(exc_info, tuple) else None))

    monkeypatch.setattr(event_bus_module, "log_exception", fake_log_exception)
    monkeypatch.setattr(sys, "stderr", None)

    bus.post(bad_callback)
    bus.post(good_callback)
    bus._drain()

    assert seen == ["good"]
    assert len(logged) == 1
    assert "bad_callback" in logged[0][0]
    assert isinstance(logged[0][1], RuntimeError)
    # One initial schedule from __init__, then another schedule after the drain.
    assert len(root.after_calls) == 2
    assert bus._after_id == "after-2"


def test_event_bus_rearms_even_if_diagnostics_fail(monkeypatch):
    root = _FakeRoot()
    bus = UIEventBus(root)

    monkeypatch.setattr(event_bus_module, "log_exception", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("logger failed")))
    bus.post(lambda: (_ for _ in ()).throw(ValueError("callback failed")))

    bus._drain()

    assert len(root.after_calls) == 2
    assert bus._after_id == "after-2"


class _QueueHost(QueueMixin):
    def __init__(self):
        self.queue_items = [QueueItem(url="u", status="Ожидает повтор", status_code="retry_pending")]
        self.queue_running = False
        self.queue_tree = SimpleNamespace(selection=lambda: ("0",))
        self._queue_lock = threading.RLock()
        self.refreshes = 0

    def _refresh_queue(self):
        self.refreshes += 1


def test_item_pause_restores_semantic_status_code():
    host = _QueueHost()
    item = host.queue_items[0]

    host.queue_toggle_item_pause()
    assert item.paused is True
    assert item.status == "На паузе"
    assert item.status_code == "paused"
    assert item.status_before_pause == "Ожидает повтор"
    assert item.status_code_before_pause == "retry_pending"

    host.queue_toggle_item_pause()
    assert item.paused is False
    assert item.status == "Ожидает повтор"
    assert item.status_code == "retry_pending"
    assert item.status_before_pause == ""
    assert item.status_code_before_pause == ""


class _RefreshOnceHost(DownloaderMixin):
    def __init__(self):
        self.calls = 0
        self.refreshes = 0
        self.prompts = []
        self.messages = []
        self.skipped = []

    def _process_book_once(self, _book, selected, _status=None):
        self.calls += 1
        selected = set(selected)
        if self.calls == 1:
            raise MissingMediaSourceError("HTTP 404", source_url="old-1", track_indices=[1])
        if self.calls == 2:
            raise MissingMediaSourceError("HTTP 404", source_url="fresh-1", track_indices=[1])
        if self.calls == 3:
            assert selected == {2, 3}
            raise MissingMediaSourceError("HTTP 404", source_url="fresh-2", track_indices=[2])
        assert selected == {3}
        return "done"

    def _refresh_book_media_playlist(self, _book, _selected):
        self.refreshes += 1
        return 1

    def _ask_missing_media_action(self, indices, **_kwargs):
        self.prompts.append(tuple(indices))
        return "skip"

    def _clear_stale_source_downloads(self, _book):
        return None

    def _record_skipped_media_parts(self, indices):
        self.skipped.extend(indices)


def test_playlist_is_refreshed_at_most_once_per_book_run():
    host = _RefreshOnceHost()
    book = Book(
        url="https://audioknigi.com.ua/book",
        title="Book",
        tracks=[
            Track(1, "One", "old-1"),
            Track(2, "Two", "old-2"),
            Track(3, "Three", "old-3"),
        ],
    )

    assert host._process_book(book, [1, 2, 3]) == "done"
    assert host.refreshes == 1
    assert host.prompts == [(1,), (2,)]
    assert host.skipped == [1, 2]


def test_event_bus_never_relies_on_stderr_printing():
    source = (Path(__file__).resolve().parents[1] / "audioknigi" / "event_bus.py").read_text(encoding="utf-8")
    assert "traceback.print_exc" not in source
    assert "print_exc(" not in source
