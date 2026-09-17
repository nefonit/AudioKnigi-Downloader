# AudioKnigi Downloader 4.8.4 — UI / Python 3.14 audit

## Reported issues

1. Python 3.14.3 could crash in Tkinter with `RecursionError` after the 4.8.3 clipboard-key changes.
2. Some captions and neighbouring controls were still squeezed or clipped.
3. Switching from dark to light theme left several native Tk surfaces dark.

## Fixes

- Replaced overlapping Ctrl key bindings with one physical-key handler and direct Entry editing operations.
- Preserved Windows Ctrl+A/C/V/X support across Latin, Russian and Ukrainian keyboard layouts by using layout-independent virtual key codes.
- Removed the callback path that could recursively re-enter Tk event handling and added a recursion-safe UI exception fallback.
- Corrected legacy pixel-to-character width conversion for both large and small CustomTkinter widths.
- Allowed ttk buttons to request enough width for their actual caption instead of inheriting obsolete pixel widths as character counts.
- Re-created native style fonts after `tk scaling` changes and increased minimum window widths for 150–200% scales when the monitor allows it.
- Reordered the header pack allocation so the Simple/Advanced mode buttons cannot be squeezed by the application title.
- Added complete light/dark recoloring for native Tk containers, labels, text areas and canvases, in addition to ttk controls/tables/scrollbars.

## Verification

- Full test run: `6 passed`; one pre-existing Pytest collection warning remains in `tests/test_range.py`.
- Launch smoke test: application remained in `mainloop` for the full test interval with no traceback.
- Theme smoke test: `dark -> light -> dark`; no legacy dark backgrounds remained in the light pass.
- Interface sizing audit exercised Simple mode and all Advanced tabs at 100%, 125%, 150%, 175% and 200% UI scale.
- Clipboard regression test covers Ctrl+C/Ctrl+V/Ctrl+X/Ctrl+A physical Windows key codes.
