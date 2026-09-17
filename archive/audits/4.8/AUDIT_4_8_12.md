# Audit 4.8.12

## Findings verified against the uploaded 4.8.11 archive

### False positives
- `actions.py` is not truncated. `_main_download_worker()` is complete, handles `Cancelled` and generic exceptions, and always clears busy state in `finally`.
- `ui_kit.py` is not truncated. The module compiles successfully and `AccessibleLabel._apply_theme_colors()` plus `CTkTextbox._install_edit_shortcuts()` are complete.
- Clipboard scheduling already uses `getattr(self, "_clipboard_offer_after", None)` in 4.8.11.

### Confirmed and fixed
1. **Late native accessibility name refresh** — repeated `AccessibilityManager.register(widget, name=...)` now also calls the Tk 9.1+ native accessibility bridge when the widget was previously auto-registered.
2. **History robustness** — `_add_history()` now accepts a typed model or a `dict`/mapping-style record without direct attribute-only assumptions.
3. **Tray UI blocking** — `TrayManager.hide()` no longer calls `join(timeout=1.5)` on the caller/Tk thread. Native-loop waiting/retry stays in the daemon retirement helper.
4. **`configure({...})` compatibility** — legacy CTk-only options in dictionary-form configuration are normalized before reaching native Tk/ttk controls.
5. **Linux Cyrillic edit shortcuts** — Entry/Textbox edit actions recognize physical X11/XKB keycodes for A/C/V/X/Y/Z, while keeping keysym fallback.
6. **ttk parent surface color** — `_parent_bg()` resolves a ttk widget's active style background, including `Notebook`, before using a fallback.
7. **Dead API parameter** — removed unused `fallback_panel` from `_theme_background`.

## Validation
- `python -m compileall`: passed.
- New 4.8.12 audit tests: **8 passed**.
- Regression group 1 (audit/stability/UI/DnD): **40 passed**.
- Regression group 2 (core/architecture/audio/accessibility): **14 passed**.
- Regression group 3 (remaining UI/threading/timing/search/reliability): **12 passed**, with the pre-existing `PytestCollectionWarning` for `TestDownloader.__init__`.
- Total: **66 passed**.
