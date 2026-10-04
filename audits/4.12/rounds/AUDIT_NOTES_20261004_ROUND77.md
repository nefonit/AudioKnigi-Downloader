# Round 77 — external audit follow-up

Applied confirmed findings from the 2026-10-04 review:

- hardened the remaining `book_flow.py` track-index conversions used for source mapping and repair-source `MissingMediaSourceError` reporting;
- allowed queries made entirely of one-letter tokens/initials to match token boundaries and person-name initials without reverting to loose substring matching;
- completed queue deserialization migration from private `__dataclass_fields__` to public `dataclasses.fields()` for `Book` as well as `Track` and `NarrationVariant`;
- made Audiobookshelf JSON-error handling safe when `requests.exceptions.JSONDecodeError` is absent in older Requests versions;
- rejected boolean model indices in template track-number conversion;
- made `display_track_timeline()` honor mapping-backed tracks consistently with `effective_track_duration()`;
- reject explicit non-image HTTP responses in `cover_fetch.py` before caching/tagging cover bytes;
- install localized context menus on `QTextEdit` as well as `QLineEdit` and `QPlainTextEdit`;
- aligned Ukrainian narration terminology with `озвучення`, English `Select all` sentence case, and German `Buchs` wording.

Reviewed and intentionally unchanged:

- support-bundle Windows file paths are redacted by the file-specific pass first; `C:\\App\\test.mp3 finished with error code 500` preserves `finished with error code 500`. Directory-like paths intentionally remain privacy-first and may over-redact ambiguous prose;
- `BookFlowMixin`/`MediaProcessingMixin`/`ProbeMixin` coupling is an intentional composition contract of the download facade, not a standalone mixin API;
- segmented retry waiting, probe-pool cancellation, worker cover-cache normalization, queue drag coordinates, player stop persistence, seek-write throttling, clipboard file-unload handling, delayed search rendering, and graceful close timeout were reviewed as correct;
- `runtime_exact.json` contains only one `Проверить системный звук` key in Round 76; the reported skipped-parts prefix/regex conflict is not a runtime conflict because `localize_runtime_text()` deterministically checks anchored regex rules before prefix fallbacks, and an existing regression test intentionally requires the prefix as a fallback contract;
- overlap between legacy and runtime locale catalogs remains a compatibility concern rather than a runtime defect; removing entries is deferred to a dedicated localization-catalog migration;
- the repeated `_split_multi_author_prefix()` call is low-cost and preserves existing `author_inferred` semantics, so it is not changed in this hardening round;
- `parts` versus `selected` download-mode terminology is normalized at queue boundaries; replacing it with shared enums would be a broader model migration;
- `browse.clicked.connect(self._choose_output_dir)` is safe because `_choose_output_dir(self, _checked=False, *, target=None)` explicitly consumes Qt's `checked` argument;
- `Едуард Саратовцев` is the creator-selected canonical spelling already protected by Round 68 regression tests.
