# 4.12.31 — Accessibility diagnostics, Advanced editors and Cloudflare DNS audit

## Scope

This follow-up implements the Windows field report collected from real NVDA/JAWS runs and the request to keep application DNS resolution on Cloudflare 1.1.1.1.

The active application remains version **4.12.31**. Historical files under `history/` are archival and were not changed into active runtime code.

## Screen-reader diagnostics

The accessibility layer now emits explicit diagnostics that can be verified from a Windows `app.log` without inferring behavior indirectly:

- `ACCESSIBILITY UIA | provider=tk-uia | active=True/False` — whether the Windows UI Automation provider actually enabled;
- `SCREEN READER GESTURE | ...` — whether the physical Insert/Up gesture reached the application fallback;
- `SCREEN READER READ LINE | ... value=... backend=...` — value exposed/read from the focused editor and delivery result;
- `HOTKEY | shortcut=... vk=... source=windows_vk layout_independent=True` — physical Windows VK hotkey routing;
- `SEARCH ACCESSIBILITY | focus_moved=True ...` — actual confirmed focus transfer to the search results table;
- `SEARCH ACCESSIBILITY | announcement_delivered=True ...` — NVDA/JAWS delivery of the results-table announcement.

Search focus logging no longer records success immediately after `focus_set()`. It waits for the actual Tk focus transition (`FocusIn`) or verifies the real focus owner. This avoids false negative/positive diagnostics on Tk 8.6.

## Advanced-mode editors

The Advanced Book editor now follows the same accessibility contract as the Simple editor:

- accessible name: **Название, автор или ссылка**;
- current editor value is available to the Windows UIA provider;
- Prism-backed `Insert+Up` fallback reads the current value when the reader passes the gesture through to Tk;
- text that is not a supported URL is treated as title/author search input and opens/runs Advanced Search rather than being rejected as an invalid URL.

The same explicit `Insert+стрелка вверх` editor guidance is applied to Advanced Search, Queue and relevant editable Settings/Audiobookshelf fields.

After successful search results are rendered, the first result is selected and focus moves to the visible results Treeview. The move is announced with the result count and Up/Down guidance. The implementation does not aggressively steal Windows focus if the application itself is inactive; it waits for the application's natural focus return before moving focus internally.

## Layout-independent hotkeys

Global `Ctrl+L`, `Ctrl+D`, `Ctrl+F`, `Ctrl+Q`, `Ctrl+H` continue to use physical Windows virtual-key handling as a fallback for non-Latin layouts. Diagnostics record the VK and resolved command. Latin Tk bindings remain in place without double execution.

## Cloudflare DNS architecture

This implementation is **DNS-only Cloudflare 1.1.1.1 / DNS-over-HTTPS**, not the full Cloudflare WARP VPN tunnel.

### Python networking (`requests`)

- `socket.getaddrinfo` is replaced on Windows for public hostnames by the application's strict Cloudflare DoH resolver.
- DoH queries target `https://cloudflare-dns.com/dns-query`.
- The DoH hostname itself is bootstrapped directly with `1.1.1.1`, then `1.0.0.1`; no ISP/system DNS is needed for the Cloudflare resolver.
- Public-name resolution does **not** fall back to the system resolver when Cloudflare fails.
- Numeric IPs, `localhost` and `.local` names bypass public DoH intentionally.
- Application `requests.Session` objects use `trust_env=False`, preventing `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` environment variables from bypassing the application's resolver policy.

### Playwright / Chromium

Chromium is a separate process and cannot inherit Python's socket hook. Every active Playwright Chromium launch therefore uses a localhost HTTP/CONNECT proxy owned by the application:

1. Chromium connects only to the local proxy.
2. The proxy resolves destination hostnames through the same Cloudflare DoH resolver.
3. Chromium also receives secure-DNS Cloudflare arguments and `--disable-quic` so QUIC cannot bypass the TCP proxy route.

### Remote FFprobe

Remote URL duration probes can resolve names inside FFprobe itself, outside Python. The remote FFprobe path therefore receives FFmpeg's `-http_proxy` input option pointing at the same localhost Cloudflare-resolving proxy. Local-file FFprobe remains local and does not need DNS.

### Shutdown

The local Cloudflare proxy is daemon-threaded, registered for shutdown, and explicitly stopped from `AudioKnigiApp.destroy()`.

## Tk scaling/root recreation hardening discovered during regression

The extended regression run exposed a separate process-lifetime issue: Tk can retain the previous root's `tk scaling` after a root is destroyed. A new root could therefore create its child widgets while still at 175/200% and only later apply the saved 100% value, leaving stale requested widget sizes.

Fixed behavior:

- the native process DPI baseline is retained once;
- every new `AudioKnigiApp` root resets Tk to that baseline **before child widgets are created**;
- the saved user scale is applied later through the normal startup path;
- `_apply_scale(silent=True)` no longer writes transient/test/startup scale changes back to settings.

This also removes an order-dependent search-focus regression in long GUI test runs.

## Verification

Targeted accessibility/DNS/scaling regression sets passed before the complete run.

The complete active suite was executed in independent Xvfb groups and passed:

- 136 passed
- 138 passed
- 115 passed
- 56 passed
- 13 passed
- 27 passed

**Total: 485/485 passed.**

`python -m compileall -q audioknigi tests` also succeeds.

## Windows acceptance note

Linux/Xvfb verifies Tk logic, source paths and build/runtime contracts but cannot emulate real Windows UI Automation, NVDA/JAWS gesture interception, Chromium networking or Windows DNS. The new `app.log` diagnostics are intentionally detailed so a real Windows smoke test can confirm each layer directly.
