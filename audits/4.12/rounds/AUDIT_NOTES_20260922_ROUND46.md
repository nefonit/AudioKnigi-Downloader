# Round 46 — Fourth external-audit hardening follow-up (2026-09-22)

Round 46 validates the fourth external audit against the current Round 45 source tree. Only findings that could be reproduced or proven from current runtime contracts were changed; speculative import, localization-order, and cancellation claims were not applied mechanically.

## Confirmed fixes

- Knigavuhe structured person nodes are now terminal once a valid `name` is found, so nested metadata such as genre/category `name` fields cannot leak into author or narrator lists.
- Queue deserialization normalizes legacy/resume `download_mode="parts"` to the queue UI contract `selected`; `full_mp3` remains unchanged, and unknown values fail safe to `selected`.
- Persisted `Track.selected` values are normalized to real booleans, including legacy string forms such as `"false"`, `"0"`, `"off"`, `"нет"`, and `"ні"`.
- AudioKnigi title cleanup can remove multiple independently corroborated coauthor prefixes consecutively instead of stopping after the first author and leaving a leading comma/second author in the title.
- Easy-mode search no longer inherits an all-off source filter hidden in Advanced mode. If every Advanced source action is unchecked, Easy mode searches all configured sources without mutating the user's Advanced checkboxes.
- Saving Settings preserves the existing `AppSettings` object identity by updating it in place, preventing controllers that retained the shared settings reference from reading stale values after Save.
- Windows `.url` drag-and-drop parsing accepts `URL="https://..."` and single-quoted variants while still validating the unquoted address through `valid_site_url()`.
- Missing-media decision dialogs are parented to the stable main window rather than a transient operation/progress dialog that may be closed or replaced during cancellation.
- Queue drag reordering is disabled whenever an active queue task exists, preventing list-order mutation while the worker/UI are tracking a running task by identity/index.
- Windows native media-event filtering rejects a null message pointer before calling `MSG.from_address()`.
- After a full-MP3 playlist refresh, `DownloadRequest.selected_indices` is resynchronized with the refreshed book track set so the returned request/result cannot retain stale pre-refresh indices.

## Reviewed and intentionally unchanged

- Support-bundle secret replacement already consumes the matched unquoted value by replacing the complete regex match; using a callable replacement also avoids replacement-string backreference interpretation.
- Segmented-download cancellation intentionally preserves `.segNNN` partials for resume and already removes a temporary `.assembling` file on failed assembly. No blanket partial deletion was added.
- Package-relative imports match the repository layout; repeated `__init__.py` filenames belong to distinct subpackages and are not an import collision.
- Runtime localization checks regex rules before exact/prefix/literal fallbacks, so the reported prefix-before-regex collision does not match the current implementation. Current `runtime_exact.json` parses without duplicate JSON keys.
- The project's declared Python runtime is >=3.11, so `ThreadPoolExecutor.shutdown(cancel_futures=True)` is supported. Running HTTP calls still cannot be force-killed safely by `Future.cancel()`; no risky thread termination rewrite was introduced.
- Strict post-hydration AudioKnigi relevance filtering remains in place. Weakening it when metadata hydration fails would reintroduce unrelated server recommendations that earlier rounds explicitly removed.
- Playwright `page.goto()` cancellation latency, thread-local HTTP-session lifetime, global JSON locking, provider registration structure, and proxy half-close handling are broader architecture/performance topics without a reproduced Round 46 correctness failure.

## Verification

- Round 46 focused regressions: **12 passed**.
- Full pytest suite: **586 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=255`, `known_shape_incompatibilities=128`, `resolved=0`).
- Full parity: **PASS 61/61**.
- Qt import audit: **OK** (75 project modules reachable, no legacy frontend path).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.
