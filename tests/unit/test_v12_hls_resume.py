"""V12: checks for safe HLS resume, honest progress, and prompt cancellation."""
from __future__ import annotations

from contextlib import contextmanager
import threading
import time

import pytest

from audioknigi.core import Cancelled
from audioknigi.download import hls_parallel

URL = "https://audio.example.org/fiction/list.m3u8"
BODY = b"#EXTM3U\n#EXTINF:3.0,\none.ts\n#EXTINF:3.0,\ntwo.ts\n#EXT-X-ENDLIST\n"
THREE = b"#EXTM3U\n#EXTINF:3.0,\none.ts\n#EXTINF:3.0,\ntwo.ts\n#EXTINF:3.0,\nthree.ts\n#EXT-X-ENDLIST\n"


def _stage(tmp_path, name, *, cache, on_progress=None, on_resume=None, workers=1):
    return hls_parallel.stage_hls_vod(
        URL, tmp_path / name, referer="", user_agent="test",
        check_cancel=lambda: None, on_progress=on_progress or (lambda *_: None),
        max_workers=workers, segment_cache_dir=cache, on_resume=on_resume,
    )


def test_restart_reuses_only_completed_segments_and_reports_network_bytes(monkeypatch, tmp_path):
    monkeypatch.setattr(hls_parallel, "_get_bytes", lambda *_a, **_kw: BODY)
    calls = []
    fail = [True]

    def fetch(index, _url, dest, *_args, **_kwargs):
        calls.append(index)
        if index == 1 and fail[0]:
            raise Cancelled("cancel")
        dest.write_bytes(b"12345")
        return index, 5

    monkeypatch.setattr(hls_parallel, "_download_segment", fetch)
    cache = tmp_path / "shared"
    with pytest.raises(Cancelled):
        _stage(tmp_path, "first", cache=cache)
    assert calls == [0, 1]

    # A second invocation represents a fresh download worker/process.
    fail[0] = False
    progress, resumed = [], []
    assert _stage(tmp_path, "second", cache=cache,
                  on_progress=lambda *x: progress.append(x),
                  on_resume=lambda *x: resumed.append(x)).exists()
    assert calls == [0, 1, 1]
    assert resumed == [(1, 2)]
    assert progress[-1] == (2, 2, 5)  # not 10: one segment was reused
    assert (tmp_path / "second" / "seq000000.ts").read_bytes() == b"12345"


def test_clean_early_eof_with_content_length_is_retried_and_not_cached(monkeypatch, tmp_path):
    calls = []

    @contextmanager
    def response(_url, _headers, **_kwargs):
        calls.append(1)
        class FakeResponse:
            headers = {"Content-Length": "12"}
            def iter_content(self, **_kwargs):
                yield b"too-short"
        yield FakeResponse()

    monkeypatch.setattr(hls_parallel, "_open_checked_response", response)
    dest = tmp_path / "seq000000.ts"
    with pytest.raises(IOError, match="Неполный HLS-сегмент"):
        hls_parallel._download_segment(0, "https://audio.example.org/one.ts", dest,
            {}, lambda: None, threading.Event())
    assert len(calls) == 3
    assert not dest.exists()


def test_exact_content_length_is_accepted(monkeypatch, tmp_path):
    @contextmanager
    def response(*_args, **_kwargs):
        class FakeResponse:
            headers = {"Content-Length": "5"}
            def iter_content(self, **_kwargs):
                yield b"hello"
        yield FakeResponse()
    monkeypatch.setattr(hls_parallel, "_open_checked_response", response)
    dest = tmp_path / "ok.ts"
    assert hls_parallel._download_segment(0, "https://audio.example.org/ok.ts", dest,
        {}, lambda: None, threading.Event()) == (0, 5)
    assert dest.read_bytes() == b"hello"


def test_stop_event_signaled_before_pool_waits_on_running_workers(monkeypatch, tmp_path):
    monkeypatch.setattr(hls_parallel, "_get_bytes", lambda *_a, **_kw: THREE)
    other_started = threading.Event()

    def fetch(index, _url, _dest, _headers, _check_cancel, stop_event, **_kw):
        if index == 0:
            assert other_started.wait(0.5)
            raise Cancelled("cancelled")
        other_started.set()
        if not stop_event.wait(1.0):
            raise AssertionError("running worker was not signaled to stop")
        raise RuntimeError("stopped")

    monkeypatch.setattr(hls_parallel, "_download_segment", fetch)
    begin = time.monotonic()
    with pytest.raises(Cancelled):
        _stage(tmp_path, "cancel", cache=tmp_path / "cache", workers=2)
    assert time.monotonic() - begin < 0.8


def test_cache_rejects_stale_checksum_on_restart(monkeypatch, tmp_path):
    monkeypatch.setattr(hls_parallel, "_get_bytes", lambda *_a, **_kw: BODY)
    calls = []
    def fetch(index, _url, dest, *_args, **_kwargs):
        calls.append(index)
        dest.write_bytes(f"part-{index}".encode())
        return index, dest.stat().st_size
    monkeypatch.setattr(hls_parallel, "_download_segment", fetch)
    cache = tmp_path / "cache"
    _stage(tmp_path, "before", cache=cache)
    segment = next(cache.glob("*/seq000000.ts"))
    segment.write_bytes(b"damaged")
    _stage(tmp_path, "after", cache=cache)
    assert calls == [0, 1, 0]  # good segment 1 was not re-fetched
