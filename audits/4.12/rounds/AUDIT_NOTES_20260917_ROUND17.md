# Audit notes — Round 17 (2026-09-17)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND16_20260917`

## Confirmed and fixed

1. **CHANGELOG structure/date**
   - Updated the `4.12.42` release date from `2026-09-15` to `2026-09-17`.
   - Moved the Round 8 Windows build-hardening notes from the end of the file back into the `4.12.42` block, between Round 9 and Round 7.

2. **`migrate_ui_scale_settings()` Mapping compatibility**
   - `core.py` now accepts any `collections.abc.Mapping`, including `AppSettings`, instead of discarding non-`dict` mappings.
   - Unknown/user/plugin keys are preserved through the one-time scale migration.

3. **`DownloadRequest.track_index()` raw string bug**
   - The audit suspected mixed raw/object argument handling.
   - Direct executable testing found a more specific bug: on a raw string such as `"04"`, `getattr(value, "index", value)` returned the built-in `str.index` method.
   - `track_index()` now explicitly handles `int`, `str`, mappings with an `index` key, and Track-like objects.

4. **Malformed runtime regex catalog safety**
   - `i18n.py` now filters malformed rows from `runtime_regex.json` instead of indexing arbitrary list items during module import.
   - A damaged external localization row can no longer crash the whole application at import time.

5. **No-source search localization**
   - `SearchService` now returns the existing catalog literal `Выберите хотя бы один сайт для поиска.` so the error localizes consistently in RU/UK/DE/EN.

6. **Formatting hygiene**
   - Split the multiple import line in `crash_report.py`.
   - Normalized the two local Knigavuhe assignments to `availability = "available"`.

## Reviewed but not changed

- **Microsoft Edge Playwright self-test** remains intentionally Edge-specific for the compact Windows release build. It is not a generic Linux CI gate.
- **`playlist_response is None`** remains as compatibility scaffolding for archived/mocked regression shapes; ordinary `requests` does not return `None`.
- **`template_values(..., language=...)`** keeps its unused language parameter for API compatibility and stable language-neutral filesystem names.
- **Support-bundle queue top-level list** matches the current `QueueStore.save()` format. Non-list data is intentionally ignored fail-safe.
- **`.assembling` / `.segments.json` behavior**, settings scale clamping, and PTS/DTS probe fallback were reviewed and are already correct.
- One archived regression literally requires the old no-space source text `availability="available"`. The PEP8 cleanup therefore adds one known historical source-shape incompatibility; runtime behavior is unchanged.

## Regression coverage

New file: `tests/integration/test_report_followup_round17_20260917.py`

Focused tests: **6/6 passed**.

Coverage includes:
- Mapping/AppSettings scale migration,
- raw integer/string/mapping/Track index handling,
- malformed runtime-regex rows,
- localized zero-provider search error,
- reported formatting hygiene,
- changelog Round 8 placement and release date.

## Final verification

- `pytest`: **342 passed, 0 failed**
- Historical regression: **PASS — 269 passed, 114 known source-shape incompatibilities**
- Exception audit: **PASS — 111 reviewed broad-exception passes**
- Undefined globals: **OK — 77 modules**
- Unused imports: **OK — 32 implementation modules**
- Qt localization: **OK — RU/UK/DE/EN, help topics complete**
- Full parity: **PASS — 61/61**
- Qt import audit: **OK — 73 project modules reachable**
- `compileall`: PASS

Windows/PySide6/PyInstaller frozen execution is not available in this Linux environment; no Windows build success is claimed here.
