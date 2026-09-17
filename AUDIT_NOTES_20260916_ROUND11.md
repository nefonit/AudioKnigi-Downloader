# AudioKnigi Downloader — audit follow-up Round 11 (2026-09-16)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND10_20260916`.

## Confirmed and fixed

- **Peer Range retries after a fatal peer error:** `_download_segmented()` now creates a shared peer-abort event. The first root failure sets it immediately, and sibling `_download_segment()` loops stop before retry/backoff instead of opening fresh Range requests after the coordinator has already decided to abort. User cancellation remains a separate `Cancelled` contract.
- **Skip-one-part source preservation:** the second-404/410 `skip` path no longer calls the broad `_clear_stale_source_downloads()` cleanup. Fresh source files already downloaded for unaffected tracks stay reusable. Full source cleanup remains tied to actual playlist refresh/replacement.
- **Parallel FFmpeg split failure:** both parallel split pools now cancel still-pending futures when one split raises, so queued unrelated work does not start after the operation is already doomed. Already-running FFmpeg work is allowed to unwind normally.
- **Malformed unfinished-download manifests:** `scan_unfinished()` safely normalizes scalar/non-iterable `selected_indices` instead of iterating an integer and crashing. Boolean payloads are treated as malformed rather than as track index `0/1`.
- **Playlist chapter HTML entities:** audioknigi.com.ua playlist titles now run through `html.unescape()` after string extraction, so `&quot;Глава 1&quot;` and `&amp;` do not leak into filenames/ID3 titles. Empty/null titles still retain the numeric fallback.
- **JSON-LD parsing order:** JSON-LD blocks are now parsed as JSON *before* HTML-entity decoding. String values are recursively unescaped only after parsing, avoiding syntax corruption when a JSON string contains `&quot;`.
- **Windows `.url` drag/drop path safety:** `Path.is_file()` now sits inside the `OSError`/`ValueError` guard, so malformed Windows path syntax cannot crash drag/drop before shortcut decoding starts.
- **Help/UI terminology:** German quality help now says `Fürs Smartphone`, and search help in RU/EN/DE/UK uses the same full visible action labels as the actual UI.

## Reviewed but not changed

- **Mixin cross-calls (`ProbeMixin` / `BookFlowMixin` / `SourceAnalysisMixin`):** these mixins are implementation pieces of the composed downloader facade, not supported standalone services. Refactoring pure helpers into a new base/common layer would be architectural cleanup, not a demonstrated production `AttributeError`; no invasive hierarchy rewrite was made in this audit round.
- **`_download_source_with_fallback()` 1-based `pos`:** the current indexing is guarded by `if pos >= len(urls): raise` before `urls[pos]`. With one or two URLs (the function contract) it does not index past the list; empty primary URLs are skipped safely.
- **Auto-Chunker compatibility alias:** persisted settings already use `auto_chunk_min_kbytes_per_sec`; the old `runtime_auto_chunk_min_kbps` attribute remains a runtime compatibility fallback. Only the misleading comment was corrected.
- **Duplicate localization entries / static regex entries:** these are maintainability/performance observations without a reproduced wrong translation in the current resolver ordering. Removing keys across catalogs was not mixed into a runtime-hardening round.
- **`requests.Response is None` defensive check:** logically unreachable for Requests, but retained as a harmless historical compatibility guard. Earlier archived tests explicitly assert this shape.
- **Queue Track serialization:** current `Track`/`Book` models inherit `MappingDataclass` and provide safe `to_dict()` serialization, so the reported loss of all tracks is not present.
- **Player-position cache after backup restore:** the Qt restore flow already suspends persistence, restores the files, reloads the player position store, reloads history/queue/settings, then resumes persistence.
- **Settings combo accessible names:** `add_combo()` receives `label` *after* `self._l(...)` localization; stripping the colon therefore leaves a localized label, not a Russian source literal. `configure_accessible()` leaves an already localized value unchanged.
- **Native media-key registration / hidden compatibility controls / local-audio drag-drop:** no new runtime defect was established beyond previously documented design tradeoffs; no behavior change was made.

## Verification

- Focused Round 11 regressions: **8 passed**.
- `pytest -q`: **288 passed**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`).
- Historical regression audit: **PASS**, 270 historical checks passed with 113 known shape incompatibilities tracked.
- Undefined-global audit: **OK (77 modules)**.
- Unused-import audit: **OK (32 implementation modules)**.
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`; static UI literals, help, onboarding and accessible names complete.
- Full parity audit: **PASS 61/61**.
- Qt import audit: **OK (73 project modules reachable, no legacy frontend path)**.
- `compileall` completed successfully.

The true Windows/PySide6/PyInstaller frozen executable gate still requires the Windows build environment; source/static Linux checks cannot replace it.
