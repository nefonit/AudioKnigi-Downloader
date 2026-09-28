# Round 58 — resilient DNS policy and automatic recovery — 2026-09-28

Round 58 addresses the field failure where Cloudflare DoH TLS handshakes timed out and all three audiobook sources became unreachable at once. The previous resolver was intentionally strict (`system_fallback=False`), so one DoH transport failure could stall or fail Python requests, the Playwright proxy, and remote FFmpeg/FFprobe lookups.

## DNS modes

- `auto` (default): Cloudflare DoH first; on DoH transport/protocol failure, transparently resolve through the system resolver.
- `cloudflare`: strict Cloudflare-only mode, preserving the old no-fallback behavior for users who explicitly want it.
- `system`: bypass Cloudflare for public hostnames and use the OS resolver directly.

The setting is exposed under Settings → Download and network and is applied immediately after Save. It is normalized in settings schema v3.

## Circuit breaker and latency bound

- Cloudflare DoH per-bootstrap timeout is reduced to 1.5 seconds.
- After three consecutive Cloudflare transport failures, automatic mode opens a five-minute circuit breaker.
- While the circuit is open, lookups go directly to system DNS instead of repeatedly waiting on Cloudflare.
- After the cooldown, the next public lookup probes Cloudflare again; a success closes the fallback state automatically.
- NXDOMAIN remains a real Cloudflare DNS answer and does not trigger system fallback.

## Unified consumers

The same DNS policy now covers Python `socket.getaddrinfo`/requests, the local Playwright/Chromium proxy, and FFmpeg/FFprobe remote URL probing. System mode removes the local proxy from new Playwright launches and returns no FFmpeg proxy arguments; automatic/strict modes continue using the shared proxy, whose target resolution follows the current policy.

## Accessibility and user feedback

The main window polls DNS runtime state without network I/O. When automatic fallback is first used, the visible guidance/status area and Qt accessibility announcement say that Cloudflare DNS is temporarily unavailable and system DNS is being used. When Cloudflare succeeds again, the recovery is announced. Strict-Cloudflare all-source failures additionally point users to the Automatic DNS setting. The Help Center documents DNS modes, the five-minute recovery interval, VPN/WARP escalation, and diagnostics.

## Regression coverage

`tests/integration/test_round58_dns_resilience_20260928.py` verifies settings normalization, automatic fallback, circuit opening/skipping, strict mode, system mode, Playwright/FFmpeg policy alignment, bounded timeout/cooldown constants, Qt settings wiring, accessible fallback feedback, and Help Center guidance. Local validation before branch CI: 14 focused/settings tests passed, Qt localization audit OK, undefined-global audit OK, unused-import audit OK, full parity 61/61, historical regression 254 passed with 129 known shape incompatibilities.
