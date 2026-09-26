# Round 51 full Easy/Advanced search synchronization — 2026-09-24

Round 51 is based on the supplied Round 50 archive and addresses the remaining mismatch reported after searching in Easy mode: the Easy results table was visible while switching to Advanced mode left the user on the Book tab even though the Advanced Search table already shared the same model.

## Confirmed fixes

- **One canonical search-result presentation state:** `_search_results_active` now controls both the Easy table/actions and the Advanced search-results stack. Search completion activates both presentations; a new search, reset, error/no-results outcome, or choosing a result deactivates the shared selection stage.
- **Mode switch routing:** switching from Easy to Advanced while pending search results are active now opens the Advanced **Search** tab automatically instead of leaving the user on **Book**. Switching back to Easy restores the Easy results table.
- **Shared selection:** Easy and Advanced table selections mirror the same row with a recursion guard. Keyboard focus can move between modes without changing which book is selected.
- **Complete query-field synchronization:** `easy_input`, `book_url_edit`, and the dedicated Advanced `search_edit` now mirror the same query/URL text.
- **Post-selection behavior preserved:** once a search result is chosen, the shared search-selection presentation is closed before analysis starts, so later mode switches return to the book workflow instead of stale search results.

## Regression coverage

Round 51 adds focused source contracts for shared result visibility, Advanced Search-tab routing on mode switch, mirrored selected rows, three-way query-field synchronization, and ending the search-selection stage before analysis. The Round 50 input-sync contract was updated to reflect the dedicated Advanced Search field.

## Verification

- Full pytest suite: **622 passed, 0 failed**.
- Round 50/51 synchronization regressions: **10 passed**.
- Historical regression audit: **PASS** (`passed=255`, `known_shape_incompatibilities=128`, `resolved=0`).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **OK** (75 project modules reachable, no legacy frontend path).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity audit: **PASS 61/61**.
- `compileall`: **PASS**.
