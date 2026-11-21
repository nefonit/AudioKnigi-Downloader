"""V37: HLS cancellation, response lifecycle, FFmpeg proxy and UI localization."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from audioknigi.core import Cancelled
from audioknigi.download import hls_parallel
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.i18n import localize_runtime_text

_URL = "https://audio.example.org/book/list.m3u8"
_MANIFEST = (
    b"#EXTM3U\n#EXTINF:3.0,\none.ts\n#EXTINF:3.0,\ntwo.ts\n#EXT-X-ENDLIST\n"
)


def test_parallel_hls_cancel_is_polled_without_completed_segments(monkeypatch, tmp_path):
    monkeypatch.setattr(hls_parallel, "_get_bytes", lambda *_a, **_kw: _MANIFEST)
    cancellation = threading.Event()
    workers_started = threading.Event()

    def stalled_download(_index, _url, _dest, _headers, _check_cancel, stop_event, **_kw):
        workers_started.set()
        # Real stream reads can block. The coordinating thread must poll
        # cancellation independently of segment future completion.
        if stop_event.wait(2.0):
            raise Cancelled("stopped by coordinator")
        raise RuntimeError("simulated CDN stall")

    monkeypatch.setattr(hls_parallel, "_download_segment", stalled_download)

    def check_cancel():
        if cancellation.is_set():
            raise Cancelled("cancelled by user")

    def request_cancel():
        assert workers_started.wait(1.0)
        cancellation.set()

    trigger = threading.Thread(target=request_cancel, daemon=True)
    trigger.start()
    begin = time.monotonic()
    with pytest.raises(Cancelled, match="cancelled by user"):
        hls_parallel.stage_hls_vod(
            _URL, tmp_path / "stage", referer="", user_agent="test",
            check_cancel=check_cancel, on_progress=lambda *_: None,
            max_workers=2,
        )
    assert time.monotonic() - begin < 1.0
    trigger.join(timeout=1)


def test_hls_http_error_closes_streamed_response(monkeypatch):
    class BrokenResponse:
        is_redirect = False
        headers = {}

        def __init__(self):
            self.closed = False

        def raise_for_status(self):
            raise requests.HTTPError("HTTP 404: playlist expired", response=self)

        def close(self):
            self.closed = True

    response = BrokenResponse()
    monkeypatch.setattr(hls_parallel, "get_http_session", lambda: SimpleNamespace(
        get=lambda *_a, **_kw: response
    ))
    with pytest.raises(requests.HTTPError):
        hls_parallel._open_checked_response(_URL, {})
    assert response.closed is True


def test_hls_response_registration_balanced_for_playlist_and_segments(monkeypatch, tmp_path):
    events = []

    class Response:
        headers = {"Content-Length": "5"}

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            events.append("close")

        def iter_content(self, **_kw):
            yield b"hello"

    monkeypatch.setattr(hls_parallel, "_open_checked_response", lambda *_a, **_kw: Response())
    register = lambda _r: events.append("register")
    unregister = lambda _r: events.append("unregister")
    data = hls_parallel._get_bytes(
        _URL, {}, lambda: None,
        register_response=register, unregister_response=unregister,
    )
    assert data == b"hello"
    assert events == ["register", "unregister", "close"]
    events.clear()
    dest = tmp_path / "seq000000.ts"
    index, size = hls_parallel._download_segment(
        0, "https://audio.example.org/one.ts", dest, {}, lambda: None,
        threading.Event(), register_response=register, unregister_response=unregister,
    )
    assert (index, size) == (0, 5)
    assert dest.read_bytes() == b"hello"
    assert events == ["register", "unregister", "close"]


@pytest.mark.parametrize("url,proxy_expected", [
    ("https://audio.example.org/master.m3u8", True),
    ("https://audio.example.org/another.m3u8", True),
    ("file:///some/file.m3u8", False),
])
def test_ffmpeg_hls_uses_proxy_only_for_remote_input(monkeypatch, tmp_path, url, proxy_expected):
    import audioknigi.download.network as network

    commands = []
    monkeypatch.setattr(network, "resolve_executable", lambda _: "ffmpeg")
    monkeypatch.setattr(
        network, "cloudflare_ffmpeg_input_args",
        lambda: ["-http_proxy", "http://127.0.0.1:9876"],
    )

    class Process:
        stdout = None
        returncode = 0

        def poll(self):
            return 0

        def wait(self, **_kw):
            return 0

    def popen(command, **_kw):
        commands.append(list(command))
        Path(command[-1]).write_bytes(b"fake playable audio")
        return Process()

    monkeypatch.setattr(network.subprocess, "Popen", popen)

    class Engine(NetworkDownloadMixin):
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"
        runtime_hls_parallel_enabled = False

        def _check_cancel(self):
            pass

        def _register_active_subprocess(self, _p):
            pass

        def _unregister_active_subprocess(self, _p):
            pass

        def set_status(self, *_a):
            pass

        def set_progress(self, *_a):
            pass

        def log(self, *_a):
            pass

    output = tmp_path / ("remote.mp3" if proxy_expected else "local.mp3")
    Engine()._run_hls_ffmpeg(url, output, "")
    assert output.exists()
    assert bool("-http_proxy" in commands[0]) is proxy_expected
    if proxy_expected:
        assert commands[0].index("-http_proxy") < commands[0].index("-i")


def test_invalid_chapter_boundary_error_is_localized():
    raw = "Некорректные границы части: конец 10 с не позже начала 25 с."
    assert "Ungültige Kapitelgrenzen" in localize_runtime_text("de", raw)
    assert "Invalid chapter boundaries" in localize_runtime_text("en", raw)
    assert "Некоректні межі частини" in localize_runtime_text("uk", raw)
    assert localize_runtime_text("ru", raw) == raw
