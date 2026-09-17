# AudioKnigi Downloader 4.8.5 — full UI/theme/editing audit

## Reported issues

1. Help opened in dark mode with a white top-level surface and dark islands.
2. Ctrl+Z was missing from input fields.
3. Some UI captions could still be squeezed/clipped, especially at large interface scaling.

## Root causes and fixes

- Native `tk.Toplevel` starts with the platform default background. `CTkToplevel` now paints the current application background immediately and repaints on live theme switches.
- `ttk.Entry` does not provide the Text widget's native undo stack. `CTkEntry` now keeps a bounded 100-state edit history and handles Ctrl+Z/Ctrl+Y/Ctrl+Shift+Z through the same single non-recursive physical-key handler used for clipboard shortcuts.
- `CTkTextbox` enables Tk undo/redo and receives the same layout-independent editing shortcuts.
- New menus inherit the active palette through the option database; existing menus are repainted during theme refresh. Tooltips now have separate dark and light palettes.
- M4B preview now uses `CTkToplevel` rather than a raw `tk.Toplevel`.
- The simple dashboard is hosted in a vertical scroll viewport and uses a responsive layout. At constrained width / large scale, the sidebar moves below the main panel instead of squeezing the hero, quality cards, counters and sidebar buttons.

## Theme audit

Checked both `dark` and `light` themes for:

- Simple mode.
- Book tab.
- Search tab.
- Queue tab.
- History tab.
- Settings tab.
- Help window opened after each theme is active.

Result: **0 opposite-theme native Tk surfaces** detected. Entry and Treeview fields resolve to `#252525` in dark mode and `#FFFFFF` in light mode.

## Layout audit

Automated geometry checks were run at 100%, 125%, 150%, 175% and 200% scaling for Simple mode and all five Advanced tabs.

Result after the responsive-layout fix:

- **0 visible horizontal/vertical child overflows**.
- **0 mapped text controls with actual size smaller than requested text size**.

The pre-fix 4.8.4 audit reproduced squeezed Simple-mode labels/buttons at 175–200%; the same audit is clean in 4.8.5.

## Editing audit

Verified:

- Ctrl+C / Ctrl+V / Ctrl+X / Ctrl+A.
- Ctrl+Z undo.
- Ctrl+Y and Ctrl+Shift+Z redo.
- Windows physical virtual-key fallback for Cyrillic keyboard layouts.
- No `<Control-KeyPress>` replacement-event binding was reintroduced, preserving the Python 3.14 recursion fix.

## Automated tests

`pytest` result: **9 passed**, with one pre-existing `PytestCollectionWarning` in `tests/test_range.py` because `TestDownloader` defines `__init__`.
