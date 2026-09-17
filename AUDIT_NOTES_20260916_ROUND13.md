# AudioKnigi Downloader — audit follow-up Round 13 (2026-09-16)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND12_20260916`.

## Confirmed and fixed

- **Support-bundle destination semantics:** `create_support_bundle()` no longer uses `Path.with_suffix()` for arbitrary user names. A destination such as `bundle_1.0` now becomes `bundle_1.0.zip` instead of `bundle_1.zip`; an existing directory receives a timestamped `support_bundle_YYYYMMDD_HHMMSS.zip` inside it.
- **Support-bundle privacy:** geometry matching is case-insensitive (`Geometry` is masked), and secret-key detection now also recognizes compact/camelCase forms such as `apiKey`, `authToken`, and `adminPassword` without weakening ordinary diagnostics fields.
- **Queue diagnostics:** `queue.summary.json` now carries both human-facing `status` and canonical `status_code` plus attempts, while continuing to hash URLs instead of exposing them.
- **`AppSettings` mapping equality:** the dataclass no longer generates a class-only `__eq__`; `MutableMapping`/`Mapping` equality semantics apply, so `AppSettings({...}) == {...}` behaves like a dictionary-compatible settings object.
- **ID3 track indices:** `_write_id3()` normalizes string/legacy indices before `:02d` formatting and before writing `TRCK`, preventing tag-writing failure on values such as `"2"`.
- **Chapter time parsing:** `_split_track()` uses the shared `parse_time_seconds()` for `start`, `end`, and next-track starts, accepting numeric and `HH:MM:SS` forms while keeping canonical integral FFmpeg argv (`10` instead of `10.0`).
- **Audio-info cache concurrency:** ffprobe is no longer executed while holding the global per-instance cache lock. Different source files can be probed concurrently, while a same-source single-flight event preserves the historical guarantee that simultaneous callers launch only one ffprobe.
- **Audioknigi search filtering:** generic query noise (`аудиокнига`, `слушать`, `онлайн`) no longer causes valid server results to be discarded. A full surname/title token plus an abbreviated initial may satisfy queries such as `Лев Толстой` against metadata `Л. Н. Толстой`, without letting a lone first name match every initial.
- **Cloudflare detection:** on HTTP 200, generic text such as `just a moment` inside a book description no longer triggers Playwright fallback. Structural challenge markers remain global; `just a moment` is treated as protection only when it appears in the page `<title>`.
- **Resume-position boundary:** `PlayerPositionStore.saved_seconds()` falls back to the duration already stored in the resume record when the caller does not yet know media duration, so a saved near-end position is correctly treated as completed.
- **CSV export safety:** spreadsheet-sensitive history cells beginning with `=`, `+`, `-`, `@` (including after leading whitespace/control characters) are neutralized with a leading apostrophe before CSV export.
- **Track-table resilience:** malformed legacy/non-numeric `Track.index` values no longer raise inside `QAbstractTableModel.data()`; a safe row-based fallback is used for display/accessibility labels.
- **Keyboard seek disk I/O:** player seek persistence now uses the existing 3.5-second throttle instead of forcing an atomic `player_positions.json` rewrite for every keyboard auto-repeat step. Pause/stop/shutdown continue to persist immediately.
- **Dynamic localization:** `Скачивается N/M` has a runtime-regex translation for German, English, and Ukrainian.

## Reviewed but not changed

- **Bare `AppSettings()` defaults:** the supported loading path is `load_app_settings()` / `AppSettings.from_mapping()`, which normalizes and fills defaults. Making a bare constructor silently inject the entire persistent schema would change object-construction semantics without a demonstrated runtime failure.
- **`audioknigi_qt.py` audit import paths:** `qt_runtime_audit.py` is actually located at package root while accessibility audit is inside `audioknigi.qt`; the differing imports match the repository layout.
- **QApplication ownership in offscreen self-test:** the existing cleanup intentionally avoids manually destroying PySide/Qt singleton C++ objects; changing that solely for hypothetical same-process test reuse risks access violations.
- **`_download_source_with_fallback()` one-based loop:** it checks `pos >= len(urls)` before using `urls[pos]`; with its primary/fallback contract this is intentionally the next candidate and does not produce the reported `IndexError`. `source_name()` already accepts full URLs.
- **`Озвучка {index}` in `runtime_exact.json`:** since Round 10, `ui_text()` deliberately falls back to runtime-exact entries and formats kwargs, so this template is used by the narration selector. The separate `Озвучка N` folder suffix remains intentionally language-stable for filesystem identity.
- **Existing APIC artwork:** preserving an embedded cover when no replacement cover is available avoids destructive metadata loss.
- **Mixin coupling / sequential provider search / media-player cache size:** these are architectural or performance-policy topics, not demonstrated correctness regressions in this audit round; no broad refactor was introduced.
- **Unreachable `playlist_response is None` guard:** retained as a harmless compatibility/source-shape guard required by archived regression tooling.

## Verification

- Focused Round 13 regressions: **12 passed**.
- `pytest -q`: **309 passed**.
- Historical regression audit: **PASS**, 270 historical checks passed with 113 known shape incompatibilities tracked.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`).
- Undefined-global audit: **OK (77 modules)**.
- Unused-import audit: **OK (32 implementation modules)**.
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`; static UI literals, help, onboarding and accessible names complete.
- Full parity audit: **PASS 61/61**.
- Qt import audit: **OK (73 project modules reachable, no legacy frontend path)**.

The real frozen Windows/PySide6/PyInstaller gate still requires the Windows build environment; source/static Linux checks do not replace it.
