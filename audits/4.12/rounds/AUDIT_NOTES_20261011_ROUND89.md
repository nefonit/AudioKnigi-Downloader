# AudioKnigi Downloader 4.12.42 — Round 89 audit follow-up

Date: 2026-10-11

## Confirmed fixes

- Added EN/DE/UK runtime localization for low-disk-space errors, Auto-Chunker premature-stop, segmented merge failure, missing audio URL, repeated Range retries, incomplete/stalled segments, selected parts disappearing after playlist refresh, and the FFmpeg failure prefix.
- Added non-empty localized accessible descriptions for the first-run wizard Cancel and Save/Start buttons.
- Added a regression proving `MutableMapping.get()` correctly returns its supplied default after legacy `AppSettings` alias targets are deleted; no runtime settings change was needed for that reported finding.
- Marked one archived regression as an intentional historical incompatibility because it required the now-obsolete empty onboarding button descriptions.

## Reviewed findings kept unchanged

- `SourceAnalysisMixin` helper dependencies are satisfied by the documented `DownloaderMixin` MRO (`ProbeMixin` precedes `SourceAnalysisMixin`); this is an architectural coupling, not a current runtime failure.
- Parallel split teardown deliberately waits for already-running workers after cancelling their FFmpeg children; returning while those workers still touch book files would be less safe.
- Privacy path redaction remains intentionally conservative.
- `_cached_probe_audio_info` keeps a stable local cache key and its reported pop/finally path is correct.
- Legacy `Book` construction is safe because `Book.tracks` has `default_factory=list`.
- Queue `selected_indices=[]` and unfinished-manifest `[]` intentionally have different compatibility semantics: explicit empty queue selection means none, while legacy resume `[]` means whole book.
- The 500-row history load/save behavior is retained as the current UI retention contract; changing history retention is a separate product decision.
- Frozen builds explicitly package `audioknigi/locales` beside `i18n.py`, so the current locale path is valid.
- Proxy half-close timeout, event-sound cache size, and support-bundle over-redaction observations are tuning recommendations, not confirmed defects.

## Regression baseline

- 957 tests collected.
- 955 runnable tests pass.
- 2 Qt accessibility self-tests remain environment-blocked because PySide6 is unavailable in the validation environment.
- Integration suite: 914 collected cases.
- Historical regression audit: PASS (`passed=251`, `known_shape_incompatibilities=132`, `resolved=0`).
