# Runtime contract hardening — 2026-09-12

This follow-up review starts from 4.12.33 Runtime Integrity Hardened and produces 4.12.34.

## Confirmed external facts

The audit text treated the current release baseline as fictional. That part was stale relative to 2026-09-12. The project therefore keeps the verified release baseline rather than downgrading to 2025-era versions:

- CPython 3.14.7 is a released maintenance build (2026-08-05).
- Chrome 153 is in the Stable channel (2026-09-08).
- PySide6 6.11.2, Playwright 1.62.0, Pillow 12.3.0, Requests 2.32.5 and PyInstaller 6.22.2 are published releases.

## Confirmed runtime fixes

- `DownloadRequest.selected_indices=None` now consistently means “all tracks”. Explicit `[]` remains an invalid empty selection.
- Duplicate preflight, deletion, full-MP3 results, normal results, queue serialization/deserialization, queue row summaries, queue reanalysis and Qt download status all honor that contract.
- `AppSettings` is now handled through Mapping/MutableMapping contracts instead of stale `dict` checks in settings synchronization and player persistence.
- Backup restore reloads typed settings through `load_app_settings()` instead of replacing `self.settings` with a raw dict.
- Audioknigi provider cancellation raises `Cancelled` instead of returning an empty result.
- Closing/cancelling the first-run wizard now persists `first_run_complete` and continues into the app instead of exiting.
- Stable-ID translation no longer calls `.format()` when no interpolation arguments were supplied, preventing warnings for literal brace examples.
- Source/frozen self-test failures print full tracebacks in developer mode. Accessibility cleanup continues through player/sound/tray cleanup even when `window.close()` fails.
- Refactor leftovers were cleaned: the shadowed `source_name` import, unused search aliases, `search.py`'s unused `copy` import, and over-indentation in `source_analysis.py`.
- Home-directory log sanitization now uses `%USERPROFILE%` on Windows and `~` on Unix-like systems.
- German shortcut help now uses consistent `Strg` / `Umschalt` terminology.
- `THIRD_PARTY_NOTICES.md` now documents the release/runtime dependency surface, including the fact that the exact FFmpeg/FFprobe license obligations depend on the binary actually bundled.

## Already fixed / stale findings

No additional code change was needed for these items because the 4.12.33 base already contained the fix:

- malformed URL ports are caught;
- disk-space preflight uses `create=False`;
- frozen support bundles have dependency-version fallbacks;
- locale runtime regex uses DOTALL and the audioknigi fast-HTTP specific rule precedes the generic “Анализирую …” rule;
- Ukrainian legacy cancellation/queue strings are present;
- locale JSON currently has no duplicate keys;
- support-bundle path redaction handles both slash styles and UTF-8 log tails safely;
- zero-based unfinished track indices are preserved;
- track status uses language-neutral status codes;
- split-module undefined globals are covered by the dedicated quality gate.

The localization audit was strengthened so duplicate JSON keys now fail the gate instead of being silently overwritten by Python's JSON loader.

## Verification

Working-tree verification for this release:

- pytest: 98 passed
- Full Parity: 61/61
- localization audit: OK (ru/uk/de/en)
- Qt import audit: OK (72 project modules)
- exception audit: PASS (113 reviewed cases)
- unused-import audit: OK (18 implementation modules)
- undefined-global audit: OK (76 modules)
- historical regression: 275 passed, no new regressions
- compileall: OK
- wheel build: `audioknigi_downloader-4.12.34-py3-none-any.whl`; all six locale JSON catalogs included

The container does not provide a Windows/PySide6/NVDA/JAWS acceptance environment, so those interactive acceptance tests remain a release-machine gate.
