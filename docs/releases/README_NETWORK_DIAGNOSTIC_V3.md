# AudioKnigi Downloader 4.12.42: DNS/TCP and HTTP diagnostic V3 (experiment)

This update is based on the DNS-TRACE-FALLBACK-V2 source archive. It does not
alter normal search, download engines, proxy settings, or provider adapters.

## Field observations (Cloudflare One switched off)

- akniga.org, yakniga.org, uknig.com: Cloudflare successfully supplies IPs,
  but TCP times out after roughly four seconds. DNS changes alone cannot be
  expected to make a blocked or unroutable TCP path work.
- yakniga.org: System DNS failed, but the Cloudflare IP had already been tried
  and timed out. V2 reported misleading "DNS failed" as the primary error.
- knigavuhe.org: TCP and TLS succeeded; HTTP 501 was returned to the HEAD
  diagnostic. An HTTP response proves network connectivity, not search health.

## Fixes

1. TCP timeout remains the primary error when the system-DNS fallback check
   fails after a Cloudflare TCP attempt. The system DNS error remains reported
   in its own field, and the socket attempt log is preserved.
2. Manual source diagnostics send GET / instead of HEAD /. They read only the
   response status line, close the connection, and never download page bodies
   or media. This avoids spurious 501 from hosts that do not support HEAD.
3. Background reachability treats any valid HTTP response (100..599) as
   network-reachable; blocked-policy HTTP statuses retain the blocked flag.
   Network reachability does NOT imply successful book search or downloading.

## Validation

- 269 tests passed: unit, network, search, privacy, settings contracts.
- 440 passed, 1 failed: download, core, provider, queue, media tests. The failed
  historical regression audit reports two Qt-localization tests also reported
  as failing in V2. No live Windows/Cloudflare One or NVDA/JAWS validation.

## Test on Windows

With Cloudflare One OFF, run source diagnostics in auto mode, then Cloudflare
mode. Compare whether knigavuhe.org now returns 200 with GET and whether
 yakniga.org accurately reports TCP timeout with a separate system DNS error.
Use the real search tab to check search functionality separately.
Keep a stable-version backup; this is source code, not a Windows installer.
