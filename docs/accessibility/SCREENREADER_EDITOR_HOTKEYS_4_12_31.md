# Screen-reader editor, keyboard-layout and search-focus hardening — 4.12.31

## Reported behavior

1. NVDA/JAWS could focus the Simple-mode field **Название, автор или ссылка**, but the standard `Insert+Up` / say-current-line gesture could fail to report the typed value on Windows Tk 8.6.
2. Global Ctrl+letter shortcuts depended on Tk keysyms and could stop matching under Russian/Ukrainian layouts.
3. Search results were keyboard-focused after a successful search, but the focus move itself was not explicitly announced.

## Implementation

### Windows UI Automation

`audioknigi.accessibility.enable_windows_uia()` enables `tk-uia` on Windows before child controls are created. Prismatoid remains the application announcement bridge; `tk-uia` supplies the Windows UI Automation control/value layer for native Tk/ttk widgets.

The universal editor now has an explicit accessible name/description. The accessibility manager also synchronizes semantic names with the UIA provider when Tk 9.1 native accessibility is unavailable.

A Prism-backed `announce_focused_editable_text()` remains as a best-effort fallback when an `Insert+Up` gesture is passed through to Tk.

### Keyboard-layout independent global shortcuts

Global Ctrl+letter commands use Windows virtual-key codes as a fallback, so the physical command remains stable regardless of whether the active layout produces Latin, Russian or Ukrainian keysyms. Latin-layout Tk bindings remain the primary path and are not executed twice.

Covered commands:

- `Ctrl+L` — focus the book/title/link editor;
- `Ctrl+D` — download/current workflow action;
- `Ctrl+F` — Search;
- `Ctrl+Q` — Queue;
- `Ctrl+H` — History.

Entry editing shortcuts `Ctrl+C/V/X/A/Z/Y` already use the same layout-independent Windows virtual-key strategy in `ui_kit.py`. Numeric/function/navigation shortcuts are inherently layout-independent.

### Search result focus

After successful search result rendering, focus moves to the appropriate results Treeview (Simple or Advanced Search), the first row is selected when necessary, and NVDA/JAWS receives an explicit announcement that focus moved to the table plus the result count and arrow-key hint.

## Frozen Windows build protection

`requirements.txt` and `pyproject.toml` require `tk-uia>=0.8.0,<0.9` on Windows. PyInstaller explicitly collects `tk_uia` and copies `tk-uia` distribution metadata. The mandatory `--accessibility-import-selftest` verifies `tk-uia` inside the finished Windows EXE in addition to Prism/CFFI.

## Validation

Automated regression coverage is in `tests/test_screenreader_editor_layout_focus_41231.py`. The complete active project suite after this change is **470/470 passed** in the available Linux/Xvfb validation environment.

A real Windows NVDA/JAWS smoke test remains required for final release acceptance because Linux/Xvfb cannot exercise Windows UI Automation or the actual reader gesture interception path.
