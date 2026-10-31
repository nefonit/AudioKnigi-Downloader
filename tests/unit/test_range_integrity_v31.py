"""V31: streamed HTTP 206 bodies must respect their Content-Range bounds."""

from pathlib import Path

import pytest

from audioknigi.download import network as network_module
from audioknigi.download.errors import RangeUnsupported
from audioknigi.download.network import NetworkDownloadMixin


class Response:
    def __init__(self, content_range, chunks):
        self.status_code = 206
        self.headers = {"content-range": content_range}
        self.chunks = list(chunks)
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.closed = True
        return False

    def iter_content(self, chunk_size=0):
        yield from self.chunks


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers_seen = []

    def get(self, _url, *, headers, **_kwargs):
        self.headers_seen.append(dict(headers))
        assert self.responses, "unexpected extra HTTP request"
        return self.responses.pop(0)


class Limiter:
    def consume(self, *_args, **_kwargs):
        pass


class Harness(NetworkDownloadMixin):
    cancel_event = None

    def __init__(self):
        self.changes = []
        self.logs = []

    def _check_cancel(self):
        pass

    def _get_bandwidth_limiter(self):
        return Limiter()

    def _register_active_network_response(self, response):
        pass

    def _unregister_active_network_response(self, response):
        pass

    def log(self, msg):
        self.logs.append(msg)

    def progress(self, amount, force=False):
        self.changes.append(amount)


def run(monkeypatch, tmp_path, responses, *, initial=b"", end=7):
    part = tmp_path / "book.part.seg000"
    if initial:
        part.write_bytes(initial)
    session = Session(responses)
    monkeypatch.setattr(network_module, "get_http_session", lambda: session)
    harness = Harness()
    return part, session, harness


def transfer(harness, part, *, end=7):
    return harness._download_segment(
        "https://cdn.invalid/audio.mp3",
        part,
        0,
        end,
        "https://book.invalid/",
        harness.progress,
    )


def test_exact_206_body_is_written(monkeypatch, tmp_path):
    response = Response("bytes 0-7/8", [b"abcd", b"efgh"])
    part, session, harness = run(monkeypatch, tmp_path, [response])
    assert transfer(harness, part) == 8
    assert part.read_bytes() == b"abcdefgh"
    assert sum(harness.changes) == 8
    assert len(session.headers_seen) == 1
    assert response.closed


def test_short_but_correct_206_is_followed_by_missing_offset(monkeypatch, tmp_path):
    first = Response("bytes 0-3/8", [b"abcd"])
    second = Response("bytes 4-7/8", [b"efgh"])
    part, session, harness = run(monkeypatch, tmp_path, [first, second])
    assert transfer(harness, part) == 8
    assert part.read_bytes() == b"abcdefgh"
    assert [item["Range"] for item in session.headers_seen] == [
        "bytes=0-7", "bytes=4-7",
    ]
    assert sum(harness.changes) == 8


@pytest.mark.parametrize("payload", [[b"ABCDE"], [b"abcd", b"e"]])
def test_oversized_response_is_rejected_and_rolled_back(monkeypatch, tmp_path, payload):
    response = Response("bytes 0-3/8", payload)
    part, session, harness = run(monkeypatch, tmp_path, [response])
    with pytest.raises(RangeUnsupported, match="длиннее Content-Range"):
        transfer(harness, part)
    assert part.read_bytes() == b""
    assert sum(harness.changes) == 0
    assert response.closed
    assert len(session.headers_seen) == 1


def test_oversized_later_response_preserves_preexisting_verified_segment(monkeypatch, tmp_path):
    first = Response("bytes 4-5/8", [b"ef", b"x"])
    part, session, harness = run(monkeypatch, tmp_path, [first], initial=b"abcd")
    with pytest.raises(RangeUnsupported, match="Content-Range"):
        transfer(harness, part)
    assert part.read_bytes() == b"abcd"
    assert sum(harness.changes) == 0
    assert session.headers_seen[0]["Range"] == "bytes=4-7"


def test_large_body_after_entire_expected_window_is_not_silently_ignored(monkeypatch, tmp_path):
    response = Response("bytes 0-3/4", [b"abcd", b"extra"])
    part, _, harness = run(monkeypatch, tmp_path, [response])
    with pytest.raises(RangeUnsupported, match="Content-Range"):
        transfer(harness, part, end=3)
    assert part.read_bytes() == b""
    assert sum(harness.changes) == 0


@pytest.mark.parametrize("header", ["bytes 0-3/3", "bytes 0-7/7", "bytes 0-0/0"])
def test_inconsistent_range_total_is_rejected_before_file_creation(monkeypatch, tmp_path, header):
    response = Response(header, [b"audio"])
    part, _, harness = run(monkeypatch, tmp_path, [response])
    with pytest.raises(RangeUnsupported, match="Некорректный Content-Range"):
        transfer(harness, part)
    assert not part.exists()
    assert harness.changes == []


def test_range_exceeding_requested_segment_is_still_rejected(monkeypatch, tmp_path):
    response = Response("bytes 0-8/9", [b"123456789"])
    part, _, harness = run(monkeypatch, tmp_path, [response])
    with pytest.raises(RangeUnsupported, match="за пределами запрошенного сегмента"):
        transfer(harness, part)
    assert not part.exists()


def test_clean_short_read_remains_resumable_at_exact_missing_byte(monkeypatch, tmp_path):
    first = Response("bytes 0-7/8", [b"abc"])
    next_response = Response("bytes 3-7/8", [b"defgh"])
    part, session, harness = run(monkeypatch, tmp_path, [first, next_response])
    assert transfer(harness, part) == 8
    assert part.read_bytes() == b"abcdefgh"
    assert [item["Range"] for item in session.headers_seen] == [
        "bytes=0-7", "bytes=3-7",
    ]
