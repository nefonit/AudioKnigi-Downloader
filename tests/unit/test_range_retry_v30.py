"""V30: temporary HTTP errors must preserve Range offsets and bounded retries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest
import requests

from audioknigi.core import Cancelled
from audioknigi.download import network as network_module
from audioknigi.download.errors import RangeUnsupported
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download.range_retry import bounded_range_retry_delay


class FakeResponse:
    def __init__(self, status, headers=None, chunks=(), error=None):
        self.status_code = status
        self.headers = headers or {}
        self.chunks = list(chunks)
        self.error = error
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.closed = True
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)

    def iter_content(self, chunk_size=0):
        yield from self.chunks
        if self.error:
            raise self.error


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, _url, *, headers, **_kwargs):
        self.calls.append(dict(headers))
        assert self.responses, "unexpected HTTP request: retry count exceeded"
        return self.responses.pop(0)


class RecordingEvent:
    def __init__(self, trigger_on_wait=False):
        self.waits = []
        self._set = False
        self.trigger_on_wait = trigger_on_wait

    def wait(self, seconds):
        self.waits.append(seconds)
        if self.trigger_on_wait:
            self._set = True
        return self._set

    def is_set(self):
        return self._set


class Limiter:
    def consume(self, *_args, **_kwargs):
        pass


class SegmentHarness(NetworkDownloadMixin):
    def __init__(self, *, cancel_event=None):
        self.cancel_event = cancel_event if cancel_event is not None else RecordingEvent()
        self.logs = []
        self.progress = []

    def _check_cancel(self):
        if self.cancel_event.is_set():
            raise Cancelled("Операция отменена пользователем.")

    def _get_bandwidth_limiter(self):
        return Limiter()

    def _register_active_network_response(self, response):
        pass

    def _unregister_active_network_response(self, response):
        pass

    def log(self, message):
        self.logs.append(message)


def _setup(monkeypatch, responses, *, cancel_event=None):
    session = FakeSession(responses)
    monkeypatch.setattr(network_module, "get_http_session", lambda: session)
    harness = SegmentHarness(cancel_event=cancel_event)
    return session, harness


def _download(harness, path, *, peer_abort_event=None):
    return harness._download_segment(
        "https://cdn.invalid/audio.mp3", path, 0, 7, "https://book.invalid/",
        lambda count, **_kwargs: harness.progress.append(count),
        peer_abort_event=peer_abort_event,
    )


def test_existing_retry_delay_unchanged_without_server_header():
    assert bounded_range_retry_delay(1) == pytest.approx(0.15)
    assert bounded_range_retry_delay(3) == pytest.approx(0.45)
    assert bounded_range_retry_delay(20) == pytest.approx(1.0)


@pytest.mark.parametrize("hint,expected", [
    ("0.5", 0.5), ("1", 1.0), ("120", 1.0),
    ("nan", 0.15), ("inf", 0.15),
    ("-5", 0.15), ("garbage", 0.15), ("", 0.15),
])
def test_retry_after_is_never_unbounded(hint, expected):
    assert bounded_range_retry_delay(1, hint) == pytest.approx(expected)


def test_retry_after_http_date_is_bounded_and_past_dates_are_ignored():
    now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    later = format_datetime(now + timedelta(seconds=30), usegmt=True)
    earlier = format_datetime(now - timedelta(seconds=30), usegmt=True)
    assert bounded_range_retry_delay(1, later, now=now) == 1.0
    assert bounded_range_retry_delay(1, earlier, now=now) == pytest.approx(0.15)


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_transient_http_status_retries_exact_same_offset_and_preserves_bytes(monkeypatch, tmp_path, status):
    seg = tmp_path / "part.seg000"
    seg.write_bytes(b"head")
    first = FakeResponse(status, {"Retry-After": "0.7"})
    second = FakeResponse(206, {"content-range": "bytes 4-7/8"}, [b"tail"])
    session, harness = _setup(monkeypatch, [first, second])
    assert _download(harness, seg) == 8
    assert seg.read_bytes() == b"headtail"
    assert [h["Range"] for h in session.calls] == ["bytes=4-7", "bytes=4-7"]
    assert harness.cancel_event.waits == [pytest.approx(0.7)]
    assert first.closed and second.closed


@pytest.mark.parametrize("status", [404, 410])
def test_permanent_missing_source_surfaces_without_retry(monkeypatch, tmp_path, status):
    seg = tmp_path / "part.seg000"
    seg.write_bytes(b"head")
    session, harness = _setup(monkeypatch, [FakeResponse(status)])
    with pytest.raises(requests.HTTPError):
        _download(harness, seg)
    assert len(session.calls) == 1
    assert seg.read_bytes() == b"head"
    assert harness.cancel_event.waits == []


def test_repeated_transient_failure_stops_after_five_attempts(monkeypatch, tmp_path):
    seg = tmp_path / "part.seg000"
    seg.write_bytes(b"head")
    responses = [FakeResponse(503, {"Retry-After": "300"}) for _ in range(5)]
    session, harness = _setup(monkeypatch, responses)
    with pytest.raises(RuntimeError, match="Сетевая ошибка Range после повторов"):
        _download(harness, seg)
    assert len(session.calls) == 5
    assert seg.read_bytes() == b"head"
    assert len(harness.cancel_event.waits) == 4
    assert all(0 < seconds <= 1.0 for seconds in harness.cancel_event.waits)


def test_stream_interruption_plus_503_resumes_at_first_missing_byte(monkeypatch, tmp_path):
    seg = tmp_path / "part.seg000"
    seg.write_bytes(b"abc")
    interrupted = FakeResponse(206, {"content-range": "bytes 3-7/8"}, [b"de"],
                               requests.ConnectionError("socket closed"))
    temporary = FakeResponse(503, {"Retry-After": "1"})
    resumed = FakeResponse(206, {"content-range": "bytes 5-7/8"}, [b"fgh"])
    session, harness = _setup(monkeypatch, [interrupted, temporary, resumed])
    assert _download(harness, seg) == 8
    assert seg.read_bytes() == b"abcdefgh"
    assert [call["Range"] for call in session.calls] == [
        "bytes=3-7", "bytes=5-7", "bytes=5-7",
    ]
    assert harness.cancel_event.waits == [1.0]


def test_user_cancellation_during_retry_delay_stops_before_next_request(monkeypatch, tmp_path):
    seg = tmp_path / "part.seg000"
    seg.write_bytes(b"head")
    cancel = RecordingEvent(trigger_on_wait=True)
    session, harness = _setup(monkeypatch, [FakeResponse(429, {"Retry-After": "1"})],
                              cancel_event=cancel)
    with pytest.raises(Cancelled):
        _download(harness, seg)
    assert len(session.calls) == 1
    assert seg.read_bytes() == b"head"
    assert cancel.waits == [1.0]


def test_peer_abort_during_retry_delay_stops_worker_quietly(monkeypatch, tmp_path):
    seg = tmp_path / "part.seg000"
    seg.write_bytes(b"head")
    peer = RecordingEvent(trigger_on_wait=True)
    session, harness = _setup(monkeypatch, [FakeResponse(503, {"Retry-After": "1"})])
    assert _download(harness, seg, peer_abort_event=peer) == 4
    assert len(session.calls) == 1
    assert seg.read_bytes() == b"head"
    assert peer.waits == [1.0]
    assert harness.cancel_event.waits == []


def test_416_still_uses_range_unsupported_instead_of_retry(monkeypatch, tmp_path):
    seg = tmp_path / "part.seg000"
    seg.write_bytes(b"head")
    session, harness = _setup(monkeypatch, [FakeResponse(416)])
    with pytest.raises(RangeUnsupported):
        _download(harness, seg)
    assert len(session.calls) == 1
    assert seg.read_bytes() == b"head"
