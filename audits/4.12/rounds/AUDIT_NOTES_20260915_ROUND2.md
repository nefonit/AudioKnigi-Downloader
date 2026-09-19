# Follow-up audit notes — 2026-09-15

This file records how the second external audit was reconciled with the actual 4.12.42 source tree. Findings were not applied mechanically: each item was checked against current behavior and existing regression contracts.

## Confirmed and fixed

- Explicit 125% UI scale could be interpreted as the legacy automatic value when a fresh mapping was deliberately saved without the migration marker.
- `persist_browser_cookies` now accepts the historical optional `headers` argument.
- Malformed/absent track indices now fail with a controlled validation result instead of leaking raw `TypeError`/`ValueError` through full-MP3/preflight paths.
- Two-pass loudnorm handles `-inf`/other non-finite first-pass measurements by falling back to normal one-pass loudnorm.
- Windows support bundles redact absolute drive/UNC paths outside the user's home and log tails are always valid UTF-8.
- Recovery scanning accepts UTF-8 BOM in `resume.json`.
- Accessible fallback names preserve visible Cyrillic content even under English/German/Ukrainian UI languages.
- QComboBox accessibility callbacks no longer retain strong references to deleted wrappers.
- Empty/error search results restore focus to the visible Easy-mode input when Easy mode is active.
- F1 opens keyboard/accessibility help; Shift+F1 remains contextual help.
- Application-copied audiobook URLs stay suppressed until clipboard content actually changes.
- History row deletion avoids a full synchronous history/table/icon reload and rolls back the in-memory removal if persistence fails.
- Circular search animation self-stops when the widget becomes effectively invisible.
- Ambiguous dash-separated audiobook page titles no longer invent an author when independent metadata does not identify one.
- Ukrainian unresolved-queue error wording was corrected to the plural-neutral form.

## Reviewed but not changed

- `session = session or get_http_session()` in `_discover_narration_variants` is not a `NameError`: `session` is already a function parameter.
- Re-normalizing a pre-normalized PoleKnig title key is redundant but idempotent in the current implementation; no runtime type mismatch exists.
- The local proxy closes the upstream socket in the handler `finally`, while `ThreadingTCPServer` owns the client socket; the reported relay leak was not reproduced from the current code.
- `server.shutdown()` is called from outside the server thread and daemon request threads do not block `serve_forever()` shutdown; the claimed atexit deadlock was not established.
- Keeping `.full-source` after an FFmpeg failure can intentionally avoid re-downloading a large source on retry; it was not treated as an unconditional leak.
- Repeated `Popen.communicate(timeout=...)` is used as cancellable polling and the current cancellation path kills the process; the report's claimed guaranteed Windows deadlock was not accepted without a reproducer.
- Range segment files are resumable state. Deleting all segments on every assembly failure would defeat recovery after low-disk/interruption scenarios.
- `_DURATION_CACHE` is bounded; churn can reduce hit rate but is not an unbounded memory leak.
- `use_templates=False` is an explicit per-request override, while `None` means inherit global settings; queue serialization preserves that distinction intentionally.
- Media-key shutdown was already present in `closeEvent`, so no additional change was needed.
- Event-sound QMediaPlayers are bounded and retired with `deleteLater`; the report describes a possible performance tradeoff rather than an unbounded resource leak.
- The filename policy that replaces a metadata audio extension with the chosen output extension is an established regression-tested contract and was kept.
- Existing German `Bereiche` and Ukrainian duration-progress wording are established localization contracts; they were not changed as runtime defects.

## Verification

`pytest -q` → **216 passed**.
