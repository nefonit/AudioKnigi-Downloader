# V27 — Separate Help Center rendering from Qt event handlers

`audioknigi/qt/help_content.py` continues to own the unchanged 16 topics and
additional details in each of four languages.

`audioknigi/qt/help_formatter.py` owns the original
`_format_help_body_html(title, body)` renderer, including HTML escaping,
shortcut-to-`<kbd>` highlighting, list/paragraph handling, and exact CSS.

`audioknigi/qt/help_actions.py` resolves the selected row and appends the
language-specific supplemental details (exactly as the old dialog did).
Both new modules are Qt-independent. The GUI in `qt/help_center.py` owns the
actual Qt widgets, focus placement, accessibility names and stable identifiers,
and the `_show_row` / `_copy_report` event handlers.

The old `help_center._format_help_body_html` import continues to refer to
the same renderer, preserving callers and earlier monkeypatching conventions.

## Validation

- Tests compare HTML output and shortcut behavior with stable expectations,
  including escaping, lists, and multilingual shortcuts.
- Tests verify topic resolution and invalid-row behavior without Qt.
- Existing Qt accessibility tests continue to check dialog controls, focus,
  splitter, copy-report callback and runtime wiring.
- No help copy, CSS, keyboard shortcuts, search, download, queue or player logic
  has been modified. Archived tests are kept intact, with the normal
  historical regression gate required before merging.
