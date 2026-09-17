# Accessibility — one universal interface

AudioKnigi Downloader does **not** have a separate screen-reader mode. The same interface is designed for sighted mouse users, keyboard users, NVDA users and JAWS users.

## Design rules

- Interactive controls are native `tk`/`ttk` widgets: buttons, edit fields, checkboxes, radio buttons, combo boxes, sliders, progress bars, notebooks and trees.
- Runtime UI uses native `tk`/`ttk` widgets for both visual containers and interactive controls. CustomTkinter is no longer a runtime dependency.
- `ttkbootstrap` themes the native ttk controls; it does not require a second accessibility mode or Canvas-only action controls.
- Every action is keyboard reachable; native controls keep their standard Enter/Space/arrow-key behavior.
- Quality cards contain real radio buttons instead of a canvas-only click target.
- Important fields have visible text labels; tables and player controls have semantic names for the screen-reader bridge.
- Placeholder/examples are persistent helper text and semantic descriptions; they are never inserted as fake Entry values.
- The long Settings page scrolls automatically when Tab/Shift+Tab moves focus to an off-screen native control.
- Dynamic statuses are announced without a user toggle. Progress is throttled to 10% milestones to avoid excessive speech.
- No application speech is produced for ordinary users. The direct-output bridge activates only when NVDA or JAWS is actually available.

## NVDA / JAWS integration

On Windows the app lazily uses `prismatoid` and asks only for the NVDA and JAWS backends. It intentionally never falls back to generic SAPI/TTS. If neither reader is running, the bridge stays silent.

When a supported reader is active, the app can announce:

- focused buttons, fields, radio buttons, checkboxes and controls;
- checked/selected state;
- selected table row and row position;
- selected tab;
- important download/processing status;
- progress at 10% milestones.

The bridge is re-detected periodically, so starting NVDA/JAWS after AudioKnigi Downloader does not require a restart.

## Future Tk accessibility API

Official CPython 3.14 Windows binaries currently bundle Tcl/Tk 8.6. Tk 9.1 adds the `tk accessible` API. AudioKnigi Downloader probes for that API at runtime and, when it exists, automatically registers accessible objects/names and emits selection-change events. No setting or alternate UI is required.

## Keyboard shortcuts

- `Ctrl+Z` — undo the last edit in the focused text field.
- `Ctrl+Y` / `Ctrl+Shift+Z` — redo an undone edit.
- `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `Ctrl+A` — standard editing shortcuts (including Russian/Ukrainian Windows layouts).
- `Ctrl+L` — focus the book URL.
- `Ctrl+D` — download the current book.
- `Ctrl+F` — Search tab.
- `Ctrl+Q` — Queue tab.
- `Ctrl+H` — History tab.
- `Alt+1`, `Alt+2`, `Alt+3` — select the three friendly quality presets.
- `F1` — Help.
- `Esc` — cancel the current operation.
- `Tab` / `Shift+Tab` — move through controls.
- `Space` / `Enter` — native activation according to control type.
- Arrow keys — native radio/combo/slider/tree/notebook navigation where applicable.

## Testing policy

Automated tests verify the native-control contract, absence of any screen-reader-mode toggle, automatic NVDA/JAWS backend selection, no generic TTS fallback, progress throttling, widget descriptions, keyboard UI smoke tests, WCAG-AA core color contrast, text-named buttons, Treeview density/zebra styling and the full download/audio regression suite.

Automated tests cannot replace a real acceptance pass with installed JAWS and NVDA on Windows. Before a public accessibility claim/release, the packaged EXE should be tested end-to-end with both readers using keyboard only.
