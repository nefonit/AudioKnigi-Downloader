from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
import requests

import audioknigi.downloader as downloader_module
from audioknigi.downloader import DownloaderMixin
from audioknigi.network_dns import cloudflare_playwright_launch_kwargs, launch_playwright_chromium


ROOT = Path(__file__).resolve().parents[1]


def test_playwright_network_dns_keeps_compat_api_and_services_use_launcher():
    assert callable(cloudflare_playwright_launch_kwargs)
    assert callable(launch_playwright_chromium)
    analysis = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    poleknig = (ROOT / "audioknigi/poleknig.py").read_text(encoding="utf-8")
    assert "launch_playwright_chromium(playwright.chromium)" in analysis
    assert "launch_playwright_chromium(pw.chromium)" in poleknig


def test_audio_probe_cache_retains_multiple_sources(tmp_path):
    class Dummy(DownloaderMixin):
        def __init__(self):
            self.calls = []

        def _probe_audio_info(self, path):
            self.calls.append(Path(path).name)
            return {"codec": "mp3", "duration": 1.0}

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    dummy = Dummy()

    dummy._cached_probe_audio_info(a)
    dummy._cached_probe_audio_info(b)
    dummy._cached_probe_audio_info(a)

    assert dummy.calls == ["a.mp3", "b.mp3"]
    assert len(dummy._audio_info_cache) == 2


def test_audio_probe_cache_is_thread_safe_for_same_source(tmp_path):
    class Dummy(DownloaderMixin):
        def __init__(self):
            self.calls = 0

        def _probe_audio_info(self, path):
            self.calls += 1
            time.sleep(0.03)
            return {"codec": "mp3", "duration": 1.0}

    source = tmp_path / "shared.mp3"
    source.write_bytes(b"x")
    dummy = Dummy()
    barrier = threading.Barrier(8)
    results = []

    def worker():
        barrier.wait()
        results.append(dummy._cached_probe_audio_info(source))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2.0)

    assert all(not thread.is_alive() for thread in threads)
    assert dummy.calls == 1
    assert len(results) == 8
    assert all(item["codec"] == "mp3" for item in results)


@pytest.mark.parametrize("status", [404, 410])
def test_range_expired_media_does_not_retry_same_url(monkeypatch, tmp_path, status):
    class FakeResponse:
        def __init__(self):
            self.status_code = status
            self.headers = {}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            err = requests.HTTPError(f"HTTP {status}")
            err.response = self
            raise err

    class FakeSession:
        def __init__(self):
            self.calls = 0

        def get(self, *args, **kwargs):
            self.calls += 1
            return FakeResponse()

    class DummyLimiter:
        def consume(self, amount, cancel_event):
            return None

    class Dummy(DownloaderMixin):
        def __init__(self):
            self.cancel_event = threading.Event()

        def _check_cancel(self):
            return None

        def _get_bandwidth_limiter(self):
            return DummyLimiter()

        def _register_active_network_response(self, response):
            return None

        def _unregister_active_network_response(self, response):
            return None

        def log(self, message):
            return None

    session = FakeSession()
    monkeypatch.setattr(downloader_module, "get_http_session", lambda: session)
    seg = tmp_path / "part.seg"

    with pytest.raises(requests.HTTPError) as caught:
        Dummy()._download_segment(
            "https://cdn.example/expired.mp3",
            seg,
            0,
            1023,
            "https://example/book",
            lambda *args, **kwargs: None,
        )

    assert caught.value.response.status_code == status
    assert session.calls == 1


def test_core_has_no_stale_urlparse_import_and_main_window_core_import_is_single_block():
    core = (ROOT / "audioknigi/core.py").read_text(encoding="utf-8")
    window = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert "from urllib.parse import urlparse" not in core
    assert window.count("from ..core import") == 1
