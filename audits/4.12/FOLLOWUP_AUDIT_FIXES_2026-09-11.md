# Follow-up audit fixes — 2026-09-11

This pass was applied to the already hardened Phase 39 Qt-only tree from 2026-09-10.
The supplied audit was verified against the actual source before changes were made.

## Confirmed and fixed

- `BandwidthLimiter.consume()` now works when no cancellation event is supplied; it sleeps normally instead of dereferencing `None`.
- Relative cover URLs are resolved against the book URL in both downloader parsing and `BookAnalysisService`; cover fetching also defensively canonicalizes against the referer.
- Resume segment discovery/cleanup escapes glob metacharacters, including `[` and `]` in book names.
- `_measure_loudnorm(..., filter_complex=...)` now appends a real loudnorm analysis node and maps its output.
- Schema.org/JSON-LD book titles now take precedence over the fallback page/player title, matching the meaning of `fallback_title`.
- Duplicate preflight accepts books whose every track exists and none is damaged even when online duration metadata was unavailable; sidecar/history identity checks still gate an exact duplicate.
- Full-MP3 transcoding now respects `runtime_delete_source` instead of always deleting the downloaded temporary source.
- FFmpeg polling checks cancellation with `is_set()` instead of adding a redundant 10 ms wait after every 250 ms `communicate()` timeout.
- Download-history de-duplication uses normalized supported URLs and normalized absolute filesystem paths.
- Knigavuhe search-page metadata parsing preserves the raw title long enough to extract author and narrator, while removing only the `(слушать аудиокнигу ...)` marker.
- Knigavuhe descriptions are parsed structurally, so nested `<div>` markup is not truncated and meta attribute order no longer matters.
- Knigavuhe narration-variant collection is activated only from structural headings/named containers, not arbitrary annotation text.
- Cloudflare bootstrap TLS failures now close the raw socket before re-raising.
- PoleKnig canonical book URLs accept supported scheme-less links through the shared URL normalizer.
- PoleKnig PlayerJS parsing normalizes JavaScript `true`/`false`/`null` before `ast.literal_eval` fallback.
- PoleKnig person matching is token-order independent (`Александр Пушкин` == `Пушкин Александр`).
- Removed the unused `original` loop variable from the PoleKnig hydrated-search filter.
- Template fallback `{Author}` is localized using the runtime UI language.
- `SettingsSyncMixin` computes the quality preset before optional widgets are checked, removing the `UnboundLocalError` path.
- Player seek state is initialized explicitly and read defensively for keyboard navigation.
- The player chapter-unavailable placeholder is localized.
- Text-editor context-menu deletion now uses a text-specific translation (`Delete` / `Löschen`) without changing queue `Remove` / `Entfernen` semantics.
- Windows multimedia-key de-duplication now suppresses the same physical command only when it arrives through different Windows message paths; two fast presses through the same path are preserved.
- Missing-media dialog text and accessibility keyboard help are fully localized; the Full-MP3 information title is explicitly localized.
- Removed the redundant double translation of the Easy-mode normalization quality item.

## Already fixed / audit item not applicable

- Track status `нет` is already context-separated: `TrackModel` maps it through `нет (файл)`, while boolean `нет` remains `no/nein/ні`.
- `start_full_mp3()` information messages already pass through `_show_message()`, which runtime-localizes title and text. It was still made explicit for consistency.
- Queue cover bytes are already serialized through Base64 and validated on restore.

## Deliberately not changed

- `_first_json_ld` is a naming/style issue only; changing the private helper provides no behavioral gain in this pass.
- The last compact PoleKnig chapter cannot obtain an `end`/`duration` from timestamp markers alone because there is no following marker. End-to-end analysis already probes missing remote durations; inventing a duration in the parser would be incorrect.
- Knigavuhe `_query_matches_metadata` is retained for compatibility/tests even though production ranking no longer applies that strict filter.
- The `QMediaPlayer.setSource(); play()` observation is timing-dependent and was not reproducible from the source-level test environment. Replacing it with status-driven replay without a failing case risks duplicate playback.
- Cross-process merging of `player_positions.json` needs a real inter-process locking contract to eliminate write races completely. The current in-process `RLock` remains unchanged rather than adding a partial lock that could imply stronger guarantees than it provides.

## Verification

- `python -m pytest -q`: **306 passed**.
- `PYTHONPATH=. python tools/full_parity_audit.py`: **FULL PARITY: PASS 61/61**.
- `PYTHONPATH=. python tools/qt_import_audit.py`: **QT IMPORT AUDIT: OK (46 project modules reachable, no legacy frontend path)**.
- `python tools/qt_localization_audit.py`: **OK** for `ru`, `uk`, `de`, `en`.
- `qt_frozen_module_audit.py` requires a PyInstaller `.toc` argument and therefore is not a standalone source-tree check.
