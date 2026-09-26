# Round 43 — Parser/query/runtime hardening follow-up (2026-09-20)

Round 43 reviews the external audit report after Round 42 and applies only confirmed fixes. Architectural notes and intentionally preserved contracts were reviewed separately instead of being changed mechanically.

## Confirmed fixes

- Knigavuhe relevance matching now handles initials symmetrically and independent of token order: `Л. Толстой` matches `Лев Толстой`, and the reverse form matches too. A lone one-letter query still cannot make a result relevant by itself.
- Knigavuhe fallback MP3 extraction now checks the parsed URL path, so technical `/0.mp3` entries are excluded even when the CDN appends query parameters.
- PoleKnig JS literal normalization treats backtick template literals as quoted strings, preventing `true` / `false` / `null` text inside a template literal from being rewritten.
- Settings boolean parsing now honors the supplied default for `None` and empty-string values; a bare `AppSettings()` now contains the documented defaults.
- Range capability probing accepts optional whitespace around the `/` in `Content-Range`.
- Download planning rejects selected tracks with a missing source URL before creating bogus download jobs, and normalizes incidental surrounding URL whitespace.
- Removed two confirmed dead-code remnants: `cookies_provided` in browser-session persistence and the unused `BookFlowMixin._is_transient_error` helper.
- Probe-side book identity parsing now accepts ASCII hyphen, en dash and em dash consistently with `BookAnalysisService`.
- Audioknigi author merging now recognizes full-name/initial variants such as `А. Пушкин` and `Александр Пушкин`, prefers the fuller spelling, and still keeps distinct initials such as `А. Иванов` / `Б. Иванов` separate.
- Audioknigi narrator fallback now stops before additional metadata fields such as duration, year, size and quality instead of swallowing them into the narrator value.

## Reviewed and intentionally unchanged

- `NarrationVariant.available` and `SearchResult.availability` represent different layers (boolean variant availability vs source/search status). The explicit boundary conversion remains intentional; no enum migration was introduced in a patch round.
- `{Output_Dir}` remains deliberately relative inside folder templates; the download base directory is already supplied separately. This behavior is protected by the existing Round 34 contract.
- `history_changed` is not a GUI-thread violation in the Qt path: the download worker callback emits a Qt signal, which is forwarded to the main-window relay with `QueuedConnection`.
- The Cloudflare bootstrap path already applies an explicit 4-second socket timeout per address. The report's claimed 20–30 second OS timeout per IPv6 attempt is therefore not representative of this implementation; no speculative address-family filtering was added.
- A non-existing `Path` object cannot preserve whether its original textual spelling ended with a directory separator. String destinations with a trailing separator are already supported; changing ambiguous `Path("new_logs")` semantics would break existing file-name behavior.
- `BookController.enter(...)` remains strict JSON with the existing direct-MP3 fallback. No permissive JavaScript-object parser was added without a real failing page sample because that would broaden executable-syntax acceptance significantly.
- Parallel single-source splitting already performs stream-copy fallback inside `_split_track`; the outer pool cancels peers only when a split still raises after its own fallback. The reported cancellation race therefore does not match the current control flow.
- The duplicate replace-with-retry helpers remain separated by architecture layer; importing downloader helpers into `core.py` would invert the current dependency direction for a negligible gain.
- Localization dictionary duplication/order and support-bundle regex compilation are maintenance/performance nits, not runtime defects, and were left untouched in this functional hardening round.
- Multi-file remote-size prefetch remains intentionally disabled to avoid dozens of network probes before download starts.
- Easy-mode stale-input download disabling and best-effort global media-key registration remain intentional safety/platform behavior.

## Verification

- Round 43 focused regressions: **10 passed**.
- Full pytest suite: **547 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=256`, `known_shape_incompatibilities=127`, `resolved=0`).
- Full parity: **PASS 61/61**.
- Qt import audit: **OK** (75 project modules reachable, no legacy frontend path).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.
