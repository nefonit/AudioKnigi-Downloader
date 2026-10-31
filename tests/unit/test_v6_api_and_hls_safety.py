"""V6: bounded GraphQL reads, truthful network labels, HLS publish safety."""
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from audioknigi.core import Cancelled, SiteStructureChanged
from audioknigi.providers import extra_sources as extra
from audioknigi.services import source_health_service as health
from audioknigi.download import network


def test_graphql_read_only_retries_once_then_succeeds(monkeypatch):
    called = []
    class Response:
        def json(self):
            return {"data": {"search": []}}
    def request(url, *, json_payload=None, cancel_event=None):
        called.append((url, json_payload))
        if len(called) == 1:
            raise requests.exceptions.ProxyError("secret=DO-NOT-PRINT")
        return Response()
    monkeypatch.setattr(extra, "_request", request)
    assert extra._yakniga_payload({"query": "query ($term: String!) { search(term:$term) { title } }", "variables": {"term": "test"}}) == {"search": []}
    assert len(called) == 2
    assert extra._YAKNIGA_QUERY_TIMEOUT == (3, 5)


def test_graphql_read_only_stops_after_two_network_failures(monkeypatch):
    calls = []
    def request(*args, **kwargs):
        calls.append(1)
        raise requests.exceptions.ConnectTimeout("blocked")
    monkeypatch.setattr(extra, "_request", request)
    with pytest.raises(requests.exceptions.ConnectTimeout):
        extra._yakniga_payload({"query": "query Test { search { title } }"})
    assert len(calls) == 2


def test_graphql_non_read_only_or_bad_response_never_retried(monkeypatch):
    calls = []
    def request(*args, **kwargs):
        calls.append(1)
        raise requests.exceptions.ReadTimeout("timeout")
    monkeypatch.setattr(extra, "_request", request)
    with pytest.raises(requests.exceptions.ReadTimeout):
        extra._yakniga_payload({"query": "mutation { changeBook }"})
    assert len(calls) == 1
    monkeypatch.setattr(extra, "_request", lambda *a, **kw: SimpleNamespace(json=lambda: {"data": None}))
    with pytest.raises(SiteStructureChanged, match="неверные данные"):
        extra._yakniga_payload({"query": "query { search { title } }"})


def test_graphql_cancelled_prevents_retry(monkeypatch):
    from threading import Event
    event = Event()
    calls = []
    def request(*args, **kwargs):
        calls.append(1)
        event.set()
        raise requests.exceptions.ProxyError("failed")
    monkeypatch.setattr(extra, "_request", request)
    with pytest.raises(Cancelled):
        extra._yakniga_payload({"query": "query { search { title } }"}, cancel_event=event)
    assert len(calls) == 1


def test_search_internal_bridge_not_user_proxy(monkeypatch):
    monkeypatch.setattr(health, "current_dns_mode", lambda: health.DNS_MODE_AUTO)
    monkeypatch.setattr(health, "user_proxy_enabled", lambda: False)
    class Provider:
        key = "yakniga"
        display_name = "yakniga.org"
        def search(self, q):
            raise requests.exceptions.ProxyError("secret_url=https://hidden.test/media?token=123")
    result = health._probe_search(Provider(), "query")
    assert result.reachable is False
    assert "Внутренний DNS-мост" in result.error
    assert "token" not in result.error
    assert result.search_endpoint == "GraphQL POST"
    monkeypatch.setattr(health, "user_proxy_enabled", lambda: True)
    assert health._classify_search_error(requests.exceptions.ProxyError("private")) == "Прокси/туннель: соединение не удалось"


def test_search_api_http_errors_no_sensitive_url():
    response = requests.Response()
    response.status_code = 503
    response.url = 'https://yakniga.org/graphql?secret=x'
    err = requests.exceptions.HTTPError('for secret=x', response=response)
    assert health._classify_search_error(err) == "Поисковый API ответил HTTP 503"
    assert health._classify_search_error(SiteStructureChanged("private data")) == "Ответ поискового API не соответствует ожидаемой структуре"


def test_hls_short_audio_never_overwrites_existing_target(monkeypatch, tmp_path):
    monkeypatch.setattr(network, "resolve_executable", lambda _: "fake-ffmpeg")
    monkeypatch.setattr(network, "hidden_subprocess_kwargs", lambda: {})
    temporary_files = []
    class Process:
        returncode = 0
        def poll(self): return 0
    def popen(cmd, **kwargs):
        p = Path(cmd[-1])
        temporary_files.append(p)
        p.write_bytes(b"valid-but-incomplete-media")
        return Process()
    monkeypatch.setattr(network.subprocess, "Popen", popen)
    class Engine:
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"
        runtime_hls_parallel_enabled = False
        def _check_cancel(self): pass
        def _register_active_subprocess(self, p): pass
        def _unregister_active_subprocess(self, p): pass
        def set_status(self, message): pass
        def log(self, message): pass
        def _probe_duration(self, file_path): return 1111.176
    target = tmp_path / "_source.mp3"
    target.write_bytes(b"previous-fully-valid-source")
    part = tmp_path / "_source.mp3.part"
    part.write_bytes(b"locked-by-someone-else")
    with pytest.raises(RuntimeError, match="неполный аудиофайл"):
        network.NetworkDownloadMixin._run_hls_ffmpeg(
            Engine(), "https://cdn.example.test/book.m3u8", target,
            "https://akniga.org/book", expected_duration=33015,
        )
    assert target.read_bytes() == b"previous-fully-valid-source"
    assert part.read_bytes() == b"locked-by-someone-else"
    assert temporary_files and all(not p.exists() for p in temporary_files)
