from __future__ import annotations

"""Lightweight reachability checks for the built-in audiobook sources."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import requests

from ..core import USER_AGENT
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


def _probe_source(host: str, *, timeout: float) -> SourceHealthItem:
    source = str(host or "").strip()
    url = f"https://{source}/"
    try:
        # Use a one-shot session with retries disabled. The application-wide
        # Cloudflare DoH socket resolver still applies, while startup probing
        # stays bounded instead of inheriting download-oriented retry delays.
        with requests.Session() as session:
            session.trust_env = False
            session.headers.update({"User-Agent": USER_AGENT})
            response = session.get(
                url,
                timeout=(timeout, timeout),
                allow_redirects=True,
                stream=True,
            )
            try:
                status = int(getattr(response, "status_code", 0) or 0)
            finally:
                response.close()
        blocked = status in {401, 403, 429, 451, 503}
        # 401/403/429/451/503 can represent authentication, policy, a browser challenge, or temporary protection
        # rather than a dead host. Playwright-backed source operations may still
        # succeed, so count those responses as network-reachable while retaining
        # blocked=True for diagnostics. 404/405 likewise prove that the host answered.
        reachable = bool(200 <= status < 400 or status in {401, 403, 404, 405, 429, 451, 503})
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
            error=str(exc).strip() or exc.__class__.__name__,
        )


def check_source_health(*, timeout: float = 3.0) -> SourceHealthOutcome:
    """Probe all supported source hosts concurrently without blocking the UI."""
    hosts = tuple(dict.fromkeys(SUPPORTED_SOURCE_HOSTS))
    if not hosts:
        return SourceHealthOutcome([])
    timeout = max(1.0, min(8.0, float(timeout or 3.0)))
    by_host: dict[str, SourceHealthItem] = {}
    with ThreadPoolExecutor(max_workers=len(hosts), thread_name_prefix="source-health") as pool:
        futures = {pool.submit(_probe_source, host, timeout=timeout): host for host in hosts}
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
                    error=str(exc).strip() or exc.__class__.__name__,
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


__all__ = ["SourceHealthItem", "SourceHealthOutcome", "check_source_health"]
