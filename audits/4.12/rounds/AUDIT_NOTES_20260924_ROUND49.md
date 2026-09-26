# Round 49 audit notes — 2026-09-24

Round 49 reviews the external post-Round-48 audit and applies only findings that match the current source tree. The base is the supplied Round 48 archive, so the Advanced-layout repair remains intact.

## Confirmed fixes

- **Support-bundle path privacy:** configured Windows drive/UNC paths stored as ordinary strings are now treated as configured paths before generic log sanitization. A value such as `D:\Audio Books\My Collection` is fully replaced with `<configured-path>` instead of risking a partially exposed final component.
- **Queue diagnostics:** support bundles now derive the opaque queue ID from both legacy top-level `url` and the current `request.book.url` schema. The summarizer also accepts a future/versioned `{"items": [...]}` / `{"queue": [...]}` wrapper without exposing titles or raw URLs.
- **Direct AppSettings normalization:** `AppSettings({...})` now canonicalizes numeric strings, range-limits and boolean spellings at construction time while preserving unknown/plugin keys. Direct construction intentionally does not persist the one-time UI-scale migration marker or falsely mark a partial in-memory mapping as an already-used profile; persisted/legacy loading still goes through the normal migration path.
- **Knigavuhe fallback narrator identity:** downloader-side recovery no longer immediately accepts the first fetched candidate whose narrator is missing when the source narrator is known. It keeps that candidate as a last resort and continues looking for an explicit narrator match, mirroring `BookAnalysisService`. Unknown-source-narrator ambiguity is handled conservatively as well.
- **Player resume NaN guard:** resume edge calculations now use `safe_float`, so `NaN`/non-finite duration metadata cannot propagate into position comparisons.
- **Smart Format diagnostics:** the copy-path message no longer claims a lower-bitrate MP3 is “no worse” than a higher target profile. It explains that lossy up-bitrate transcoding would not improve quality and the source stream is therefore preserved.
- **Provider typing:** `KnigavuheProvider.enrich_search_results` now matches the provider contract with `Iterable[SearchResult] -> list[SearchResult]` annotations.
- **Easy-mode minimum geometry:** the Easy card minimum is reduced from 860 px to 820 px so its 80 px of combined outer/layout margins fit the window's declared 900 px minimum instead of forcing an implicit ~940 px minimum.

## Reviewed and intentionally unchanged

- Empty folder/track templates are not a supported “no folder/no name” mode in the current UI/runtime: Settings, request deserialization and template rendering deliberately fall back to the canonical defaults. The audit recommendation was conditional on empties being supported, so no semantic change was made.
- The reported multi-file `remote_size` overestimation scenario is not produced by the current analyzer: `BookAnalysisService` fetches `remote_size` only when `len(unique_files) == 1`. Multi-file books keep `remote_size == 0` and use duration-based estimation. No speculative reinterpretation of externally supplied aggregate sizes was added.
- The narration-count localization placeholder is already called as `_l("Найдено вариантов озвучки: {count}. Выберите чтеца.", count=count)`, so exact-template lookup plus named formatting works as intended.
- Duplicate locale literals, punctuation consistency and JSON key order are maintenance/style concerns rather than runtime defects and are unchanged in this patch.
- `_audioknigi_description_from_html` and related underscore helpers are not dead code: `BookAnalysisService` imports and uses them. Moving them into a new shared parser module is an architectural refactor, not a correctness patch.
- Python 3.8 compatibility findings do not apply: `pyproject.toml` declares Python >= 3.11, so `ThreadPoolExecutor.shutdown(cancel_futures=True)` is within the supported runtime.
- Localization data is bundled at `audioknigi/locales`, matching `i18n.py`'s package-relative lookup; no frozen-path fallback was required.
- `QueueItem` remains a legacy compatibility model, filename length limiting remains intentional Windows path protection, hidden compatibility actions remain technical debt, and the global QApplication language property remains a Qt-model design choice. None was changed without a demonstrated runtime failure.
- Batch-analysis errors already publish an assertive visible status before suppressing the modal dialog, so the report's “no visual notification” claim does not match the current code.

## Regression coverage

Round 49 adds focused tests for:

- a Windows configured path containing spaces;
- current nested queue URL hashing and a versioned queue wrapper;
- downloader fallback continuing past an unknown narrator to an exact match;
- finite resume guards for `float("nan")`;
- Smart Format log semantics;
- direct `AppSettings` type/range normalization;
- the 900 px Easy-mode minimum geometry contract.

## Verification

- Full pytest suite: **612 passed, 0 failed**.
- Round 49 focused regressions: **8 passed**.
- Historical regression audit: **PASS** (`passed=255`, `known_shape_incompatibilities=128`, `resolved=0`).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **OK** (75 project modules reachable, no legacy frontend path).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity audit: **PASS 61/61**.
- `compileall`: **PASS**.
