# Round 48 audit notes — 2026-09-23

Round 48 is a focused Advanced-mode layout repair based on the supplied Round 47 source archive. The target is the Book tab, especially the geometry transition after a successful book analysis.

## Confirmed layout failures

- `_analysis_finished()` called `track_table.resizeColumnsToContents()` after the model was populated. That one-shot resize overrode the deliberate header policy and allowed long raw source URLs to widen the table after analysis.
- The Advanced book synopsis used an unconstrained word-wrapped `QLabel`, so long descriptions could consume most of the vertical workspace and squeeze the chapters table.
- Narration variants used the combo box's content-derived size hint, allowing long narrator names to influence the whole tab width.
- Analysis/download progress widgets and result-only controls occupied layout space even when their operation/state was inactive.
- Book cover, synopsis, summary and narration controls were stacked as separate vertical sections, amplifying the layout jump when analysis completed.

## Fixes

- Removed the post-analysis `resizeColumnsToContents()` call. The table now keeps its persistent policy: compact metadata columns use `ResizeToContents`, chapter title uses `Stretch`, and source stays an `Interactive` 280 px column with horizontal pixel scrolling available when needed.
- Converted the Advanced synopsis to a read-only `QTextEdit` with a bounded height and keyboard-friendly scrolling. The metadata summary is also height-bounded and exposes its complete value through the tooltip/accessibility text.
- Grouped cover, metadata, synopsis and narration into the existing styled `bookCard`, reducing vertical reflow after analysis.
- Configured the narration combo with `AdjustToMinimumContentsLengthWithIcon`, so a very long reader name no longer determines window width.
- Result-only track controls and the track table are hidden until analysis actually produces tracks.
- Inline analysis progress and the download activity card only consume layout space while the relevant operation is active; completion continues to be announced through the status/accessibility path.
- Explicitly made the track table horizontally scrollable and width-flexible instead of allowing its contents to dictate the page minimum width.

## Verification

- Added focused Round 48 source-contract regressions for post-analysis geometry, bounded description, narration sizing, result-state visibility, and progress-state visibility.
- Full `pytest -q`: **604 passed**.
- Focused Round 48 + relevant prior UI contracts: **27 passed**.
- Historical regression audit: **PASS — 255 passed / 128 known shape incompatibilities**.
- Qt localization: **PASS — ru/uk/de/en**.
- Qt import audit: **PASS — 75 project modules**.
- Exception audit: **PASS — 107 reviewed broad exception passes**.
- Undefined-global audit: **PASS — 79 modules**.
- Unused-import audit: **PASS — 32 implementation modules**.
- Full parity: **PASS — 61/61**.
- `compileall`: **PASS**.
- PySide6 is not installed in the Linux audit container, so final visual geometry must still be accepted on the Windows Qt build.
