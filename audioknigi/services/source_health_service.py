from __future__ import annotations

"""Lightweight reachability checks for the built-in audiobook sources."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
import re
import socket
import ssl
import time

import requests

from ..core import USER_AGENT
from ..network_dns import (user_proxy_enabled, current_dns_mode, DNS_MODE_AUTO,
                           ensure_cloudflare_playwright_proxy, _connect_target_with_info,
                           note_http_read_timeout, note_http_response)
from ..logging_utils import app_logger
from ..sources import SUPPORTED_SOURCE_HOSTS


@dataclass(frozen=True, slots=True)
class SourceHealthItem:
    source: str
    url: str
    reachable: bool
    blocked: bool = False
    status_code: int | None = None
    error: str = ""
    dns_provider: str = ""
    ip_address: str = ""
    dns_ms: int | None = None
    tcp_ms: int | None = None
    tls_ms: int | None = None
    http_ms: int | None = None
    alternate_attempted: bool = False
    error_code: str = ""
    cloudflare_addresses: tuple[str, ...] = ()
    system_addresses: tuple[str, ...] = ()
    system_dns_checked: bool = False
    system_dns_error: str = ""
    attempted_routes: tuple[tuple[str, str, str, int], ...] = ()
    fallback_status: str = ""
    first_http_timeout_ip: str = ""
    search_checked: bool = False
    search_results: int | None = None
    search_supported: bool = True
    search_endpoint: str = ""


@dataclass(slots=True)
class SourceHealthOutcome:
    items: list[SourceHealthItem] = field(default_factory=list)

    @property
    def reachable_count(self) -> int:
        return sum(1 for item in self.items if item.reachable)

    @property
    def unavailable_count(self) -> int:
        return sum(1 for item in self.items if not item.reachable)

    @property
    def all_unavailable(self) -> bool:
        return bool(self.items) and self.reachable_count == 0

    @property
    def blocked_count(self) -> int:
        return sum(1 for item in self.items if item.blocked)


def classify_network_error(exc: BaseException) -> str:
    """Explain connectivity failures without exposing signed URLs or secrets."""
    # Classify the outer Requests exception first: its nested urllib3/socket
    # timeout may otherwise hide whether the failure was during HTTP *reading*.
    if isinstance(exc, requests.exceptions.ReadTimeout):
        return "HTTP: тайм-аут ожидания ответа сервера (соединение установлено)"
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return "HTTPS/TCP: тайм-аут (возможна фильтрация или проблема маршрута)"
    cause = getattr(exc, "__cause__", None)
    if isinstance(cause, BaseException) and cause is not exc:
        safe_cause = classify_network_error(cause)
        if not safe_cause.startswith("Сеть: "):
            return safe_cause
    if isinstance(exc, requests.exceptions.ProxyError):
        return "Прокси/туннель: соединение не удалось"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "HTTPS/TCP: тайм-аут (возможна фильтрация или проблема маршрута)"
    if isinstance(exc, (requests.exceptions.SSLError, ssl.SSLError)):
        return "HTTPS: ошибка сертификата или TLS"
    if isinstance(exc, socket.gaierror):
        return "DNS: не удалось определить IP-адрес"
    explanation = str(exc).lower()
    if any(word in explanation for word in ("nameresolutionerror", "failed to resolve", "getaddrinfo failed", "name or service not known", "dns returned no", "hostname resolution")):
        return "DNS: не удалось определить IP-адрес"
    if any(word in explanation for word in ("read timed out", "read timeout", "timed out while reading")):
        return "HTTP: тайм-аут ожидания ответа сервера (соединение установлено)"
    if any(word in explanation for word in ("timed out", "timeout", "winerror 10060")):
        return "HTTPS/TCP: тайм-аут (возможна фильтрация или проблема маршрута)"
    if "proxy" in explanation or "tunnel" in explanation:
        return "Прокси/туннель: соединение не удалось"
    if "connection refused" in explanation or "winerror 10061" in explanation:
        return "TCP: удалённый узел отказал в соединении"
    return f"Сеть: {type(exc).__name__} (проверьте DNS/прокси/доступ к серверу)"


def _probe_source(host: str, *, timeout: float) -> SourceHealthItem:
    source = str(host or "").strip()
    url = f"https://{source}/"
    try:
        # No download-style retries during health checks. Use the same optional
        # local upstream bridge that Python search and FFmpeg use.
        with requests.Session() as session:
            session.trust_env = False
            session.headers.update({"User-Agent": USER_AGENT})
            if (user_proxy_enabled() or current_dns_mode() == DNS_MODE_AUTO) and hasattr(session, "proxies"):
                bridge = ensure_cloudflare_playwright_proxy()
                session.proxies.update({"http": bridge, "https": bridge})
            response = session.get(
                url, timeout=(timeout, timeout), allow_redirects=True, stream=True,
            )
            try:
                status = int(getattr(response, "status_code", 0) or 0)
            finally:
                response.close()
        blocked = status in {401, 403, 429, 451, 503}
        # Any valid HTTP response confirms that TCP/TLS/HTTP worked, including
        # 501 (unsupported method) and 5xx (server failure). This is a transport
        # check, NOT a claim that the search API or downloads will succeed.
        # Keep policy/authentication/challenge statuses separately marked.
        reachable = bool(100 <= status <= 599)
        return SourceHealthItem(
            source=source,
            url=url,
            reachable=reachable,
            blocked=blocked,
            status_code=status or None,
            error="" if reachable else f"HTTP {status}" if status else "HTTP error",
        )
    except Exception as exc:
        return SourceHealthItem(
            source=source,
            url=url,
            reachable=False,
            blocked=False,
            error=classify_network_error(exc),
        )


def _probe_source_detailed_once(host: str, *, timeout: float) -> SourceHealthItem:
    """DNS/TCP/TLS/HTTP diagnostic using one real TLS connection.

    Uses GET instead of HEAD because some hosts respond HTTP 501 to HEAD.
    Reads only the status line; closes the socket without reading the body,
    downloading audio, saving cookies, or logging request paths.
    """
    source = str(host or "").strip()
    info: dict[str, object] = {}
    tls_ms = None
    http_ms = None
    phase = "connect"
    http_started = None
    try:
        raw, info = _connect_target_with_info(source, 443, timeout=timeout, diagnostic=True)
        began_tls = time.monotonic()
        phase = "tls"
        try:
            with ssl.create_default_context().wrap_socket(raw, server_hostname=source) as tls:
                tls_ms = round((time.monotonic()-began_tls)*1000)
                tls.settimeout(timeout)
                http_started = time.monotonic()
                phase = "http_send"
                tls.sendall((f"GET / HTTP/1.1\r\nHost: {source}\r\n"
                             "User-Agent: AudioKnigi-Connectivity/1.0\r\n"
                             "Accept: */*\r\nConnection: close\r\n\r\n").encode("ascii"))
                phase = "http_read"
                status_line = tls.recv(256).split(b"\n", 1)[0]
                http_ms = round((time.monotonic()-http_started)*1000)
            phase = "http_parse"
            match = re.match(rb"HTTP/\d(?:\.\d)?\s+(\d{3})", status_line)
            if not match:
                raise OSError("HTTPS: некорректный ответ сервера")
            code = int(match.group(1))
            blocked = code in {401, 403, 429, 451, 503}
            note_http_response(source, 443, str(info.get("address", "")))
            return SourceHealthItem(source, f"https://{source}/", True, blocked,
                                    status_code=code, dns_provider=str(info.get("dns_provider", "")),
                                    ip_address=str(info.get("address", "")),
                                    dns_ms=int(info.get("dns_ms", 0)), tcp_ms=int(info.get("tcp_ms", 0)),
                                    tls_ms=tls_ms, http_ms=http_ms, alternate_attempted=bool(info.get("alternate_attempted", False)),
                                    cloudflare_addresses=tuple(info.get("cloudflare_addresses", ())),
                                    system_addresses=tuple(info.get("system_addresses", ())),
                                    system_dns_checked=bool(info.get("system_dns_checked", False)),
                                    system_dns_error=str(info.get("system_dns_error", "")),
                                    attempted_routes=tuple(info.get("attempt_log", ())),
                                    fallback_status=str(info.get("fallback_status", "")))
        finally:
            raw.close()
    except Exception as exc:
        message = classify_network_error(exc)
        if message.startswith("HTTPS/TCP: тайм-аут"):
            if phase in {"http_send", "http_read"}:
                message = "HTTP: тайм-аут ожидания ответа сервера (TCP/TLS установлены)"
            elif phase == "tls":
                message = "TLS: тайм-аут защищённого соединения (TCP установлен)"
        if http_started is not None and http_ms is None:
            http_ms = round((time.monotonic()-http_started)*1000)
        if hasattr(exc, "details"):
            info = getattr(exc, "details", {})
        root_exc = getattr(exc, "__cause__", None) or exc
        winerror = getattr(root_exc, "winerror", None)
        errno = getattr(root_exc, "errno", None)
        code = (f"WinError {winerror}" if isinstance(winerror, int)
                else f"errno {errno}" if isinstance(errno, int) else "")
        return SourceHealthItem(source, f"https://{source}/", False,
                                error=message,
                                error_code=code,
                                dns_provider=str(info.get("dns_provider", "")),
                                ip_address=str(info.get("address", "")),
                                dns_ms=info.get("dns_ms"), tcp_ms=info.get("tcp_ms"),
                                tls_ms=tls_ms, http_ms=http_ms,
                                alternate_attempted=bool(info.get("alternate_attempted", False)),
                                cloudflare_addresses=tuple(info.get("cloudflare_addresses", ())),
                                system_addresses=tuple(info.get("system_addresses", ())),
                                system_dns_checked=bool(info.get("system_dns_checked", False)),
                                system_dns_error=str(info.get("system_dns_error", "")),
                                attempted_routes=tuple(info.get("attempt_log", ())),
                                fallback_status=str(info.get("fallback_status", "")))


def _probe_source_detailed(host: str, *, timeout: float) -> SourceHealthItem:
    """If HTTP stalls after TLS, try another Cloudflare A record once.

    A different-IP HTTP retry is only for this harmless GET / check. Keep
    one-attempt behavior for POST, media and hosts with a single IP. The hint
    also improves subsequent ordinary connections (including search) through
    the existing local DNS bridge. HTTPS certificate checking remains enabled.
    """
    first = _probe_source_detailed_once(host, timeout=timeout)
    if (first.reachable or not first.error.startswith("HTTP: тайм-аут")
            or not note_http_read_timeout(host, 443, first.ip_address, first.cloudflare_addresses)):
        return first
    # The first HTTPS response may have taken the full timeout. One small
    # additional attempt is preferable to displaying a false 'site offline'.
    second = _probe_source_detailed_once(host, timeout=min(timeout, 4.0))
    # If route selection did not change, report original failure rather than
    # hiding the timeout or repeatedly probing a single bad IP.
    if second.ip_address == first.ip_address:
        return first
    return replace(second, alternate_attempted=True,
                   first_http_timeout_ip=first.ip_address,
                   fallback_status="http_route_switched" if second.reachable else "http_route_failed")


def _search_endpoint(key: str) -> str:
    """Safe, user-facing endpoint type, never a URL with search terms."""
    return {
        "yakniga": "GraphQL POST",
        "akniga": "Каталог GET",
        "izibuk": "Каталог GET",
        "librivox": "Archive.org / LibriVox API",
        "uknig": "Каталог GET",
    }.get(str(key or "").casefold(), "Поиск API")


def _classify_search_error(exc: BaseException) -> str:
    """Report a failing *internal* DNS bridge without implying user proxy use."""
    from ..core import SiteStructureChanged
    if isinstance(exc, requests.exceptions.ProxyError):
        if current_dns_mode() == DNS_MODE_AUTO and not user_proxy_enabled():
            return "Внутренний DNS-мост: HTTPS-соединение до сайта не установлено"
    if isinstance(exc, requests.exceptions.HTTPError):
        response = getattr(exc, "response", None)
        code = getattr(response, "status_code", None)
        if isinstance(code, int):
            return f"Поисковый API ответил HTTP {code}"
    if isinstance(exc, SiteStructureChanged):
        return "Ответ поискового API не соответствует ожидаемой структуре"
    return classify_network_error(exc)


def _probe_search(provider, query: str) -> SourceHealthItem:
    """Query a real provider search, not just its site's homepage.

    Zero results is success if the request completed. Never serialize query
    content, cookies, media links or raw HTTP exceptions into the UI report.
    """
    import time
    started = time.monotonic()
    key = str(provider.display_name)
    provider_key = str(getattr(provider, "key", ""))
    endpoint = _search_endpoint(provider_key)
    # The shared diagnostic defaults to "Поттер", which should not be expected
    # in LibriVox's public-domain catalogue. Use a disclosed English test term
    # for this provider only; normal user searches remain unchanged.
    probe_query = "Sherlock Holmes" if provider_key == "librivox" and query == "Поттер" else query
    if probe_query != query:
        endpoint += " (тест: Sherlock Holmes)"
    from ..providers.base import SourceProvider
    # Do not report the base provider's empty placeholder as a successful query.
    # Lightweight fake providers used in offline tests do not derive from it.
    if isinstance(provider, SourceProvider) and type(provider).search is SourceProvider.search:
        return SourceHealthItem(key, "", False, error="Поиск не поддерживается",
                                search_checked=True, search_supported=False, tcp_ms=0,
                                search_endpoint=endpoint)
    try:
        results = provider.search(probe_query)
        count = len(list(results or ()))
        return SourceHealthItem(key, "", True, search_checked=True, search_results=count,
                                tcp_ms=round((time.monotonic()-started)*1000), search_endpoint=endpoint)
    except Exception as exc:
        message = _classify_search_error(exc)
        if message.startswith("Сеть: "):
            message = "Ошибка поиска: " + type(exc).__name__
        return SourceHealthItem(key, "", False, error=message, search_checked=True,
                                tcp_ms=round((time.monotonic()-started)*1000), search_endpoint=endpoint)


def check_source_search(query: str = "Поттер") -> SourceHealthOutcome:
    """On-demand provider search check; called only by explicit UI action."""
    from ..providers import registered_providers
    cleaned = str(query or "").strip()
    if len(cleaned) < 3:
        cleaned = "Поттер"
    providers = registered_providers()
    # Parallel providers must not be serialized by a blocked site.
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(providers))),
                            thread_name_prefix="source-search-check") as pool:
        futures = {pool.submit(_probe_search, provider, cleaned): provider for provider in providers}
        found = {}
        for future in as_completed(futures):
            provider = futures[future]
            try:
                found[provider.key] = future.result()
            except Exception as exc:
                found[provider.key] = SourceHealthItem(str(provider.display_name), "", False,
                    error="Ошибка поиска: " + type(exc).__name__, search_checked=True)
    return SourceHealthOutcome([found[provider.key] for provider in providers])


def check_source_health(*, timeout: float = 3.0, detailed: bool = False) -> SourceHealthOutcome:
    """Probe source hosts concurrently. Detailed mode is opt-in (manual UI)."""
    hosts = tuple(dict.fromkeys(SUPPORTED_SOURCE_HOSTS))
    if not hosts:
        return SourceHealthOutcome([])
    timeout = max(1.0, min(8.0, float(timeout or 3.0)))
    by_host: dict[str, SourceHealthItem] = {}
    probe = _probe_source_detailed if detailed else _probe_source
    with ThreadPoolExecutor(max_workers=min(len(hosts), 8), thread_name_prefix="source-health") as pool:
        futures = {pool.submit(probe, host, timeout=timeout): host for host in hosts}
        for future in as_completed(futures):
            host = futures[future]
            try:
                by_host[host] = future.result()
            except Exception as exc:  # defensive: _probe_source already contains errors
                app_logger.exception("Source health worker failed for %s", host)
                by_host[host] = SourceHealthItem(
                    source=host,
                    url=f"https://{host}/",
                    reachable=False,
                    error=classify_network_error(exc),
                )
    outcome = SourceHealthOutcome([by_host[host] for host in hosts if host in by_host])
    app_logger.info(
        "SOURCE HEALTH | reachable=%d | unavailable=%d | blocked=%d | total=%d",
        outcome.reachable_count,
        outcome.unavailable_count,
        outcome.blocked_count,
        len(outcome.items),
    )
    return outcome


__all__ = ["SourceHealthItem", "SourceHealthOutcome", "check_source_health", "check_source_search", "classify_network_error"]
