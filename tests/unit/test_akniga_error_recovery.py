"""Regression tests for Akniga's Windows file locks and local DNS proxy errors."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi import akniga
from audioknigi.download import network

URL = "https://akniga.org/glubina-pogruzhenie-76-e"
HLS = "https://media.example.test/a.m3u8"


@pytest.mark.parametrize("dns_mode, expected_attempts", [("auto", [False, True]), ("cloudflare", [False])])
def test_akniga_only_retries_proxy_failure_if_auto_dns(monkeypatch, dns_mode, expected_attempts):
    launches = []
    closes = []

    class Page:
        def on(self, *_args):
            pass

        def goto(self, *_args, **_kwargs):
            if launches[-1] is False:
                raise RuntimeError("Page.goto: net::ERR_TUNNEL_CONNECTION_FAILED")

        def content(self):
            return "<section data-bid='123'></section><script>LIVESTREET_SECURITY_KEY = 'abc'</script>"

    class Context:
        def new_page(self):
            return Page()

        def close(self):
            closes.append("context")

    class Browser:
        def new_context(self, **_kwargs):
            return Context()

        def close(self):
            closes.append("browser")

    def launch(_type, *, use_system_dns=False):
        launches.append(use_system_dns)
        return Browser()

    @contextmanager
    def playwright():
        yield SimpleNamespace(chromium=object())

    monkeypatch.setattr(akniga, "sync_playwright", playwright)
    monkeypatch.setattr(akniga, "launch_playwright_chromium", launch)
    monkeypatch.setattr(akniga, "current_dns_mode", lambda: dns_mode)
    monkeypatch.setattr(akniga, "_api_data", lambda *args: {"items": []})
    monkeypatch.setattr(akniga, "_find_hls", lambda *args: HLS)
    monkeypatch.setattr(akniga, "_parse_api_book", lambda *args: "parsed-book")
    if dns_mode == "auto":
        assert akniga.fetch_book(URL) == "parsed-book"
    else:
        with pytest.raises(RuntimeError, match="ERR_TUNNEL_CONNECTION_FAILED"):
            akniga.fetch_book(URL)
    assert launches == expected_attempts
    assert closes == ["context", "browser"] * len(expected_attempts)


def test_hls_preserves_other_process_old_part_and_stages_uniquely(monkeypatch, tmp_path):
    monkeypatch.setattr(network, "resolve_executable", lambda _: "fake-ffmpeg")
    monkeypatch.setattr(network, "hidden_subprocess_kwargs", lambda: {})
    requested_outputs = []

    class FakeProcess:
        returncode = 0

        def poll(self):
            return 0

    def fake_popen(cmd, **_kwargs):
        output = Path(cmd[-1])
        requested_outputs.append(output)
        assert output.name != "_source.mp3.part"
        output.write_bytes(b"ID3mock-audio")
        return FakeProcess()

    monkeypatch.setattr(network.subprocess, "Popen", fake_popen)

    class Engine:
        def _check_cancel(self):
            pass

        def set_status(self, _message):
            pass

        def _register_active_subprocess(self, _proc):
            pass

        def _unregister_active_subprocess(self, _proc):
            pass

    target = tmp_path / "_source.mp3"
    old_part = tmp_path / "_source.mp3.part"
    old_part.write_bytes(b"held-by-another-process")
    result = network.NetworkDownloadMixin._download_hls_to_mp3(Engine(), HLS, target, URL)
    assert result == target
    assert target.read_bytes() == b"ID3mock-audio"
    assert old_part.read_bytes() == b"held-by-another-process"
    assert all(not p.exists() for p in requested_outputs)
    assert all(p.parent == tmp_path for p in requested_outputs)
