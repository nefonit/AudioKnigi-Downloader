"""V10: HTTPS read timeout should prefer another Cloudflare address."""
import socket
from unittest.mock import MagicMock
import pytest

from audioknigi import network_dns as nd
from audioknigi.services import source_health_service as health

BAD, GOOD = "192.0.2.71", "192.0.2.72"

class Sock:
    def __init__(self, ip):
        self.ip = ip
        self.closed = False
    def close(self): self.closed = True
    def getpeername(self): return self.ip, 443

@pytest.fixture(autouse=True)
def clean():
    nd.configure_user_proxy("")
    nd.configure_dns_mode("system")
    nd.configure_dns_mode("auto")
    yield
    nd.configure_user_proxy("")
    nd.configure_dns_mode("system")
    nd.configure_dns_mode("auto")


def test_http_timeout_hint_reorders_next_auto_connect(monkeypatch):
    attempts = []
    monkeypatch.setattr(nd, "_resolve", lambda host, family: (BAD, GOOD))
    monkeypatch.setattr(nd, "_ORIGINAL_CREATE_CONNECTION",
                        lambda target, timeout=None: (attempts.append(target[0]) or Sock(target[0])))
    assert nd.note_http_read_timeout("example.org", 443, BAD, (BAD, GOOD))
    sock, info = nd._connect_target_with_info("example.org", 443, timeout=2)
    assert sock.ip == GOOD
    assert attempts == [GOOD]
    assert info["fallback_status"] == "http_stalled_ip_deprioritized"
    sock.close()


def test_one_ip_no_http_route_hint(monkeypatch):
    assert not nd.note_http_read_timeout("example.org", 443, BAD, (BAD,))
    assert nd._http_stalled_ip("example.org", 443) == ""


def test_config_change_clears_stalled_hint():
    assert nd.note_http_read_timeout("example.org", 443, BAD, (BAD, GOOD))
    assert nd._http_stalled_ip("example.org", 443) == BAD
    nd.configure_dns_mode("cloudflare")
    assert nd._http_stalled_ip("example.org", 443) == ""


def test_custom_proxy_disallows_hint():
    nd.configure_user_proxy("http://127.0.0.1:8091")
    assert not nd.note_http_read_timeout("example.org", 443, BAD, (BAD, GOOD))


def test_http_success_on_same_ip_clears_its_hint():
    assert nd.note_http_read_timeout("example.org", 443, BAD, (BAD, GOOD))
    nd.note_http_response("example.org", 443, GOOD)
    assert nd._http_stalled_ip("example.org", 443) == BAD
    nd.note_http_response("example.org", 443, BAD)
    assert nd._http_stalled_ip("example.org", 443) == ""


def test_detailed_http_timeout_retries_different_cloudflare_ip_once(monkeypatch):
    sockets = []
    def connect(host, port, timeout, *, diagnostic):
        address = BAD if not sockets else GOOD
        sock = Sock(address)
        sockets.append(sock)
        return sock, {
            "dns_provider":"Cloudflare", "address":address,
            "cloudflare_addresses":(BAD, GOOD),
            "system_addresses":(GOOD,), "system_dns_checked":True,
            "attempt_log": [("Cloudflare", address, "OK", 4)],
            "dns_ms":1, "tcp_ms":4,
        }
    monkeypatch.setattr(health, "_connect_target_with_info", connect)
    class TLS:
        def __init__(self, sock): self.sock=sock
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): pass
        def sendall(self, payload): assert payload.startswith(b"GET / HTTP/1.1")
        def recv(self, n):
            if self.sock.ip == BAD: raise socket.timeout("stalled response")
            return b"HTTP/1.1 200 OK\r\n"
    class Context:
        def wrap_socket(self, sock, server_hostname):
            assert server_hostname == "example.org"
            return TLS(sock)
    monkeypatch.setattr(health.ssl, "create_default_context", lambda: Context())
    result = health._probe_source_detailed("example.org", timeout=2)
    assert len(sockets) == 2
    assert all(s.closed for s in sockets)
    assert result.reachable and result.status_code == 200
    assert result.ip_address == GOOD
    assert result.first_http_timeout_ip == BAD
    assert result.fallback_status == "http_route_switched"
    assert nd._http_stalled_ip("example.org", 443) == BAD


def test_detailed_no_retry_on_tcp_timeout(monkeypatch):
    called=[]
    def connect(*args, **kwargs):
        called.append(1)
        raise socket.timeout("tcp timeout")
    monkeypatch.setattr(health, "_connect_target_with_info", connect)
    result = health._probe_source_detailed("example.org", timeout=.1)
    assert len(called)==1
    assert not result.reachable


def test_detailed_no_retry_with_single_cloudflare_ip(monkeypatch):
    called=[]
    def connect(*args,**kwargs):
        called.append(1)
        return Sock(BAD),{"dns_provider":"Cloudflare","address":BAD,"cloudflare_addresses":(BAD,),"dns_ms":1,"tcp_ms":1}
    monkeypatch.setattr(health,"_connect_target_with_info",connect)
    class TLS:
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def settimeout(self,*a): pass
        def sendall(self,*a): pass
        def recv(self,*a): raise socket.timeout("HTTP read timeout")
    context=MagicMock()
    context.wrap_socket.return_value=TLS()
    monkeypatch.setattr(health.ssl,"create_default_context",lambda:context)
    result=health._probe_source_detailed("example.org",timeout=.1)
    assert not result.reachable and len(called)==1
