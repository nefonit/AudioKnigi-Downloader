# Audit notes — Round 31 (2026-09-18)

Round 31 addresses two Easy-mode usability requests from Windows testing.

## Changes

- Direct user editing of the Easy input now uses `QLineEdit.textEdited` so a fully cleared query/URL can be distinguished from programmatic text changes.
- When the user manually deletes the entire Easy input and no search, analysis or download thread is active, the UI returns to the same initial state as the visible `Скачать следующую книгу` action.
- Both reset paths now share `_easy_reset_to_initial_state`, clearing selected Book state, search results, narration selection, cover/metadata, download enablement and the advanced shared book presentation consistently.
- Added a dedicated Easy-mode annotation block using a read-only, accessible, word-wrapped `QPlainTextEdit` capped at 120 px height so long descriptions remain readable without making the whole card excessively tall.
- The annotation is populated directly from the already analyzed `Book.description`; no extra network request is introduced.
- The annotation heading/content remain hidden when a provider supplies no description.
- Added RU/UK/DE/EN translations for the new annotation labels.

## Verification

- Round 31 focused regressions: **4 passed**.
- Full pytest suite: **428 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI/help/onboarding/accessibility complete).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.
