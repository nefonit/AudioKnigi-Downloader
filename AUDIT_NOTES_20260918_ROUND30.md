# Audit notes — Round 30 (2026-09-18)

Windows screenshot verification after Round 29 showed that Easy mode correctly displayed grouped search results and their variant count, but selecting a multi-narration result always analyzed `SearchResult.url` — the representative/first recording — without allowing the user to choose among `narration_variants`.

## Fix

- Added an Easy-mode narration row with an accessible `Озвучка` combo box.
- The picker appears only when the selected search result contains more than one unique narration URL.
- Multi-variant results start with `Выберите озвучку…`; no narrator is silently preselected.
- `Выбрать и проанализировать` remains disabled until a narration is selected.
- The combo lists narrator names and existing availability suffixes; unnamed variants fall back to localized `Озвучка {index}`.
- The selected narration URL, rather than the representative first result URL, is passed into analysis.
- `_pending_search_result` is cloned with the chosen URL/narrator so the full `narration_variants` list is still attached to the analyzed Book afterward.
- `Копировать ссылку` uses the chosen narration URL when one has been selected.
- Single-narration results preserve the previous one-click behavior with no extra picker.
- Added Russian/Ukrainian/German/English translations for the new narration-selection UI text.

## Verification

- Round 30 focused regressions: **4 passed**.
- Full pytest suite: **424 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI/help/onboarding/accessibility complete).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.
