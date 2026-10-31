"""V29 HTTP 206/416 single-stream resume and connection-loss regressions.

No external network calls: all responses are supplied by in-memory fake sessions.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import requests

from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download.resume_validation import (
    is_complete_partial_after_416,
    validate_resumed_206,
)
from audioknigi.download import network as network_module


class FakeResponse:
    def __init__(self, status, headers=None, chunks=(), error=None):
        self.status_code = status
        self.headers = headers or {}
        self.chunks = list(chunks)
        self.error = error
        self.iterated = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)

    def iter_content(self, chunk_size=0):
        self.iterated = True
        yield from self.chunks
        if self.error is not None:
            raise self.error


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, headers, **kwargs):
        self.calls.append(dict(headers))
        assert self.responses, f"unexpected extra HTTP request: {url}"
        return self.responses.pop(0)


class Limiter:
    def consume(self, *_args, **_kwargs):
        pass


class DownloaderHarness(NetworkDownloadMixin):
    cancel_event = None
    _suppress_source_transfer_ui = True

    def _check_cancel(self):
        pass

    def _get_bandwidth_limiter(self):
        return Limiter()

    def _register_active_network_response(self, response):
        pass

    def _unregister_active_network_response(self, response):
        pass

    def record_transfer_metrics(self, *_args):
        pass

    def set_progress(self, *_args):
        pass

    def set_status(self, *_args):
        pass


def _run(monkeypatch, target, responses):
    session = FakeSession(responses)
    monkeypatch.setattr(network_module, "get_http_session", lambda: session)
    return session, DownloaderHarness()


@pytest.mark.parametrize("header", ["bytes */4", "bytes 0-3/4", "/4", "Bytes * / 4"])
def test_416_complete_partial_recognizes_existing_cdn_variants(header):
    assert is_complete_partial_after_416(4, header)


@pytest.mark.parametrize("header", ["", "bytes */8", "bytes */3", "not a range"])
def test_416_does_not_promote_partial_when_total_does_not_match(header):
    assert not is_complete_partial_after_416(4, header)
    assert not is_complete_partial_after_416(0, header)


def test_complete_416_promotes_existing_partial_without_redownloading(monkeypatch, tmp_path):
    target = tmp_path / "book.mp3"
    part = Path(str(target) + ".part")
    part.write_bytes(b"full")
    response = FakeResponse(416, {"content-range": "bytes */4"})
    session, loader = _run(monkeypatch, target, [response])

    assert loader._download_single("https://cdn.invalid/book.mp3", target, "") == target
    assert target.read_bytes() == b"full"
    assert not part.exists()
    assert not response.iterated
    assert len(session.calls) == 1
    assert session.calls[0]["Range"] == "bytes=4-"


def test_aligned_206_appends_exact_missing_tail(monkeypatch, tmp_path):
    target = tmp_path / "book.mp3"
    Path(str(target) + ".part").write_bytes(b"head")
    response = FakeResponse(
        206, {"content-range": "bytes 4-7/8", "content-length": "4"}, [b"tail"],
    )
    session, loader = _run(monkeypatch, target, [response])

    assert loader._download_single("https://cdn.invalid/book.mp3", target, "") == target
    assert target.read_bytes() == b"headtail"
    assert session.calls[0]["Range"] == "bytes=4-"


@pytest.mark.parametrize("header", ["bytes 0-3/8", "", "bytes 5-7/8", "bytes 4-3/8", "bytes 4-9/8"])
def test_invalid_resumed_206_preserves_partial_and_never_appends(monkeypatch, tmp_path, header):
    target = tmp_path / "book.mp3"
    part = Path(str(target) + ".part")
    part.write_bytes(b"head")
    response = FakeResponse(
        206, {"content-range": header, "content-length": "4"}, [b"tail"],
    )
    session, loader = _run(monkeypatch, target, [response])

    with pytest.raises(RuntimeError, match="Content-Range"):
        loader._download_single("https://cdn.invalid/book.mp3", target, "")
    assert part.read_bytes() == b"head"
    assert not target.exists()
    assert not response.iterated
    assert len(session.calls) == 1


def test_resumed_206_validation_accepts_whitespace_around_slash():
    validate_resumed_206(4, "bytes 4-7 / 8")


def test_server_200_replaces_stale_partial_without_appending(monkeypatch, tmp_path):
    target = tmp_path / "book.mp3"
    Path(str(target) + ".part").write_bytes(b"old")
    session, loader = _run(monkeypatch, target, [
        FakeResponse(200, {"content-length": "5"}, [b"fresh"]),
    ])
    assert loader._download_single("https://cdn.invalid/book.mp3", target, "") == target
    assert target.read_bytes() == b"fresh"
    assert session.calls[0]["Range"] == "bytes=3-"


def test_interrupted_response_preserves_partial_then_resumes(monkeypatch, tmp_path):
    target = tmp_path / "book.mp3"
    part = Path(str(target) + ".part")
    interrupted = FakeResponse(
        200, {"content-length": "7"}, [b"abc"],
        error=requests.ConnectionError("stream disconnected"),
    )
    resumed = FakeResponse(
        206, {"content-range": "bytes 3-6/7", "content-length": "4"}, [b"defg"],
    )
    session, loader = _run(monkeypatch, target, [interrupted, resumed])
    with pytest.raises(RuntimeError, match="Сетевая ошибка"):
        loader._download_single("https://cdn.invalid/book.mp3", target, "")
    assert part.read_bytes() == b"abc"
    assert not target.exists()

    assert loader._download_single("https://cdn.invalid/book.mp3", target, "") == target
    assert target.read_bytes() == b"abcdefg"
    assert "Range" not in session.calls[0]
    assert session.calls[1]["Range"] == "bytes=3-"


def test_stale_416_restarts_only_once_from_zero(monkeypatch, tmp_path):
    target = tmp_path / "book.mp3"
    Path(str(target) + ".part").write_bytes(b"stale")
    session, loader = _run(monkeypatch, target, [
        FakeResponse(416, {"content-range": "bytes */9"}),
        FakeResponse(200, {"content-length": "5"}, [b"fresh"]),
    ])
    assert loader._download_single("https://cdn.invalid/book.mp3", target, "") == target
    assert target.read_bytes() == b"fresh"
    assert session.calls[0]["Range"] == "bytes=5-"
    assert "Range" not in session.calls[1]
    assert len(session.calls) == 2


def test_second_416_is_not_retried_again(monkeypatch, tmp_path):
    target = tmp_path / "book.mp3"
    Path(str(target) + ".part").write_bytes(b"stale")
    session, loader = _run(monkeypatch, target, [
        FakeResponse(416, {"content-range": "bytes */9"}),
        FakeResponse(416, {"content-range": "bytes */9"}),
    ])
    with pytest.raises(RuntimeError, match="Сетевая ошибка"):
        loader._download_single("https://cdn.invalid/book.mp3", target, "")
    assert len(session.calls) == 2
    assert not target.exists()
