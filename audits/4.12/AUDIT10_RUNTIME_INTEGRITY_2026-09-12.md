# 4.12.33 runtime-integrity follow-up — 2026-09-12

## Scope

Follow-up review after the structural refactor, focused on release metadata, split-module runtime safety, provider/service boundaries, localization ordering, diagnostics, and recovery compatibility.

## Confirmed fixes

- Restored missing globals/imports in `qt/track_model.py`, `qt/mixins/lifecycle.py`, `qt/mixins/history.py`, and `network_dns.py`.
- Added `tools/undefined_global_audit.py` and wired it into CI/release quality gates.
- Made `DownloadRequest.selected_indices=None` fail with the intended validation error and made preflight/result construction defensive.
- Preserved zero-based unfinished track indices, rejected malformed explicit URL ports safely, and made `MappingDataclass.__doc__` real.
- Disk-space estimation no longer creates book folders; support-bundle dependency versions have a frozen-runtime fallback.
- Settings migration now normalizes `normalization_mode`; `%APPDATA%` falls back safely when the variable is empty.
- Reordered runtime-regex rules, completed Ukrainian legacy literals, removed shadowed runtime prefixes, corrected Ukrainian wording, and refreshed Search help text.
- `search_all_sources()` now uses the provider registry. Audioknigi search/hydration moved to `providers/audioknigi_search.py`; the compatibility API remains re-exported by `services.search_service`.
- Downloader source analysis delegates PlayerJS/Cloudflare analysis to `BookAnalysisService`; only compatibility hooks and downloader-specific fallback selection remain in the mixin.
- Qt selftests force offscreen only while they own `QApplication`, emit Playwright success/failure text, and expose the current runtime stage while retaining `QT_MIGRATION_STAGE=phase-39` for historical acceptance schemas.
- README/architecture docs now explicitly describe `download_engine.py`; CHANGELOG hierarchy/orphan historical notes were repaired.

## Audit claims intentionally not applied

- Python 3.14.7, Chrome 153, PySide6 6.11.2, requests 2.32.5, Playwright 1.62.0, Pillow 12.3.0 and PyInstaller 6.22.2 are real 2026 releases; downgrading them to 2025-era versions would be incorrect.
- `runtime_exact.json` is intentionally keyed by source text then language, matching `localize_runtime_text()`. It is not a language-first catalog.
- The retained `language=` parameter in path-template helpers is an API-compatibility parameter; filesystem identity is intentionally language-neutral.

## Verification

Pre-packaging verification on the hardened 4.12.33 tree:

- Active pytest suite: 81 passed.
- Full parity audit: 61/61 passed.
- Localization audit: OK for ru/uk/de/en.
- Qt import audit: 72 project modules reachable; no legacy frontend path.
- Reviewed silent-exception audit: 113 approved cleanup/fallback cases.
- Unused-import audit: OK across 18 refactored implementation modules.
- Undefined-global audit: OK across 76 Python package modules.
- Historical regression gate: 275 historical tests still pass with no new regressions.
- `compileall`: OK.
- Wheel build (`--no-deps --no-build-isolation`): OK; all six JSON localization catalogs and the refactored provider/source-analysis modules are packaged.

The distributable ZIP is re-extracted and re-tested separately before release; final archive results and SHA-256 are recorded in the release response.
