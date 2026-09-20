# Round 41 — Wide workspace layout (2026-09-20)

Round 41 applies the data-density layout rule to Advanced mode.

## Layout policy

- Book, Search, Queue and History now use the full Advanced workspace width with the main-window 16 px side margins.
- The global 1500 px maximum width was removed from the Advanced QTabWidget.
- Settings is now a centered form card capped at 1180 px.
- Player remains a centered form card capped at 1180 px.

## Tables

- Search: compact columns 0/4/5/6 use ResizeToContents; Title stretches; Author and Narrator are Interactive with 260/280 px base widths.
- History: Cover/Date/Parts stay compact; Title/Author/Narrator use practical interactive widths; Folder stretches into the remaining desktop space.
- Book chapters: checkbox/index/status/timestamps/duration stay compact, chapter Title stretches, Source remains an interactive 280 px technical column and can still be hidden by the existing setting.
- Dark table zebra colors are now #181a1f / #20242c with #2d333f grid token; visible grid lines remain disabled, so the alternating row bands do the tracking work.

## Window chrome

- Menu bar left padding increased to 10 px and item spacing to 6 px to reduce overlap with top-left FPS/overlay tools.

## Accessibility

- No accessible names, IDs, keyboard shortcuts, Tab order or focus-ring behavior were removed.
- Wider columns reduce visual ellipsis without changing screen-reader cell text.

## Verification

- compileall: PASS.
- Round 40 + Round 41 static UI contracts: PASS (14 tests).
- Architecture/layout tests: PASS (11 tests).
- Undefined-global audit: PASS (79 modules).
- Unused-import audit: PASS (32 implementation modules).
- Qt import audit: PASS.
- Qt localization audit: PASS (ru, uk, de, en).
- Exception audit: PASS (reviewed_broad_exception_passes=107).
- Full parity: PASS 61/61.
- Runtime/Windows visual acceptance remains required on the packaged Windows build because PySide6 is not installed in this container.
