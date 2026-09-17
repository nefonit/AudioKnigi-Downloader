"""Cloudflare 1.1.1.1 DNS-over-HTTPS integration.

The desktop application targets Windows.  Public hostname lookups made by
Python networking are resolved through Cloudflare DoH and never fall back to
the ISP/system resolver.  Numeric IPs, localhost and .local names are left to
the operating system because they are not public DNS names.

Playwright runs Chromium in a child process, so the Python socket hook cannot
reach it.  ``cloudflare_chromium_args`` returns the Secure DNS arguments used by
all Chromium fallback launches.
"""
from __future__ import annotations

import atexit
import http.client
import ipaddress
import select
import json
import os
import socket
import socketserver
import ssl
import threading
import time
from urllib.parse import quote, urlsplit

from .logging_utils import app_logger

CLOUDFLARE_DOH_HOST = "cloudflare-dns.com"
CLOUDFLARE_DOH_PATH = "/dns-query"
CLOUDFLARE_DOH_TEMPLATE = "https://cloudflare-dns.com/dns-query{?dns}"
CLOUDFLARE_BOOTSTRAP_IPS = (
    "1.1.1.1",
    "1.0.0.1",
    "2606:4700:4700::1111",
    "2606:4700:4700::1001",
)

_ORIGINAL_GETADDRINFO = socket.getaddrinfo
_ORIGINAL_CREATE_CONNECTION = socket.create_connection
_INSTALL_LOCK = threading.RLock()
_CACHE_LOCK = threading.RLock()
_CACHE: dict[tuple[str, int], tuple[float, tuple[str, ...]]] = {}
_CACHE_MAX = 512
_INSTALLED = False


def _is_numeric_host(host: str) -> bool:
    value = str(host or "").strip().strip("[]")
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _bypass_cloudflare(host) -> bool:
    if host is None:
        return True
    if isinstance(host, bytes):
        try:
            host = host.decode("ascii")
        except Exception:
            return True
    value = str(host or "").strip().rstrip(".").lower()
    if not value or _is_numeric_host(value):
        return True
    # Public names go through Cloudflare DoH.  Single-label and conventional
    # private suffixes must stay on the OS resolver so NAS/Audiobookshelf hosts
    # such as ``nas`` or ``audiobookshelf.lan`` keep working on local networks.
    if "." not in value:
        return True
    return (
        value in {"localhost", "localhost.localdomain"}
        or value.endswith((".local", ".lan", ".home", ".internal", ".localhost"))
    )


class _BootstrapHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection whose TCP bootstrap never needs DNS."""

    def __init__(self, bootstrap_ip: str, timeout: float = 4.0):
        context = ssl.create_default_context()
        super().__init__(CLOUDFLARE_DOH_HOST, 443, timeout=timeout, context=context)
        self._bootstrap_ip = bootstrap_ip

    def connect(self):  # noqa: D401 - mirrors http.client implementation
        raw = _ORIGINAL_CREATE_CONNECTION(
            (self._bootstrap_ip, 443),
            timeout=self.timeout,
            source_address=self.source_address,
        )
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=CLOUDFLARE_DOH_HOST)
        except Exception:
            raw.close()
            raise


def _query_cloudflare_json(host: str, record_type: int, timeout: float = 4.0, _seen: set[str] | None = None) -> tuple[tuple[str, ...], int, str]:
    """Return (addresses, ttl, bootstrap_ip) from Cloudflare DoH."""
    qtype = "AAAA" if int(record_type) == 28 else "A"
    try:
        dns_host = str(host or "").rstrip(".").encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise OSError(f"Некорректное DNS-имя: {host}") from exc
    seen = set(_seen or ())
    folded_host = dns_host.casefold()
    if folded_host in seen:
        raise OSError(f"Cloudflare DoH CNAME loop for {host}")
    seen.add(folded_host)
    path = f"{CLOUDFLARE_DOH_PATH}?name={quote(dns_host, safe='')}&type={qtype}"
    last_error: Exception | None = None
    for bootstrap_ip in CLOUDFLARE_BOOTSTRAP_IPS:
        conn = None
        try:
            conn = _BootstrapHTTPSConnection(bootstrap_ip, timeout=timeout)
            conn.request(
                "GET",
                path,
                headers={
                    "Host": CLOUDFLARE_DOH_HOST,
                    "Accept": "application/dns-json",
                    "User-Agent": "AudioKnigiDownloader-CloudflareDNS/1.0",
                    "Connection": "close",
                },
            )
            response = conn.getresponse()
            payload = response.read()
            if int(response.status) != 200:
                raise OSError(f"Cloudflare DoH HTTP {response.status}")
            data = json.loads(payload.decode("utf-8", "replace"))
            status = int(data.get("Status", -1))
            if status != 0:
                # NXDOMAIN (3) is a real DNS answer rather than a transport error.
                if status == 3:
                    return (), 30, bootstrap_ip
                raise OSError(f"Cloudflare DoH DNS status {status}")
            answers = data.get("Answer") if isinstance(data.get("Answer"), list) else []
            addresses: list[str] = []
            ttls: list[int] = []
            wanted = 28 if qtype == "AAAA" else 1
            for answer in answers:
                if not isinstance(answer, dict) or int(answer.get("type", -1)) != wanted:
                    continue
                value = str(answer.get("data") or "").strip()
                try:
                    ipaddress.ip_address(value)
                except ValueError:
                    continue
                if value not in addresses:
                    addresses.append(value)
                try:
                    ttls.append(int(answer.get("TTL", 60)))
                except Exception:
                    pass
            ttl = min(ttls) if ttls else 60
            ttl = max(15, min(int(ttl), 600))
            if not addresses:
                cname_rows = [
                    answer for answer in answers
                    if isinstance(answer, dict) and int(answer.get("type", -1)) == 5
                ]
                if cname_rows:
                    cname = str(cname_rows[-1].get("data") or "").strip().rstrip(".")
                    if cname:
                        resolved, cname_ttl, resolved_bootstrap = _query_cloudflare_json(
                            cname, record_type, timeout, seen
                        )
                        alias_ttls = []
                        for row in cname_rows:
                            try:
                                alias_ttls.append(int(row.get("TTL", 60)))
                            except Exception:
                                pass
                        combined_ttl = min([cname_ttl, *alias_ttls]) if alias_ttls else cname_ttl
                        return resolved, max(15, min(int(combined_ttl), 600)), resolved_bootstrap
            return tuple(addresses), ttl, bootstrap_ip
        except OSError as exc:
            # A CNAME cycle is a deterministic DNS answer, not a bootstrap
            # transport failure. Retrying another Cloudflare IP only repeats
            # the same recursive loop and hides the useful root cause.
            if "CNAME loop" in str(exc):
                raise
            last_error = exc
        except Exception as exc:
            last_error = exc
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    raise socket.gaierror(socket.EAI_AGAIN, f"Cloudflare DoH failed for {host}: {last_error}")


def _resolve(host: str, family: int) -> tuple[str, ...]:
    normalized = str(host or "").strip().rstrip(".").lower()
    record_type = 28 if family == socket.AF_INET6 else 1
    cache_key = (normalized, record_type)
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and cached[0] > now:
            app_logger.debug("NETWORK DNS | provider=Cloudflare | cache=hit | host=%s | type=%s", normalized, record_type)
            return cached[1]

    addresses, ttl, bootstrap = _query_cloudflare_json(normalized, record_type)
    with _CACHE_LOCK:
        # Keep the long-running tray application's DNS cache bounded.  Expired
        # entries are removed first; oldest insertion-order entries are evicted
        # only if the cache is still at the ceiling.
        expired = [key for key, (expires, _values) in _CACHE.items() if expires <= now]
        for key in expired:
            _CACHE.pop(key, None)
        while len(_CACHE) >= _CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)), None)
        _CACHE[cache_key] = (now + ttl, tuple(addresses))
    app_logger.debug(
        "NETWORK DNS | provider=Cloudflare | mode=DoH-secure | host=%s | type=%s | answers=%d | bootstrap=%s | ttl=%s",
        normalized,
        record_type,
        len(addresses),
        bootstrap,
        ttl,
    )
    return tuple(addresses)


def cloudflare_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """socket.getaddrinfo replacement using strict Cloudflare DoH for public names."""
    if _bypass_cloudflare(host):
        return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)

    host_text = host.decode("ascii") if isinstance(host, bytes) else str(host)
    requested_family = int(family or socket.AF_UNSPEC)
    if requested_family == socket.AF_INET6:
        addresses = _resolve(host_text, socket.AF_INET6)
    else:
        # Prefer IPv4 for Windows compatibility.  If the name is IPv6-only,
        # fall back to an AAAA query while still remaining entirely on Cloudflare.
        addresses = _resolve(host_text, socket.AF_INET)
        if not addresses and requested_family == socket.AF_UNSPEC:
            addresses = _resolve(host_text, socket.AF_INET6)

    if not addresses:
        raise socket.gaierror(socket.EAI_NONAME, f"Cloudflare DNS returned no address for {host_text}")

    results = []
    seen = set()
    for address in addresses:
        ip_family = socket.AF_INET6 if ":" in address else socket.AF_INET
        if requested_family not in (socket.AF_UNSPEC, 0, ip_family):
            continue
        for item in _ORIGINAL_GETADDRINFO(address, port, ip_family, type, proto, flags):
            key = (item[0], item[1], item[2], item[4])
            if key not in seen:
                results.append(item)
                seen.add(key)
    if not results:
        raise socket.gaierror(socket.EAI_NONAME, f"Cloudflare DNS returned no usable address for {host_text}")
    return results


def install_cloudflare_dns(*, force: bool = False) -> bool:
    """Install strict Cloudflare DoH resolution for Python networking.

    On Windows this is enabled by default. ``force`` exists for deterministic
    tests on non-Windows hosts.
    """
    global _INSTALLED
    if os.name != "nt" and not force:
        return False
    with _INSTALL_LOCK:
        if socket.getaddrinfo is cloudflare_getaddrinfo:
            _INSTALLED = True
            return True
        socket.getaddrinfo = cloudflare_getaddrinfo
        _INSTALLED = True
    app_logger.info(
        "NETWORK DNS | provider=Cloudflare 1.1.1.1 | mode=DoH-secure | active=True | bootstrap=%s | system_fallback=False",
        ",".join(CLOUDFLARE_BOOTSTRAP_IPS),
    )
    return True


def cloudflare_dns_active() -> bool:
    return bool(_INSTALLED and socket.getaddrinfo is cloudflare_getaddrinfo)


def cloudflare_dns_diagnostic() -> str:
    return (
        "provider=Cloudflare 1.1.1.1 | mode=DoH-secure | "
        f"active={cloudflare_dns_active()} | system_fallback=False"
    )


def cloudflare_chromium_args() -> list[str]:
    """Secure-DNS configuration for Chromium used by Playwright.

    Chromium documents secure/automatic/off DoH modes and custom URI templates.
    The child browser is additionally logged by the caller because these options
    are independent from Python's socket resolver.
    """
    return [
        "--dns-over-https-mode=secure",
        f"--dns-over-https-templates={CLOUDFLARE_DOH_TEMPLATE}",
    ]

# ---------------------------------------------------------------------------
# Local Cloudflare-resolving proxy for Playwright/Chromium
# ---------------------------------------------------------------------------

_PROXY_LOCK = threading.RLock()
_PROXY_SERVER = None
_PROXY_THREAD = None
_PROXY_ATEXIT_REGISTERED = False


def _parse_proxy_authority(value: str, default_port: int) -> tuple[str, int]:
    """Parse an HTTP proxy authority, including bracketed/numeric IPv6."""
    text = str(value or "").strip()
    if not text:
        raise ValueError("Empty proxy authority")
    if text.startswith("["):
        end = text.find("]")
        if end < 0:
            raise ValueError(f"Malformed IPv6 proxy authority: {text}")
        host = text[1:end].strip()
        suffix = text[end + 1 :].strip()
        if not suffix:
            return host, int(default_port)
        if not suffix.startswith(":") or not suffix[1:].isdigit():
            raise ValueError(f"Malformed proxy port: {text}")
        return host, int(suffix[1:])

    # An unbracketed numeric IPv6 literal is an address, not host:port. RFC
    # proxy authorities require brackets when an IPv6 port is supplied;
    # treating the final hextet as a port would silently corrupt ::1, etc.
    try:
        numeric = ipaddress.ip_address(text)
    except ValueError:
        numeric = None
    if numeric is not None:
        return text, int(default_port)

    host, sep, port_text = text.rpartition(":")
    if sep:
        if not host or not port_text.isdigit():
            raise ValueError(f"Malformed proxy authority: {text}")
        return host, int(port_text)
    return text, int(default_port)


def _connect_target(host: str, port: int, timeout: float = 12.0):
    if _bypass_cloudflare(host):
        return _ORIGINAL_CREATE_CONNECTION((host, int(port)), timeout=timeout)
    if _is_numeric_host(host):
        addresses = (host.strip("[]"),)
    else:
        addresses = _resolve(host, socket.AF_INET)
        if not addresses:
            addresses = _resolve(host, socket.AF_INET6)
    last_error = None
    for address in addresses:
        try:
            return _ORIGINAL_CREATE_CONNECTION((address, int(port)), timeout=timeout)
        except Exception as exc:
            last_error = exc
    raise OSError(f"Cloudflare proxy could not connect to {host}:{port}: {last_error}")


def _relay_bidirectional(
    left: socket.socket, right: socket.socket, *, return_when_right_closes: bool = False
) -> None:
    """Relay sockets while respecting half-close; plain HTTP can end on upstream EOF."""
    sockets = (left, right)
    readable_sockets = {left, right}
    half_close_deadline = None
    try:
        for sock in sockets:
            sock.setblocking(False)
        while readable_sockets:
            active = tuple(readable_sockets)
            timeout = 30.0
            if half_close_deadline is not None:
                remaining = half_close_deadline - time.monotonic()
                if remaining <= 0:
                    return
                timeout = min(timeout, remaining)
            readable, _, exceptional = select.select(active, (), active, timeout)
            if exceptional:
                return
            if not readable:
                if half_close_deadline is not None and time.monotonic() >= half_close_deadline:
                    return
                continue
            for source in readable:
                target = right if source is left else left
                try:
                    data = source.recv(65536)
                except (BlockingIOError, InterruptedError):
                    continue
                except (ConnectionResetError, BrokenPipeError, OSError):
                    return
                if not data:
                    if return_when_right_closes and source is right:
                        return
                    # FIN only closes this direction. Preserve the reverse path
                    # so buffered/server response bytes still reach the client.
                    readable_sockets.discard(source)
                    if half_close_deadline is None:
                        half_close_deadline = time.monotonic() + 30.0
                    try:
                        target.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
                    continue
                view = memoryview(data)
                stalled_since = None
                while view:
                    try:
                        sent = target.send(view)
                        if sent <= 0:
                            return
                        view = view[sent:]
                        stalled_since = None
                    except (BlockingIOError, InterruptedError):
                        if stalled_since is None:
                            stalled_since = time.monotonic()
                        elif time.monotonic() - stalled_since >= 20.0:
                            return
                        select.select((), (target,), (), 1.0)
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        return
    finally:
        for sock in sockets:
            try:
                sock.setblocking(True)
            except Exception:
                pass


def _read_http_head(sock: socket.socket, limit: int = 131072, *, deadline_seconds: float = 20.0) -> tuple[bytes, bytes]:
    data = bytearray()
    deadline = time.monotonic() + max(0.1, float(deadline_seconds))
    while b"\r\n\r\n" not in data:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Proxy request header deadline exceeded")
        sock.settimeout(remaining)
        chunk = sock.recv(8192)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > limit:
            raise OSError("Proxy request headers too large")
    marker = data.find(b"\r\n\r\n")
    if marker < 0:
        return bytes(data), b""
    marker += 4
    return bytes(data[:marker]), bytes(data[marker:])


class _CloudflareProxyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client = self.request
        client.settimeout(20.0)
        upstream = None
        try:
            head, remainder = _read_http_head(client)
            if not head:
                return
            lines = head.split(b"\r\n")
            request_line = lines[0].decode("iso-8859-1", "replace")
            parts = request_line.split(None, 2)
            if len(parts) != 3:
                raise OSError("Malformed proxy request line")
            method, target, version = parts

            if method.upper() == "CONNECT":
                host, port = _parse_proxy_authority(target, 443)
                upstream = _connect_target(host, port)
                app_logger.debug("NETWORK DNS | client=Chromium-proxy | host=%s | port=%s | via=Cloudflare", host, port)
                client.sendall(b"HTTP/1.1 200 Connection Established\r\nProxy-Agent: AudioKnigi-Cloudflare\r\n\r\n")
                if remainder:
                    upstream.sendall(remainder)
                client.settimeout(None)
                upstream.settimeout(None)
                _relay_bidirectional(client, upstream, return_when_right_closes=True)
                return

            parsed = urlsplit(target)
            if parsed.scheme and parsed.hostname:
                host = parsed.hostname
                port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
                path = parsed.path or "/"
                if parsed.query:
                    path += "?" + parsed.query
            else:
                host_header = ""
                for line in lines[1:]:
                    if line.lower().startswith(b"host:"):
                        host_header = line.split(b":", 1)[1].decode("iso-8859-1", "replace").strip()
                        break
                if not host_header:
                    raise OSError("Proxy request has no host")
                host, port = _parse_proxy_authority(host_header, 80)
                path = target
                # Origin-form must start with '/' (or be '*'). Be defensive
                # against authority/path forms occasionally produced by proxy
                # clients so an invalid request target is never forwarded.
                if path != "*" and not path.startswith("/"):
                    reparsed = urlsplit("//" + path)
                    if reparsed.hostname:
                        path = reparsed.path or "/"
                        if reparsed.query:
                            path += "?" + reparsed.query
                    else:
                        path = "/" + path.lstrip("/")

            upstream = _connect_target(host, port)
            app_logger.debug("NETWORK DNS | client=Chromium-proxy | host=%s | port=%s | via=Cloudflare", host, port)
            filtered = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                low = line.lower()
                if low.startswith((b"connection:", b"proxy-connection:")):
                    continue
                filtered.append(line)
            # Ordinary HTTP proxying is one request per upstream connection.
            # Force EOF after the response so the relay cannot wait forever on
            # an origin keep-alive socket. CONNECT tunnels remain untouched.
            filtered.append(b"Connection: close")
            forward_head = f"{method} {path} {version}\r\n".encode("iso-8859-1") + b"\r\n".join(filtered) + b"\r\n\r\n"
            upstream.sendall(forward_head + remainder)
            client.settimeout(None)
            upstream.settimeout(None)
            _relay_bidirectional(client, upstream, return_when_right_closes=True)
        except Exception as exc:
            app_logger.debug("NETWORK DNS | Cloudflare proxy request failed | %s: %s", type(exc).__name__, exc)
            try:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\nContent-Length: 0\r\n\r\n")
            except Exception:
                pass
        finally:
            try:
                if upstream is not None:
                    upstream.close()
            except Exception:
                pass


class _ThreadingProxyServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def ensure_cloudflare_playwright_proxy() -> str:
    """Start the localhost proxy and return its Playwright proxy URL."""
    global _PROXY_SERVER, _PROXY_THREAD, _PROXY_ATEXIT_REGISTERED
    with _PROXY_LOCK:
        if _PROXY_SERVER is not None:
            host, port = _PROXY_SERVER.server_address[:2]
            return f"http://{host}:{port}"
        server = _ThreadingProxyServer(("127.0.0.1", 0), _CloudflareProxyHandler)
        thread = threading.Thread(target=server.serve_forever, name="cloudflare-doh-proxy", daemon=True)
        thread.start()
        _PROXY_SERVER = server
        _PROXY_THREAD = thread
        if not _PROXY_ATEXIT_REGISTERED:
            atexit.register(shutdown_cloudflare_playwright_proxy)
            _PROXY_ATEXIT_REGISTERED = True
        host, port = server.server_address[:2]
        url = f"http://{host}:{port}"
        app_logger.info(
            "NETWORK DNS | client=Playwright/Chromium | proxy=%s | provider=Cloudflare | mode=DoH-secure | system_fallback=False",
            url,
        )
        return url


def shutdown_cloudflare_playwright_proxy() -> None:
    global _PROXY_SERVER, _PROXY_THREAD
    with _PROXY_LOCK:
        server, thread = _PROXY_SERVER, _PROXY_THREAD
        _PROXY_SERVER = None
        _PROXY_THREAD = None
    if server is not None:
        if thread is not None and thread.is_alive():
            try:
                server.shutdown()
            except Exception:
                pass
        try:
            server.server_close()
        except Exception:
            pass
    if thread is not None and thread.is_alive() and thread is not threading.current_thread():
        try:
            thread.join(timeout=1.0)
        except Exception:
            pass


def cloudflare_ffmpeg_input_args() -> list[str]:
    """FFmpeg/FFprobe input options that keep remote URL DNS behind Cloudflare.

    FFmpeg's HTTP/TLS protocols support the ``http_proxy`` input option,
    including CONNECT tunnelling for HTTPS.  The localhost proxy resolves the
    destination host exclusively with the same Cloudflare DoH resolver used by
    Python and Playwright.
    """
    return ["-http_proxy", ensure_cloudflare_playwright_proxy()]


def cloudflare_playwright_launch_kwargs() -> dict:
    """Launch Microsoft Edge without bundling Playwright's Chromium.

    Playwright's Python driver remains embedded in the application, but the
    browser itself is the stable Microsoft Edge installation already present
    on supported Windows systems.  This keeps the one-file build much smaller
    while preserving the same Cloudflare-resolving local proxy.
    """
    return {
        "channel": "msedge",
        "headless": True,
        "proxy": {"server": ensure_cloudflare_playwright_proxy()},
        "args": cloudflare_chromium_args() + ["--disable-quic"],
    }


def launch_playwright_chromium(browser_type):
    """Launch Edge when available, otherwise fall back to Playwright Chromium."""
    kwargs = cloudflare_playwright_launch_kwargs()
    try:
        return browser_type.launch(**kwargs)
    except Exception as edge_exc:
        if not kwargs.get("channel"):
            raise
        fallback = dict(kwargs)
        fallback.pop("channel", None)
        app_logger.warning(
            "Playwright Edge channel unavailable; retrying bundled/default Chromium: %s",
            edge_exc,
        )
        return browser_type.launch(**fallback)
