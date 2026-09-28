# Settings schema

`audioknigi.config.settings` is the single normalization/migration boundary for `settings.json`.

Current schema: version 2.

Migration v1 → v2 renames the historically misleading `auto_chunk_min_kbps` key to
`auto_chunk_min_kbytes_per_sec`. The UI has always displayed KB/s; the migration changes the
name, not the arithmetic or user-visible behavior.

Migration v2 → v3 adds `dns_mode`. Supported values are `auto` (default: Cloudflare DoH with
system-DNS fallback and a circuit breaker), `cloudflare` (strict Cloudflare DoH only), and
`system` (Windows/system resolver only). Invalid or missing values normalize to `auto`.

Unknown settings are preserved to avoid breaking plugins/future fields. New settings should be
added to `DEFAULT_SETTINGS` and normalized in `migrate_settings()` rather than scattered across UI code.
