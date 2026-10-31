"""Deterministic loopback-only tests for the optional upstream proxy."""
from __future__ import annotations

import socket
import socketserver
import threading

import pytest
import requests

from audioknigi import network_dns as nd
from audioknigi.core import build_http_session, refresh_http_session_profile
from audioknigi.services.source_health_service import classify_network_error


@pytest.fixture(autouse=True)
def reset_upstream():
    nd.configure_user_proxy("")
    refresh_http_session_profile()
    yield
    nd.configure_user_proxy("")
    refresh_http_session_profile()


def test_proxy_url_validation():
    assert nd.validate_user_proxy("") == ""
    assert nd.validate_user_proxy("http://127.0.0.1:8080") == "http://127.0.0.1:8080"
    assert nd.validate_user_proxy("socks5h://localhost:1080") == "socks5h://localhost:1080"
    for candidate in ("http://user:secret@example.org:80", "https://example.org:443",
                      "socks5h://localhost", "http://localhost:99999", "http://localhost:80/token"):
        with pytest.raises(ValueError):
            nd.validate_user_proxy(candidate)


class _ProxyServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _FakeHttpProxy(socketserver.BaseRequestHandler):
    def handle(self):
        head, _ = nd._read_http_head(self.request)
        assert head.startswith(b"CONNECT ")
        self.server.targets.append(head.split(b"\r\n", 1)[0])
        self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        self.request.sendall(b"ok")


class _FakeSocksProxy(socketserver.BaseRequestHandler):
    def handle(self):
        assert nd._recv_exact(self.request, 3) == b"\x05\x01\x00"
        self.request.sendall(b"\x05\x00")
        version, command, zero, address_type = nd._recv_exact(self.request, 4)
        assert (version, command, zero) == (5, 1, 0)
        if address_type == 3:
            host_length = nd._recv_exact(self.request, 1)[0]
            hostname = nd._recv_exact(self.request, host_length).decode("ascii")
        elif address_type == 1:
            hostname = socket.inet_ntoa(nd._recv_exact(self.request, 4))
        else:
            raise AssertionError("Unsupported ATYP")
        port = int.from_bytes(nd._recv_exact(self.request, 2), "big")
        self.server.targets.append((hostname, port))
        self.request.sendall(b"\x05\x00\x00\x01" + b"\x00" * 4 + b"\x00\x00")
        self.request.sendall(b"ok")


@pytest.mark.parametrize("scheme,handler", [("http", _FakeHttpProxy), ("socks5h", _FakeSocksProxy)])
def test_proxy_tunnel_connects_remotely(scheme, handler):
    with _ProxyServer(("127.0.0.1", 0), handler) as server:
        server.targets = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        nd.configure_user_proxy(f"{scheme}://127.0.0.1:{server.server_address[1]}")
        with nd._connect_target("example.invalid", 443, timeout=2) as remote:
            assert remote.recv(2) == b"ok"
        assert server.targets == ([b"CONNECT example.invalid:443 HTTP/1.1"]
                                  if scheme == "http" else [("example.invalid", 443)])
        server.shutdown()


def test_requests_session_uses_local_bridge():
    """No network services outside loopback; verify transport is consistent."""
    with _ProxyServer(("127.0.0.1", 0), _FakeHttpProxy) as server:
        server.targets = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        nd.configure_user_proxy(f"http://127.0.0.1:{server.server_address[1]}")
        session = build_http_session()
        try:
            assert session.trust_env is False
            assert session.proxies["http"].startswith("http://127.0.0.1:")
            assert session.proxies["https"] == session.proxies["http"]
        finally:
            session.close()
            server.shutdown()


def test_diagnostic_classes_are_specific_and_safe():
    assert classify_network_error(requests.exceptions.ConnectTimeout("server" )).startswith("HTTPS/TCP")
    assert classify_network_error(requests.exceptions.ProxyError("private-token=xyz")).startswith("Прокси")
    assert "private-token" not in classify_network_error(requests.exceptions.ProxyError("private-token=xyz"))
    assert classify_network_error(socket.gaierror(-2, "not found")).startswith("DNS")


def test_proxy_dns_paths_are_consistent():
    from audioknigi.network_dns import cloudflare_ffmpeg_input_args, cloudflare_playwright_launch_kwargs
    nd.configure_dns_mode("system")
    assert cloudflare_ffmpeg_input_args() == []
    assert "proxy" not in cloudflare_playwright_launch_kwargs()
    nd.configure_user_proxy("socks5h://127.0.0.1:1080")
    assert cloudflare_ffmpeg_input_args()[0] == "-http_proxy"
    assert cloudflare_playwright_launch_kwargs()["proxy"]["server"].startswith("http://127.0.0.1:")

class _Origin(socketserver.BaseRequestHandler):
    def handle(self):
        nd._read_http_head(self.request)
        self.request.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\nConnection: close\r\n\r\nHELLO")


class _ForwardHttpProxy(socketserver.BaseRequestHandler):
    def handle(self):
        request, _ = nd._read_http_head(self.request)
        hostport = request.split(b"\r\n", 1)[0].split()[1].decode()
        hostname, port = hostport.rsplit(":", 1)
        with socket.create_connection((hostname, int(port)), timeout=3) as target:
            self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            nd._relay_bidirectional(self.request, target, return_when_right_closes=True)


class _ForwardSocksProxy(socketserver.BaseRequestHandler):
    def handle(self):
        assert nd._recv_exact(self.request, 3) == b"\x05\x01\x00"
        self.request.sendall(b"\x05\x00")
        head = nd._recv_exact(self.request, 4)
        if head[3] == 1:
            host = socket.inet_ntoa(nd._recv_exact(self.request, 4))
        elif head[3] == 3:
            host = nd._recv_exact(self.request, nd._recv_exact(self.request, 1)[0]).decode()
        else:
            raise AssertionError(head)
        port = int.from_bytes(nd._recv_exact(self.request, 2), "big")
        with socket.create_connection((host, port), timeout=3) as target:
            self.request.sendall(b"\x05\x00\x00\x01" + b"\x00" * 4 + b"\x00\x00")
            nd._relay_bidirectional(self.request, target, return_when_right_closes=True)


@pytest.mark.parametrize("scheme,handler", [("http", _ForwardHttpProxy), ("socks5h", _ForwardSocksProxy)])
def test_end_to_end_requests_through_proxy_bridge(scheme, handler):
    with _ProxyServer(("127.0.0.1", 0), _Origin) as origin:
        with _ProxyServer(("127.0.0.1", 0), handler) as remote:
            threads = [threading.Thread(target=server.serve_forever, daemon=True)
                       for server in (origin, remote)]
            for thread in threads:
                thread.start()
            nd.configure_user_proxy(f"{scheme}://127.0.0.1:{remote.server_address[1]}")
            refresh_http_session_profile()
            with build_http_session() as session:
                response = session.get(f"http://127.0.0.1:{origin.server_address[1]}/", timeout=3)
                assert response.status_code == 200
                assert response.text == "HELLO"
            remote.shutdown()
            origin.shutdown()
