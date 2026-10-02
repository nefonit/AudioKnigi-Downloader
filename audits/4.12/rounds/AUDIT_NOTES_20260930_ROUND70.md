# Round 70 — Round 69 audit follow-up

Applied confirmed findings from the 2026-09-30 review:

- multi-source disk preflight scales whole-book `remote_size` to the selected/missing share while preserving full-size budgeting for one shared physical source;
- stable `_source*.mp3` assignment moved to `download.common.source_target_assignments`, removing `ProbeMixin`'s hidden dependency on `BookFlowMixin` while keeping a compatibility wrapper;
- when retained sources are enabled, a freshly downloaded `_repair_...` source atomically replaces the stale canonical `_source*.mp3`, preventing the next run from reusing the damaged source;
- a `non_increasing_middle_boundary` playlist defect no longer triggers the short-source Knigavuhe fallback intended for physically truncated shared audio;
- Playwright playlist reuse ignores non-2xx `.pl.txt` responses, allowing the authenticated HTTP fallback to run instead of parsing a 403/503/404 HTML body as JSON;
- Playwright navigation timeouts for AudioKnigi and PoleKnig were reduced from 60 to 30 seconds to bound cancellation latency;
- `PlayerPositionStore.reload()` now serializes with `_persist_latest()` using the same `_persist_lock -> _lock` order;
- full-MP3 mode normalizes the request/result to all track indices and duplicate preflight tolerates a file-system race around `stat()`;
- the built-in player discovers `cover.webp`, `folder.webp`, and `front.webp`;
- the circular search progress widget skips painting below 16 px, avoiding invalid negative `QRectF` sizes;
- Advanced Search text no longer overwrites the analyzed Book URL; the Easy universal field remains the bridge between modes;
- `AppSettings.replace_all()` performs batch replacement in one normalization pass and Settings Save uses it while preserving object identity;
- History Clear is blocked during an active long operation, matching backup/restore safety;
- Queue and History cover icons use explicit scale-aware icon/row sizes;
- missing runtime translations were added for refreshed-playlist decisions, damaged-file recreation, Auto-Chunker/Range diagnostics, source fallback, and MP3 compatibility fallback.

Reviewed and intentionally unchanged:

- Windows-path support-bundle over-redaction remains privacy-first by design;
- direct `AppSettings({...})` construction intentionally treats a partial mapping as current in-memory intent and keeps `first_run_complete=False` unless explicitly supplied;
- global `safe_int(bool)` semantics remain unchanged because index consumers explicitly reject booleans and changing the generic helper could affect unrelated callers;
- `author_inferred` is present on `SearchResult` with a default, so there is no `unexpected keyword` failure; after detail-page hydration it is not used by grouping/ranking;
- `source_health_service` and the main requests session both intentionally use `trust_env=False`;
- provider adapters / `BookAnalysisService` coupling and provider-specific `fetch_remote_size` behavior are architectural follow-ups, not current runtime regressions;
- `_LOCALE_DIR = Path(__file__).with_name("locales")` matches the PyInstaller destination `audioknigi\locales;audioknigi\locales`, so frozen locale lookup is correct;
- duplicate legacy/runtime translation entries and broader German Du/Sie wording are maintenance/editorial cleanup rather than release-blocking defects.
