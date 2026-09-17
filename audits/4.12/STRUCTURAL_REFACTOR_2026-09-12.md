# Structural refactor — 2026-09-12

This refactor implements the nine agreed quality improvements and reorganizes the repository by responsibility while preserving compatibility facades and historical evidence.

## 1. Main window decomposition — complete

`audioknigi/qt/main_window.py` is now the composition/common-state layer. Behavior moved to focused mixins under `audioknigi/qt/mixins/`: accessibility/menu, clipboard, analysis/download, search, queue, history, settings, and lifecycle. Player behavior remains in its dedicated player mixin and page construction in `main_window_pages.py`.

## 2. Downloader decomposition — complete

The old monolithic downloader was split into `audioknigi/download/` modules for probing, source analysis/recovery, HTTP/range/resume, media/FFmpeg processing, and book flow. `audioknigi/downloader.py` remains a small compatibility facade so existing imports and the download engine keep a stable public surface.

## 3. Localization catalogs and stable IDs — complete, migration-compatible

Locale data moved from the large Python dictionary into external JSON catalogs under `audioknigi/locales/`. `message()` / `tr()` are the preferred stable-ID APIs for new code. `ui_text()` remains a compatibility bridge for existing Russian source literals so the migration can be incremental rather than a risky all-at-once rewrite. Locale JSON is included in both setuptools package data and the PyInstaller build.

## 4. Versioned settings schema — complete

`audioknigi/config/settings.py` owns defaults, normalization and migrations. The schema is versioned. The misleading historical `auto_chunk_min_kbps` key migrates to `auto_chunk_min_kbytes_per_sec` while preserving the established KB/s behavior and unknown keys for forward/plugin compatibility.

## 5. Common source-provider contract — complete

`audioknigi/providers/` defines `SourceProvider`, adapters and a registry for audioknigi.com.ua, knigavuhe.org and poleknig.com. Search and book fetch operations now use the provider contract, while provider-specific parsing remains isolated in the source modules.

## 6. Tests and historical material — complete

Active tests are organized as `tests/unit/`, `tests/integration/`, `tests/architecture/`, plus deterministic `tests/fixtures/providers/`. Historical phase/audit suites are under `archive/tests/`. `tools/historical_regression_audit.py` temporarily executes the archived suite from the correct repository root and fails on any new regression among historically passing tests; source-shape assertions tied to retired monoliths are explicitly allow-listed.

Historical source variants, old branch audits and migration-only tools live under `archive/history/`, `archive/audits/` and `archive/tools/` respectively.

## 7. Diagnostic support bundle — complete

`audioknigi/diagnostics/` creates a bounded support ZIP available from Help → Diagnostics. It contains version/dependency facts, redacted settings, log tails and non-content queue status. API keys, cookies, passwords, audiobook media, book titles, raw configured URLs and identifying full executable/app-data paths are excluded or redacted.

## 8. Silent-exception review gate — complete

Existing best-effort cleanup paths using bare `except Exception: pass` were reviewed and recorded in `tools/exception_allowlist.json`. `tools/exception_audit.py` fails if a new unreviewed silent catch appears. This preserves intentional cleanup resilience without allowing silent exception swallowing to grow unnoticed.

## 9. Release/developer hardening extras — complete

- Runtime version consumers use `audioknigi/metadata.py` backed by the single source `audioknigi/version.py`.
- `requirements-release.txt` provides an exact-version release baseline.
- Provider HTML/PlayerJS fixtures protect parser behavior without live-site dependency.
- The old KB/s settings key is migrated to a precise name.
- CI runs active tests plus parity, localization, Qt import, exception and historical-regression gates.

## Repository placement rules

The canonical rules are in `docs/architecture/PROJECT_STRUCTURE.md`. Root is reserved for launch/build/package metadata and primary documents. Production modules, active tests, current audit evidence, current technical documentation and historical artifacts each have dedicated trees.

## Compatibility strategy

Compatibility facades are retained where external imports are likely (`audioknigi.downloader`, legacy literal translation). Historical tests are kept as evidence and a behavioral safety net, but they no longer determine current module boundaries.

## Verification before source packaging

- Active pytest: 48 passed.
- Full parity: 61/61.
- Localization audit: RU/UK/DE/EN complete.
- Exception audit: 116 reviewed silent cleanup catches; no unreviewed additions.
- Historical compatibility gate: 277 archived regressions still pass; 104 known source-shape incompatibilities are allow-listed and any new failure is fatal.
- Qt import-boundary audit: 71 project modules reachable, no legacy frontend path.
- `compileall`: pass.
- Setuptools wheel smoke build: pass; all six locale JSON catalogs present in the wheel.

The current execution environment does not have PySide6 installed, so live Qt/NVDA/JAWS GUI runtime tests are not claimed here. The Windows build/acceptance pipeline remains the release gate for those checks.
