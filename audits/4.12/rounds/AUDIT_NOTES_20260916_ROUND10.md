# AudioKnigi Downloader — audit follow-up Round 10 (2026-09-16)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND9_20260916`.

## Confirmed and fixed

- **Knigavuhe legitimate titles:** `_usable_search_title()` no longer rejects a book merely because its title contains `отзыв` or `комментар`. UI action labels remain filtered, and counter-only review/comment links such as `Отзывы (12)` are ignored.
- **Knigavuhe narration availability:** grouped `NarrationVariant` entries now preserve `available=True`, `available=False` for rights-restricted alternatives, or `None` when availability is unknown.
- **Knigavuhe JS argument parsing:** `_extract_call_argument()` now tracks nested parentheses in addition to `{}` and `[]`, so parenthesized/function-call expressions inside `BookController.enter(...)` are not truncated at the first `)`.
- **PoleKnig Playwright fallback metadata:** after a browser fallback, narration discovery runs against the rendered browser DOM instead of the stale/blocked HTML returned by the original `requests` call. The outer `fetch_book()` no longer overwrites those browser-derived variants with stale metadata.
- **PoleKnig cancellation:** `_discover_narration_variants()` now raises `Cancelled` immediately even before title/author-link early-return paths, matching the rest of the provider cancellation contract.
- **DownloadRequest index API:** added public `DownloadRequest.track_index()` and migrated engine/UI callers to it. `_track_index()` remains as a backward-compatible alias for older code/tests.
- **Probe path safety:** `_probe_duration()` now keeps `Path.resolve()` inside the same `OSError` guard as `stat()`, avoiding analysis crashes on inaccessible/broken Windows/UNC paths.
- **Copied/restored Track matching:** `_split_track()` can find a logically identical track by normalized numeric index when object identity changed after refresh/deserialization, while retaining the identity fast path.
- **Legacy/string Track indices:** `BookFlowMixin` normalizes `Track.index` to `int` before comparing it with selected integer indices.
- **Audioknigi narrator parsing:** the fallback narrator regex now stops before comma-separated metadata such as `Исполнитель: Иван Иванов, Жанр: Фантастика` instead of leaking genre text into the narrator field.
- **DownloadWorker deepcopy boundary:** the worker itself now normalizes or removes non-serializable/native `cover_cache` objects before `copy.deepcopy()`, so it is safe even if a caller bypasses the GUI-side snapshot preparation.
- **Narration-selector localization:** fallback labels (`Озвучка N`) and availability suffixes are localized instead of being concatenated in Russian in EN/DE/UK interfaces.
- **Static/runtime localization bridge:** `ui_text()` can fall back to `runtime_exact.json` for exact strings. This removes the need to duplicate static accessibility/tool-tip translations across two catalogs while preserving existing legacy-literal precedence.
- **Search/export localization:** added runtime translations for `Поиск не выполнен: ...`, the empty-history export error, and three additional concatenated visible prefixes discovered by the strengthened audit.
- **Accessibility wording:** the settings save button's accessible name now matches its visible label instead of adding an unexplained `Qt` suffix.
- **Localization audit coverage:** the static audit now recognizes direct `QComboBox.addItem(...)` literals and audits leading literal prefixes in concatenated user-visible status/message calls, while avoiding false positives from technical-log composition.

## Reviewed but not changed

- **Chrome 151–153 User-Agent values:** the audit called these “future/nonexistent”, but the supplied Windows build log from the same date reports Microsoft Edge 153. The project timeline is internally consistent, so no User-Agent rollback was made.
- **`availability="available"` formatting:** no PEP 8 defect exists here; keyword arguments conventionally omit spaces around `=`.
- **Auto-Chunker `runtime_auto_chunk_min_kbps` alias:** retained as a runtime compatibility alias. Persisted settings already migrate to `auto_chunk_min_kbytes_per_sec`; removing the alias would only risk older adapters/tests without fixing a user-visible bug.
- **MediaProcessingMixin subprocess hooks:** the production downloader composition includes the shared subprocess registry. Moving the hooks solely for standalone-mixin purity was not justified by a runtime failure.
- **CDN `source_name()` log wording / provider instantiation:** diagnostic/performance style only; no download correctness issue was demonstrated.
- **Runtime-regex static entries / lowercase quality words:** current quality/status values are already localized by the UI before they reach those dynamic messages. No mixed-language reproduction was established.
- **Queue Base64 covers:** potentially large JSON is a storage/performance tradeoff, not a correctness/data-loss defect in the audited flow; no cache-format migration was introduced here.
- **Player-position writes every four seconds:** retained intentionally for crash-resume durability. Reducing disk writes would trade recovery guarantees for performance and requires a separate policy decision.
- **Local audio-file drag/drop:** current drag/drop contract is for supported website URLs and `.url` shortcuts; opening arbitrary local media is a feature request, not a regression.
- **History row removal:** no stale row-index accessibility metadata is generated by the current implementation, and the transactional in-place delete remains preferable to reloading all cover icons.
- **Playwright self-test requiring Edge:** the compact release intentionally uses the installed Edge channel to avoid bundling a browser. Runtime fallback is useful in development when Playwright Chromium exists, but treating a machine without Edge as release-ready would weaken the compact-build acceptance gate.
- **Acceptance gate constants / manual reader timeout:** maintainability/UX suggestions without a current release correctness failure; left unchanged.

## Verification

- `pytest -q`: **280 passed**.
- Focused Round 10 regressions: **9 passed**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`).
- Undefined-global audit: **OK (77 modules)**.
- Unused-import audit: **OK (32 implementation modules)**.
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`.
- Full parity audit: **PASS 61/61**.
- Qt import audit: **OK (73 project modules reachable, no legacy frontend path)**.
- Historical regression audit: **PASS**, 270 historical checks passed with 113 known shape incompatibilities tracked.

The real Windows/PySide6/PyInstaller frozen self-test still has to run on Windows; Linux source/static verification cannot substitute for that platform-specific gate.
