# Selective upstream proxy + actual search diagnostic (experimental)

Settings → Downloads & network:
- `Proxy`: supply an **existing working** `http://host:port` or `socks5h://host:port` URL. No credentials.
- `Proxy sites`: comma-separated supported site domains such as `akniga.org, yakniga.org, uknig.com`.
- With an empty site list, the legacy behavior (all destinations via configured proxy) is preserved.
- With a non-empty list, only matching hostnames and their subdomains use the upstream proxy, and other hostnames use the selected DNS mode and direct TCP.
- A redirect/media CDN on a different hostname does **not** inherit the book site route. Add that exact public hostname to the list if needed. Hostnames must be public DNS names; no URL schemes, ports, masks, or credentials.
- `Check real source searches` runs provider search adapters with the Search tab text (fallback: Поттер), shows found-item counts or sanitized error types, never downloads files.
- HTTP 200 on a homepage is not proof that any source adapter works. Search success (including zero results) does not prove downloads work.
- Does not provide a proxy service, VPN, WARP or bypass provider-level blocking. No proxy is enabled unless the user explicitly supplies its URL.
- Historical Akniga HLS-duration mismatch is **not** fixed by these network changes.

Source snapshot version: AudioKnigi 4.12.42 V3 baseline; targeted V4 experiment only, Windows/JAWS/NVDA/live-site testing outstanding.
