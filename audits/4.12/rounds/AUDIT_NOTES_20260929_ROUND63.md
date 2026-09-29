# Round 63 — Round 62 audit follow-up

Applied confirmed findings from the 2026-09-29 review:

- fixed a real privacy regression introduced in Round 62: absolute paths inside the user profile are now fully collapsed to `<configured-path>` when a configured path is sanitized, even after `%USERPROFILE%` / `~` masking;
- normalized `AppSettings.__setitem__` through the same schema boundary used at construction/save time, preventing transient string booleans, numeric strings and invalid ranges from leaking into live runtime state;
- bounded AudioKnigi detail-page hydration to the 30 highest-ranked search results while preserving all parsed result cards;
- removed the unreachable `return False` after `unlink_with_retry`.

Reviewed and intentionally unchanged:

- an empty `folder_template` is not an operational “save directly in output_dir” mode in the current architecture; the UI, settings normalization and `render_folder` all deliberately fall back to `{Book_Title}`;
- `QT_QUEUE_FILE` is correctly owned by `services.queue_service`;
- `ProbeMixin` / `BookFlowMixin` and `SourceAnalysisMixin` / `ProbeMixin` coupling is part of the composed download-engine design;
- selected-chapter disk preflight remains deliberately conservative when only whole-book remote size is known;
- `runtime_exact.json` no longer contains the reported duplicate `Проверить системный звук` key;
- runtime regex localization is evaluated before prefix localization, so the reported prefix-shadowing conflict does not occur;
- Audioknigi description helpers are used by `BookAnalysisService`;
- the `services` package keeps a deliberately narrow public facade;
- `audioknigi.config.settings` is the correct import path;
- Python 3.8 `cancel_futures` compatibility remains outside the Python 3.11+ project contract.
