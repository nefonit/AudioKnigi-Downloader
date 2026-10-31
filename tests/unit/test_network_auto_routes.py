"""Regression tests for auto DNS→TCP fallback, telemetry and strict isolation."""
import socket
from unittest.mock import MagicMock

import pytest

from audioknigi import network_dns as nd
from audioknigi.services import source_health_service as health


@pytest.fixture(autouse=True)
def clean_state():
    nd.configure_user_proxy("")
    nd.configure_dns_mode("auto")
    nd._reset_dns_runtime_state()
    yield
    nd.configure_user_proxy("")
    nd.configure_dns_mode("auto")
    nd._reset_dns_runtime_state()


class SocketStub:
    def __init__(self, ip="192.0.2.22"):
        self.ip = ip
        self.closed = False

    def getpeername(self):
        return self.ip, 443

    def close(self):
        self.closed = True


def test_auto_prefers_cloudflare_when_connects(monkeypatch):
    attempts = []
    monkeypatch.setattr(nd, "_resolve", lambda host, fam: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_system_addresses", lambda *a: pytest.fail("system DNS not needed"))
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", lambda target, timeout=None: (attempts.append(target[0]) or SocketStub(target[0])))
    sock, info = nd._connect_target_with_info("example.org", 443, timeout=1)
    assert attempts == ["192.0.2.1"]
    assert info["dns_provider"] == "Cloudflare"
    assert info["address"] == "192.0.2.1"
    sock.close()


def test_auto_retries_different_system_ip_after_tcp_failure(monkeypatch):
    attempts = []
    monkeypatch.setattr(nd, "_resolve", lambda host, fam: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_system_addresses", lambda host, fam: ("192.0.2.2",))

    def connect(target, timeout=None):
        attempts.append(target[0])
        if target[0] == "192.0.2.1":
            raise TimeoutError("TCP timeout")
        return SocketStub(target[0])

    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", connect)
    sock, info = nd._connect_target_with_info("example.org", 443, timeout=1)
    assert attempts == ["192.0.2.1", "192.0.2.2"]
    assert info["dns_provider"] == "system (TCP fallback)"
    assert info["alternate_attempted"] is True
    sock.close()


def test_strict_cloudflare_does_not_use_system_even_after_tcp_failure(monkeypatch):
    nd.configure_dns_mode("cloudflare")
    monkeypatch.setattr(nd, "_resolve_with_policy", lambda *_args: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_system_addresses", lambda *_args: pytest.fail("must not use system"))
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", lambda *_a, **_kw: (_ for _ in ()).throw(TimeoutError("timeout")))
    with pytest.raises(nd.TargetConnectError):
        nd._connect_target("example.org", 443, timeout=.1)


def test_same_ip_not_retried_via_system(monkeypatch):
    attempts=[]
    monkeypatch.setattr(nd, "_resolve", lambda *_: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_system_addresses", lambda *_: ("192.0.2.1",))
    def fail(target, timeout=None):
        attempts.append(target[0]);raise TimeoutError("failed")
    monkeypatch.setattr(nd,"_ORIGINAL_CREATE_CONNECTION",fail)
    with pytest.raises(nd.TargetConnectError) as exc:
        nd._connect_target("example.org",443,timeout=.2)
    assert attempts == ["192.0.2.1"]
    assert exc.value.details["attempts"] == 1


def test_user_proxy_takes_precedence_over_all_dns_fallbacks(monkeypatch):
    nd.configure_user_proxy("http://127.0.0.1:8000")
    monkeypatch.setattr(nd,"_connect_via_user_proxy",lambda host,port,timeout: SocketStub())
    monkeypatch.setattr(nd,"_resolve",lambda *a: pytest.fail("DNS must be remote"))
    sock,info=nd._connect_target_with_info("example.org",443,timeout=.1)
    assert info["dns_provider"] == "upstream proxy (remote DNS)"
    assert info["address"] == "via proxy"
    sock.close()


def test_cache_does_not_fake_cloudflare_recovery(monkeypatch):
    nd._record_cloudflare_failure(OSError("DoH unreachable"))
    monkeypatch.setattr(nd,"_resolve",lambda *a: ("192.0.2.1",))
    monkeypatch.setattr(nd,"_ORIGINAL_CREATE_CONNECTION",lambda target,timeout=None: SocketStub(target[0]))
    _,info=nd._connect_target_with_info("example.org",443,timeout=.1)
    assert nd.dns_runtime_status()["fallback_active"] is True


def test_auto_python_sessions_use_bridge_but_strict_uses_doh_hook():
    from audioknigi.core import build_http_session
    nd.configure_dns_mode("cloudflare")
    with build_http_session() as strict:
        assert not strict.proxies
    nd.configure_dns_mode("auto")
    with build_http_session() as auto:
        assert auto.proxies["https"].startswith("http://127.0.0.1:")


def test_diagnostic_reports_ip_tcp_tls_and_http_status(monkeypatch):
    sock=SocketStub("192.0.2.1")
    monkeypatch.setattr(health,"_connect_target_with_info",lambda *a,**kw:(sock,{"dns_provider":"Cloudflare","address":"192.0.2.1","dns_ms":9,"tcp_ms":12,"alternate_attempted":False}))
    class TLS:
        def __enter__(self):return self
        def __exit__(self,*_):return False
        def settimeout(self,_):pass
        def sendall(self,data):assert b"GET / HTTP/1.1" in data
        def recv(self,n):return b"HTTP/1.1 200 OK\r\n"
    context=MagicMock()
    context.wrap_socket.return_value=TLS()
    monkeypatch.setattr(health.ssl,"create_default_context",lambda:context)
    item=health._probe_source_detailed("example.org",timeout=1)
    assert item.reachable and item.status_code==200
    assert item.dns_provider=="Cloudflare" and item.ip_address=="192.0.2.1"
    assert item.dns_ms==9 and item.tcp_ms==12
    assert isinstance(item.tls_ms,int)
    assert sock.closed


def test_diagnostic_error_is_categorized_without_exposing_secrets(monkeypatch):
    err=nd.TargetConnectError("sensitive-path?token=secret",{"dns_provider":"Cloudflare","address":"192.0.2.1","tcp_ms":3000})
    err.__cause__=TimeoutError("timed out")
    monkeypatch.setattr(health,"_connect_target_with_info",lambda *a,**kw:(_ for _ in ()).throw(err))
    item=health._probe_source_detailed("example.org",timeout=1)
    assert not item.reachable
    assert item.error.startswith("HTTPS/TCP")
    assert "secret" not in item.error
    assert item.ip_address=="192.0.2.1"


# Detailed DNS comparison and fallback deadline regression cases.
def test_diagnostic_cloudflare_only_compares_system_but_does_not_connect(monkeypatch):
    nd.configure_dns_mode("cloudflare")
    monkeypatch.setattr(nd, "_resolve", lambda *a: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_resolve_with_policy", lambda *a: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_system_addresses", lambda *a: ("192.0.2.2",))
    attempted = []
    def connect(target, timeout=None):
        attempted.append(target[0])
        raise TimeoutError("not reachable")
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", connect)
    with pytest.raises(nd.TargetConnectError) as error:
        nd._connect_target_with_info("example.org", 443, timeout=.4, diagnostic=True)
    assert attempted == ["192.0.2.1"]
    d = error.value.details
    assert d["cloudflare_addresses"] == ("192.0.2.1",)
    assert d["system_addresses"] == ("192.0.2.2",)
    assert d["fallback_status"] == "strict_cloudflare"
    assert not d["alternate_attempted"]


def test_diagnostic_auto_reports_identical_answers_without_retry(monkeypatch):
    monkeypatch.setattr(nd, "_resolve", lambda *a: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_system_addresses", lambda *a: ("192.0.2.1",))
    attempts = []
    def connect(target, timeout=None):
        attempts.append(target[0])
        raise TimeoutError("no response")
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", connect)
    with pytest.raises(nd.TargetConnectError) as error:
        nd._connect_target_with_info("example.org", 443, timeout=.2, diagnostic=True)
    d = error.value.details
    assert d["system_dns_checked"] is True
    assert d["fallback_status"] == "no_distinct_addresses"
    assert attempts == ["192.0.2.1"]
    assert d["attempt_log"][0][:3] == ("Cloudflare", "192.0.2.1", "timeout")


def test_auto_reserves_time_for_other_ip_after_primary_timeout(monkeypatch):
    import time
    monkeypatch.setattr(nd, "_resolve", lambda *a: ("192.0.2.1",))
    monkeypatch.setattr(nd, "_system_addresses", lambda *a: ("192.0.2.2",))
    attempted = []
    def connect(target, timeout=None):
        attempted.append((target[0], timeout))
        if target[0] == "192.0.2.1":
            time.sleep(timeout)  # simulate actual OS timeout consuming its budget
            raise TimeoutError("primary TCP timeout")
        return SocketStub(target[0])
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", connect)
    sock, d = nd._connect_target_with_info("example.org", 443, timeout=.4, diagnostic=True)
    assert [a for a, _ in attempted] == ["192.0.2.1", "192.0.2.2"]
    assert attempted[0][1] < .4  # reserved time was not consumed by first attempt
    assert d["alternate_attempted"]
    assert d["attempt_log"][-1][2] == "OK"
    assert d["dns_provider"] == "system (TCP fallback)"
    sock.close()


def test_health_diagnostic_keeps_dns_routes_on_connection_failure(monkeypatch):
    error = nd.TargetConnectError("not connected", {
        "dns_provider": "Cloudflare", "address": "192.0.2.3",
        "dns_ms": 0, "tcp_ms": 3200,
        "cloudflare_addresses": ("192.0.2.3",),
        "system_addresses": ("192.0.2.3",),
        "system_dns_checked": True, "fallback_status": "no_distinct_addresses",
        "attempt_log": [("Cloudflare", "192.0.2.3", "timeout", 3200)],
    })
    error.__cause__ = TimeoutError("timed out")
    monkeypatch.setattr(health, "_connect_target_with_info", lambda *a, **kw: (_ for _ in ()).throw(error))
    item = health._probe_source_detailed("example.org", timeout=8)
    assert item.cloudflare_addresses == item.system_addresses == ("192.0.2.3",)
    assert item.system_dns_checked is True
    assert item.fallback_status == "no_distinct_addresses"
    assert item.attempted_routes[0][2] == "timeout"


def test_auto_tcp_timeout_stays_tcp_when_system_dns_fails(monkeypatch):
    """Fallback gaierror must not override the Cloudflare-IP TCP timeout."""
    from audioknigi.services.source_health_service import classify_network_error

    nd.configure_dns_mode("auto")
    monkeypatch.setattr(nd, "_resolve", lambda *args: ("192.0.2.9",))
    def system_dns_failure(*args):
        raise socket.gaierror(11002, "DNS unavailable")
    monkeypatch.setattr(nd, "_system_addresses", system_dns_failure)
    def tcp_timeout(target, timeout=None):
        raise TimeoutError("TCP connection timed out")
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION", tcp_timeout)
    with pytest.raises(nd.TargetConnectError) as caught:
        nd._connect_target_with_info("example.org", 443, timeout=.2, diagnostic=True)
    assert isinstance(caught.value.__cause__, TimeoutError)
    assert classify_network_error(caught.value).startswith("HTTPS/TCP")
    assert caught.value.details["fallback_status"] == "system_dns_failed"
    assert caught.value.details["system_dns_error"] == "gaierror"
    assert caught.value.details["attempt_log"][0][2] == "timeout"


def test_diagnostic_http_501_is_not_tcp_failure(monkeypatch):
    """A status code from an HTTPS server is distinct from connection loss."""
    sock = SocketStub("192.0.2.5")
    monkeypatch.setattr(health, "_connect_target_with_info", lambda *args, **kwargs: (
        sock, {"dns_provider": "Cloudflare", "address": "192.0.2.5", "dns_ms": 1, "tcp_ms": 4},
    ))
    class TLS:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def settimeout(self, value): pass
        def sendall(self, data): assert data.startswith(b"GET / HTTP/1.1")
        def recv(self, count): return b"HTTP/1.1 501 Not Implemented\r\n"
    context = MagicMock()
    context.wrap_socket.return_value = TLS()
    monkeypatch.setattr(health.ssl, "create_default_context", lambda: context)
    item = health._probe_source_detailed("example.org", timeout=1)
    assert item.reachable is True
    assert item.status_code == 501


def test_background_http_501_confirms_network_reachable(monkeypatch):
    class Response:
        status_code = 501
        def close(self): pass
    class Session:
        def __init__(self):
            self.headers = {}
            self.trust_env = True
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def get(self, *args, **kwargs): return Response()
    monkeypatch.setattr(health.requests, "Session", Session)
    item = health._probe_source("example.invalid", timeout=1)
    assert item.reachable is True
    assert item.status_code == 501
    assert item.blocked is False


# V9: distinguish successful TLS from a server that never answers HTTP.
def _mock_detailed_tls(monkeypatch, *, recv, handshake_error=None):
    sock = SocketStub("192.0.2.70")
    monkeypatch.setattr(health, "_connect_target_with_info", lambda *a, **kw: (
        sock, {"dns_provider": "Cloudflare", "address": "192.0.2.70", "dns_ms": 5, "tcp_ms": 9}
    ))
    class TLS:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def settimeout(self, value): pass
        def sendall(self, data): assert data.startswith(b"GET / HTTP/1.1")
        def recv(self, count): return recv()
    class Context:
        def wrap_socket(self, *args, **kwargs):
            if handshake_error: raise handshake_error
            return TLS()
    monkeypatch.setattr(health.ssl, "create_default_context", lambda: Context())
    return sock


def test_detailed_http_read_timeout_is_not_tcp_timeout(monkeypatch):
    sock = _mock_detailed_tls(monkeypatch, recv=lambda: (_ for _ in ()).throw(socket.timeout("read timed out")))
    result = health._probe_source_detailed("example.org", timeout=.25)
    assert result.reachable is False
    assert "HTTP: тайм-аут ожидания ответа" in result.error
    assert result.ip_address == "192.0.2.70"
    assert result.tcp_ms == 9 and result.tls_ms is not None
    assert result.http_ms is not None
    assert sock.closed


def test_detailed_tls_timeout_is_not_tcp_timeout(monkeypatch):
    sock = _mock_detailed_tls(monkeypatch, recv=lambda: b"", handshake_error=socket.timeout("handshake timed out"))
    result = health._probe_source_detailed("example.org", timeout=.25)
    assert result.reachable is False
    assert result.error.startswith("TLS: тайм-аут")
    assert result.tls_ms is None and result.http_ms is None
    assert sock.closed


def test_detailed_http_response_includes_elapsed_time(monkeypatch):
    _mock_detailed_tls(monkeypatch, recv=lambda: b"HTTP/1.1 500 Internal Server Error\r\n")
    result = health._probe_source_detailed("example.org", timeout=.25)
    assert result.reachable is True and result.status_code == 500
    assert result.http_ms is not None


def test_read_timeout_classified_as_http_phase_without_leaking_url():
    import requests
    error = requests.exceptions.ReadTimeout("https://private.example/?token=secret, read timed out")
    result = health.classify_network_error(error)
    assert result.startswith("HTTP:") and "secret" not in result
    nested = requests.exceptions.ConnectionError("request failed")
    nested.__cause__ = error
    assert health.classify_network_error(nested).startswith("HTTP:")
    assert health.classify_network_error(requests.exceptions.ConnectTimeout("timeout")).startswith("HTTPS/TCP")
