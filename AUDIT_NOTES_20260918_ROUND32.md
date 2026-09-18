# Audit notes — Round 32 (2026-09-18)

Round 32 validates the pasted cross-module audit against the current Round 31 source and fixes confirmed defects without mechanically applying false positives.

## Confirmed and fixed

- Support-bundle settings now sanitize `pathlib.Path` values as paths rather than allowing `json.dumps(default=str)` to expose them.
- Segmented-download cancellation now tears down active registered network I/O from a `finally` block if worker threads remain alive.
- Adjacent duplicate `want_mp3 and mp3_needs_creation` guards were consolidated.
- ID3 chapter-title extraction accepts Mapping-style tracks as well as typed Track objects.
- Empty `{Track_Title}` now falls back to a stable unique `track-NN` token, preventing collisions/overwrites for `{Track_Title}.mp3` without producing duplicated names such as `01 - 01.mp3` when `{Track_Number}` is also present.
- `core.load_json()` reads `utf-8-sig`, preserving settings/history JSON saved with a Windows UTF-8 BOM.
- audioknigi.com.ua metadata and analysis fast paths decode raw response bytes as UTF-8/UTF-8-SIG consistently.
- Queue selected-index parsing rejects booleans explicitly so JSON `true`/`false` cannot become tracks 1/0.
- Book-analysis Knigavuhe fallback now derives clean title/author/narrator identity hints before searching.
- Advanced Settings honors persisted `quality_preset` before legacy audio/normalization heuristics.
- Audiobookshelf Library ID accessible name is localized.
- German Help Center grammar corrected (`die Download-Engine ... dieselbe`).
- Player mixin state fields are initialized in the main window.
- Context-menu Delete restores editor focus for Windows UIA/screen-reader continuity.
- Track-player enablement is recalculated after analysis/download model refresh instead of being unconditionally disabled.
- Added missing translations for final search status, fallback-source status, analysis error/cancel summaries and history/queue column labels.
- German narration terminology now consistently uses `Sprecherfassung` and Du-form `Wähle`; English Range setting wording is now `Range min. file size:`.
- Prefix fallback wording for skipped unavailable parts is aligned with the regex translation.
- Runtime-exact annotation entries were normalized to the conventional `de`, `en`, `uk` order.

## Reviewed and intentionally unchanged

- `Cancelled` inherits directly from `Exception`, not `RuntimeError`, so the stream-copy `except RuntimeError` cannot swallow cancellation in the current source.
- `core.save_json(..., raise_errors=True)` is valid; `raise_errors=False` is part of the current signature.
- Queue model serialization is valid: Track/NarrationVariant derive from `MappingDataclass`, which provides `to_dict()`.
- Runtime localization already evaluates regex patterns before prefixes, so the reported prefix-shadowing architecture bug is not present.
- Broad literal duplication across localization catalogs is maintenance debt, not a runtime regression; it was not mass-refactored in this bug-fix round.
- BookFlowMixin host hooks remain part of the downloader facade contract; replacing required methods with silent no-ops would risk hiding persistence/history failures.

## Verification

- Round 32 focused regressions: **15 passed**.
- Full pytest suite: **443 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI/help/onboarding/accessibility complete).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=266`, `known_shape_incompatibilities=117`, `resolved=0`).
- `compileall`: **PASS**.
- One archived expectation that deliberately required the unsafe book-title fallback for empty track titles is recorded as a known historical incompatibility.
