# Audit 4 follow-up fixes — 2026-09-11

This pass was applied to the Phase 39 Qt-only source after the previous AUDIT3 fixes.

## Fixed

- Refused unsafe chapter-index remapping when switching from audioknigi.com.ua to a provider with a different chapter layout. Full-book fallback still switches automatically; partial selections require re-analysis/reselection on the fallback source.
- Added the primary `source_path` input to the `filter_complex` loudnorm measurement pass.
- Relaxed duration verification with a bounded proportional tolerance (5–15 seconds) to avoid rejecting healthy files solely because remote chapter metadata is slightly rounded.
- Completed safe default host hooks/attributes for `DownloaderMixin` so focused/headless hosts do not fail only because UI/history hooks are absent.
- Added `download_mode` to resume manifests and made Full MP3 recovery preserve and restart Full MP3 mode.
- Replaced fragile `.part`/`.assembling` suffix construction with name-appending semantics.
- Ensured a still-running `ffprobe` process is killed/collected on exceptional exit.
- Made fallback-source logging name the actual alternative source.
- Switched crash-report branding to `brand.DISPLAY_NAME` and removed the unused `os` import.
- Knigavuhe: recognize `book_description`, neutral structural headings for narration variants, and en-dash metadata separators.
- PoleKnig: support author slugs, close/relax meta-attribute regexes safely, and normalize JS `true`/`false`/`null` only outside quoted strings.
- UI scaling: keep the base font in a Python attribute so repeated scaling cannot compound if Qt dynamic-property round-tripping is unreliable.
- Player seek persistence: save the requested target explicitly rather than immediately rereading asynchronous `QMediaPlayer.position()`.
- Settings button: accept Qt's `clicked(bool)` argument.
- Shutdown: include the Audiobookshelf worker thread in interruption and exit waiting.
- Book-analysis recovery: parse track end values defensively instead of calling `float()` on arbitrary persisted input.
- Queue restore: normalize stale textual `Скачивается` entries to `interrupted`/`Незавершено`.
- Added runtime localization for the short-audioknigi-source fallback status.
- Audiobookshelf: surface self-signed/untrusted TLS failures as an explicit actionable error without silently disabling certificate verification.
- Event sounds: defer first playback until the new Qt media source reaches a playable status; cached players still play immediately.
- Reduced `qt/main_window.py` back below the repository architecture threshold: 3997 lines.

## Reviewed but intentionally not changed

- Chrome User-Agent 153/152/151: the audit's assertion that these are future versions is outdated for 2026-09-11. Chrome 153 entered Stable on 2026-09-08 and Chrome 154 entered Early Stable on 2026-09-09, so the existing set is realistic for the current date.
- The `нет` localization-key collision does not break the track table in this source: `track_model.py` maps local status `нет` through the context-specific `нет (файл)` key.
- `_query_matches_metadata` is retained because the repository's compatibility/regression tests import it directly even though production search no longer uses it as a strict filter.
- Queue drag-and-drop target-half behavior is a UX nuance, not a demonstrated corruption bug; no semantic change was made without a failing interaction contract.
- The audit note about files physically named `text/x-python` does not apply to the archive: the modules have their normal package filenames.

## Regression coverage added

`tests/test_audit4_followup_20260911.py` adds focused coverage for fallback selection safety, Full MP3 resume mode, loudnorm inputs, duration tolerance, headless mixin defaults, Knigavuhe/PoleKnig parser cases, defensive analysis/queue restore, dynamic localization, seek persistence, Qt settings/shutdown/base-font/event-sound source contracts, Audiobookshelf TLS handling, and crash-report branding.

## Validation

- `python -m pytest -q`: 321 passed
- Full Parity Audit: PASS 61/61
- Qt Localization Audit: OK for ru/uk/de/en
- Qt Import Audit: OK, 46 project modules reachable and no legacy frontend path
- `python -m compileall -q audioknigi tests`: PASS
