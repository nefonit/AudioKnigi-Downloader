# Round 39 — Production UI polish (2026-09-19)

Round 39 is intentionally visual-only: it does not change search, analysis, download, queue or player business logic.

## Production design pass

- Introduced one cohesive theme vocabulary for system/light/dark modes: window, surface, elevated surface, border, text, muted text, accent, destructive and focus colors.
- Polished menu bar, popup menus, status bar, tooltips, buttons, inputs, progress bars, group boxes, cards, tables, lists, headers, tabs and scrollbars.
- Kept the Round 38 amber keyboard focus ring stronger than all decorative borders.
- Added named top-level header elements (`appHeader`, `appBrand`, `appSubtitle`) so the product header is styled consistently instead of relying on an inline stylesheet.
- Increased spacing inside the Easy-mode card and selected-book card, slightly enlarged the cover and annotation viewport, and raised the main search/download control heights.
- Removed visible table grids and enabled per-pixel vertical scrolling for Easy results and the main Advanced tables.
- Widened the Player card and chapter list for a less cramped desktop presentation.
- Preserved existing accessible identifiers, Tab order, focus styling and screen-reader metadata.

## Verification

- `compileall`: PASS.
- Round 39 source-contract tests: PASS.
- Undefined-global audit: PASS.
- Unused-import audit: PASS.
- Qt localization/import audits: PASS where available without importing PySide6.
- Visual Windows acceptance remains required because the build container used for this round does not provide PySide6/Windows rendering.
