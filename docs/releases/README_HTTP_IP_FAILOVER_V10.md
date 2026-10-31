# V10 — HTTP-stalled IP diagnostics and Cloudflare route preference

Base: AudioKnigi Downloader 4.12.42, V9 (HTTP phase diagnostic).

## Why this change
Cloudflare returned two A records for audioknigi.com.ua: the first accepted TCP/TLS,
but GET / did not return an HTTP status within eight seconds. The other address
was never tried because V9 considered the successful TLS handshake sufficient.

## Behavior
1. A manual **detailed** HTTPS health check still tries GET / through TLS and
   validates the server certificate. If that HTTP read times out and Cloudflare
   supplied more than one *different* IP, the app remembers the stalled IP
   for 90 seconds and tries one other IP (up to four extra seconds).
2. The next connections through the built-in DNS bridge (AUTO mode) prefer a
   non-stalled Cloudflare IP during the 90-second window. This also helps a
   subsequent normal search after running diagnostics. The DNS response itself
   is NOT modified. Strict Cloudflare mode still uses Cloudflare IPs only;
   system mode and explicitly configured user proxies are not overridden.
3. The diagnostic report indicates the original HTTP-stalled IP and the final
   route. If both IPs fail, the test reports a failure rather than declaring
   the site reachable. There is no infinite retry loop.
4. HTTP 4xx/5xx are recorded as received HTTP responses (reachable network),
   not as indications that search or download works.

## Boundaries
- Only a read-only GET / health check triggers this HTTP-level failover.
  Downloads and GraphQL POST requests are not replayed.
- If a user starts search without running diagnostics first, a fresh
  HTTP-read timeout may still occur. The routing hint is short-lived and
  in-memory only, so restarts will clear it.
- Different IPs do NOT guarantee a healthy service or that the search API
  will work. Cloudflare One/WARP may still be required for some domains.
- No actual Windows + Cloudflare One OFF network testing in this environment.

## Windows validation
1. Keep an untouched V9 backup. Start V10, set DNS to Auto and leave the
   user proxy disabled.
2. With Cloudflare One OFF, run the manual all-source network diagnostic.
3. If first audioknigi.com.ua IP stalls but another IP works, expect HTTP 200
   on the alternative and a message identifying the original HTTP-stalled IP.
4. Immediately run the real search; compare search time/results with V9.
5. Repeat with Cloudflare One ON, and test all other sources as regressions.

Tested offline using pytest and synthetic socket/TLS fixtures. No actual source
availability guarantees. The user's previous V7-V9 implementations are kept.
