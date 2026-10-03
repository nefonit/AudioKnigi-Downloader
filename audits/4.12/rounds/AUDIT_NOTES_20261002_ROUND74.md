# Round 74 — Round 73 audit follow-up

Applied confirmed findings from the 2026-10-02 follow-up review:

- sidecar generation now accepts model or mapping-shaped tracks, uses safe indices, and preserves duration/timeline data without aborting on `index=None`;
- `effective_track_duration` reads either objects or mappings consistently;
- refreshed media playlists filter malformed track/selection indices instead of raising raw `TypeError`/`ValueError`;
- parallel multi-source splitting keeps one aggregate user status instead of competing per-track worker-thread status updates;
- Knigavuhe fallback recovery fetches a missing cover (or preserves the already-cached original cover) before returning the replacement book;
- identity tokenization uses Unicode letter/digit classes consistently, including Ukrainian/Belarusian letters;
- queue deserialization no longer shadows `dataclasses.fields`;
- full-MP3 refresh updates `full_indices`, rewrites the resume manifest, and returns the current request selection after a changed playlist;
- PoleKnig narration availability comparisons are case-insensitive and Knigavuhe current variants carry explicit availability when the page state is known;
- track selection and queue re-analysis use safe index conversion;
- delayed post-analysis queue/download actions verify that the same analyzed `Book` is still current and that shutdown was not requested;
- dropped `.url` files are read with a 64 KiB bound and single-track download rejects malformed indices cleanly;
- Settings output-folder initialization falls back from `None`, Easy-mode download is explicitly disabled with no current book, and German onboarding/remaining direct commands use the Sie form;
- the restart-only badge translations no longer add punctuation absent from the source UI label.

Reviewed and intentionally unchanged:

- Windows support-bundle path redaction remains privacy-first even when a path with spaces can consume trailing diagnostic prose; weakening it can leak part of a user directory name;
- `AppSettings.__setitem__` keeps full normalization for correctness; bulk UI updates already use `replace_all`;
- `SourceAnalysisMixin._service()` allocation is a small architectural/performance concern, not a runtime defect;
- runtime localization already evaluates exact matches, then regex rules, then prefixes, so overlapping prefixes cannot preempt a valid full regex match;
- `Найдено вариантов озвучки: {count}...` is intentionally stored as an exact UI template because `ui_text(..., count=...)` performs lookup before formatting; a regression test covers it;
- duplicate localization catalog rows, provider-private helper imports, the HTML-description regex fallback, and `_split_multi_author_prefix` double parsing remain maintenance/refactor topics rather than release-blocking failures;
- Round 73 fixes for unlimited backup history restore, Windows-safe FFmpeg output replacement, persisted booleans, `.full-source` reuse, `TRCK` removal, exact-before-regex localization, adaptive duplicate-duration tolerance, Unicode search-title validation, Easy URL recognition, single player load announcement, batch queue continuation, missing-media dialog cleanup and stable history column widths remain in place.
