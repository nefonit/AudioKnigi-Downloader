# Cloudflare 1.1.1.1 DNS routing — 4.12.31

## What this feature is

AudioKnigi Downloader uses Cloudflare **DNS-over-HTTPS (DoH)** for public hostname resolution performed by the application. This is a DNS privacy/routing feature. It is **not** the full Cloudflare WARP VPN tunnel and does not claim to tunnel all payload traffic through WARP.

## Resolver

- DoH endpoint: `https://cloudflare-dns.com/dns-query`
- bootstrap IPs: `1.1.1.1`, then `1.0.0.1`
- system/ISP DNS fallback for public hostnames: disabled
- local/numeric exceptions: numeric IPs, `localhost`, `.local`

## Network clients

### Requests/Python

Public Python socket lookups are routed through `audioknigi.network_dns.cloudflare_getaddrinfo`. `requests` sessions disable environment proxy inheritance (`trust_env=False`) so an external proxy cannot silently change the application's DNS path.

### Playwright/Chromium

Chromium uses an application-owned localhost HTTP/CONNECT proxy. The proxy resolves destination names via Cloudflare DoH. Chromium receives Cloudflare secure-DNS arguments and QUIC is disabled.

### FFprobe

Only remote URL FFprobe operations need network DNS. They receive `-http_proxy <local Cloudflare proxy>`. Local-file FFprobe is unaffected.

## Diagnostics

At startup look for:

`NETWORK DNS | provider=Cloudflare 1.1.1.1 | mode=DoH-secure | active=True ... system_fallback=False`

and:

`NETWORK DNS STATE | provider=Cloudflare 1.1.1.1 | mode=DoH-secure | active=True | system_fallback=False`

Playwright/proxy activity is logged separately with `client=Playwright/Chromium` or `client=Chromium-proxy`; remote FFprobe logs `client=FFprobe`.

If Cloudflare DoH is unavailable, public-name resolution fails instead of silently falling back to the ISP/system resolver. This is intentional for the requested strict DNS policy.
