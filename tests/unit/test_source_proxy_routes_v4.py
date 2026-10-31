from __future__ import annotations

from dataclasses import dataclass
import socket
from unittest.mock import Mock

import pytest

from audioknigi import network_dns as nd
from audioknigi.config.settings import normalize_settings
from audioknigi.services import source_health_service as health


@pytest.fixture(autouse=True)
def reset_proxy():
    previous_url = nd.current_user_proxy()
    previous_hosts = ", ".join(nd.current_proxy_hosts())
    previous_mode = nd.current_dns_mode()
    yield
    nd.configure_user_proxy(previous_url)
    nd.configure_proxy_hosts(previous_hosts)
    nd.configure_dns_mode(previous_mode)


def test_proxy_disabled_even_when_hosts_set():
    nd.configure_user_proxy("")
    nd.configure_proxy_hosts("akniga.org, yakniga.org")
    assert not nd.proxy_for_host("akniga.org")


def test_proxy_scoped_hosts_and_subdomains():
    nd.configure_user_proxy("socks5h://localhost:1080")
    nd.configure_proxy_hosts("akniga.org, yakniga.org")
    assert nd.proxy_for_host("akniga.org")
    assert nd.proxy_for_host("www.akniga.org")
    assert nd.proxy_for_host("yakniga.org")
    assert not nd.proxy_for_host("archive.org")
    assert not nd.proxy_for_host("fakeakniga.org")
    assert not nd.proxy_for_host("xn--akniga.org.evil.example")


def test_empty_allowlist_preserves_legacy_global_proxy():
    nd.configure_user_proxy("http://localhost:8080")
    nd.configure_proxy_hosts("")
    assert nd.proxy_for_host("akniga.org")
    assert nd.proxy_for_host("archive.org")


@pytest.mark.parametrize("invalid", ["*.akniga.org", "https://akniga.org", "127.0.0.1:8000", "x", "../a", "foo bar.org", "http://a:123"])
def test_proxy_site_validation_rejects_invalid(invalid):
    with pytest.raises(ValueError):
        nd.normalize_proxy_hosts(invalid)


def test_proxy_cdn_host_is_explicitly_allowed():
    assert nd.normalize_proxy_hosts("audio.cdn-example.net") == "audio.cdn-example.net"
    assert nd.normalize_proxy_hosts("aKNIGA.ORG, akniga.org ; www.akniga.org") == "akniga.org, www.akniga.org"


def test_settings_roundtrip():
    values = normalize_settings({"proxy_url": "http://localhost:8080", "proxy_only_hosts": "akniga.org, yakniga.org"})
    assert values["proxy_only_hosts"] == "akniga.org, yakniga.org"
    old = normalize_settings({"proxy_url": "http://localhost:8080"})
    assert old["proxy_only_hosts"] == ""


def test_connect_uses_proxy_only_for_matching_hosts(monkeypatch):
    nd.configure_user_proxy("http://127.0.0.1:8080")
    nd.configure_proxy_hosts("akniga.org")
    chosen = []
    sock = Mock()
    monkeypatch.setattr(nd, "_connect_via_user_proxy", lambda host, port, timeout: (chosen.append((host, port)), sock)[1])
    connected, info = nd._connect_target_with_info("akniga.org", 443, .2)
    assert connected is sock
    assert "upstream proxy" in info["dns_provider"]
    assert chosen == [("akniga.org", 443)]

    nd.configure_dns_mode("system")
    direct = Mock()
    direct.getpeername.return_value = ("127.0.0.2", 443)
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", lambda address, timeout=None, **kw: direct)
    other, info2 = nd._connect_target_with_info("archive.org", 443, .2)
    assert other is direct
    assert info2["dns_provider"] == "system"
    assert chosen == [("akniga.org", 443)]


@dataclass
class FakeProvider:
    key: str
    display_name: str
    result: object = None
    exception: Exception | None = None

    def search(self, query):
        assert query == "Поттер"
        if self.exception is not None:
            raise self.exception
        return self.result


def test_real_search_check_reports_results_empty_and_sanitized_failures(monkeypatch):
    providers = (
        FakeProvider("a", "A", [object(), object()]),
        FakeProvider("b", "B", []),
        FakeProvider("c", "C", exception=TimeoutError("https://secret.invalid/path?token=SECRET")),
    )
    import audioknigi.providers as providers_module
    monkeypatch.setattr(providers_module, "registered_providers", lambda: providers)
    report = health.check_source_search("Поттер")
    assert [r.source for r in report.items] == ["A", "B", "C"]
    assert report.items[0].search_results == 2
    assert report.items[1].reachable and report.items[1].search_results == 0
    assert not report.items[2].reachable
    assert "тайм-аут" in report.items[2].error
    assert "SECRET" not in report.items[2].error
