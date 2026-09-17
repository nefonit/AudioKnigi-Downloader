# Diagnostic support bundle

Use **Help → Diagnostics → Create diagnostic bundle…** to create a ZIP for troubleshooting.

The bundle contains:

- application/Python/platform and dependency versions;
- sanitized settings;
- bounded tails of the application/error logs and last crash report when present;
- queue status/attempt counters without book titles or media URLs.

Privacy rules: API keys, cookies, passwords, raw configured URLs, audiobook media, book titles, full executable paths, AppData paths and window geometry are excluded, generalized or redacted. User-home prefixes in configured paths are represented as `~`.
