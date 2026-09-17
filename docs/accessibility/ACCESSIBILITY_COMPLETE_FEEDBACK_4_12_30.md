# AudioKnigi Downloader 4.12.30 — complete screen-reader interaction feedback

This release extends the 4.12.29 Prism/NVDA/JAWS connection fix from focus-only speech to action/state feedback across the UI.

## User-action feedback
- Checkboxes: focus reports current state; Space/click immediately reports `отмечен` / `не отмечен`.
- Radio buttons: changed selection is spoken immediately.
- Comboboxes: selected value is spoken; Tcl implementation names (`PY_VAR...`) are never used as accessible names.
- Sliders: keyboard or mouse changes announce the new value.
- Buttons: when the command does not produce a richer status/dialog/focus change, the app confirms `Действие выполнено`.
- Book-parts Treeview: Space announces the part number and checked state; bulk selection announces the aggregate result and part count.
- Notebooks: current tab name and position are exposed.
- Context menus: active menu item is spoken while navigating with arrow keys.
- UI mode changes: Simple/Advanced mode is announced and focus is moved to a useful control.

## Navigation
- Tab/Shift+Tab skip disabled action controls.
- A global fallback also handles dynamically-created controls that were not present during initial registration.
- Disabled read-only Text is treated differently from disabled actions: it remains reachable so blind users can inspect Help and diagnostics.

## Read-only text
When a disabled Tk Text receives focus, the app exposes it as `только чтение` and provides line reading:
- Up/Down: previous/next line
- PageUp/PageDown: ten lines
- Home/End: first/last line

## Diagnostics
`ACCESSIBILITY CHANGE` lines in `app.log` record semantic state/value feedback sent to the reader. Existing `ACCESSIBILITY STATE`, `ACCESSIBILITY FOCUS`, and Ctrl+Shift+F12 diagnostics remain available.
