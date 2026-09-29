# Round 66 — Round 65 audit follow-up

Applied confirmed findings from the 2026-09-29 review:

- removed the racy/redundant `jobs.empty()` pre-check from segmented workers and rely on atomic `get_nowait()` / `queue.Empty`;
- removed the second identical six-regex absolute-path redaction pass from support bundles while preserving the privacy-first pre-mask;
- added a 30 MiB minimum source reserve when both remote size and duration metadata are unknown, so a completely full volume cannot bypass preflight;
- treat HTTP 403 source-health responses as network-reachable but blocked/challenged, allowing browser-backed operations to remain available;
- capture and consume a `.pl.txt` playlist body from Playwright/Chromium before closing the browser context, falling back to `requests` only when no browser body is available;
- accept legacy `qt_queue.json` wrapper objects (`items` / `queue`) during backup restore and normalize them to the current list format;
- log PoleKnig author-catalog page failures instead of silently dropping a page;
- schedule transient `QMessageBox` instances for deletion after their result is read.

Reviewed and intentionally unchanged:

- HTTP 416 restart recursion is already bounded to one restart in practice: the stale `.part` is deleted before the recursive call, so the second request has `existing == 0` and a repeated 416 raises instead of recursing again;
- Python 3.8 compatibility is outside the declared Python 3.11+ project contract;
- `runtime_exact.json` contains only one `Проверить системный звук` key and is covered by a duplicate-key regression test;
- runtime regex localization executes before prefix localization, so the reported prefix-shadowing conflict does not occur;
- `trust_env=False` remains deliberate network isolation and matches the application HTTP-session policy;
- broad DE/UK wording cleanup, provider parser extraction, executor cancellation semantics, IPv6-route probing, and accessibility string-ID refactoring are architectural/style follow-ups rather than confirmed runtime regressions.
