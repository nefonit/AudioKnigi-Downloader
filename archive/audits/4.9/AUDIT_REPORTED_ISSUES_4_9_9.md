# Audit of reported issues — 4.9.9

This audit was performed against the complete uploaded 4.9.8 archive, not truncated `[source: ...]` excerpts.

## Fixed

1. **AudioKnigi reader text leaking `Жанр:`**
   - Reproduced from the real UI screenshot.
   - `extract_extended_metadata_from_html()` used a broad fallback capture after `Исполнитель:`.
   - The capture now stops at the next metadata label (`Жанр`, `Серия`, `Добавлено`, `Автор`, etc.) or markup boundary.
   - Example: `Исполнитель: Зборовский Алекс, Жанр: Фантастика` -> `Зборовский Алекс`.

2. **Opening a missing downloaded/history folder recreated an empty folder**
   - `_open_path()` no longer creates directories by default.
   - A missing historical/book folder shows `Папка не найдена` and is left missing.
   - The configured output root is still created on demand by `open_output_folder()`.

3. **Search narration cache mutation**
   - Search-cached `NarrationVariant` objects are cloned before attachment to an analyzed `Book`.
   - Updating `current`, reader/title fallback data, or selector state no longer mutates reusable search-cache objects.

4. **Stale saved window position after monitor removal**
   - Added `safe_window_geometry()`.
   - Saved/restored geometry is validated against Tk's current virtual desktop.
   - Legitimate negative/snap coordinates that still overlap a live monitor are preserved; truly off-screen coordinates are clamped.

5. **Legacy string widths such as `150px`**
   - `_pixel_width_to_chars()` accepts the `px` suffix.
   - Malformed width strings now fall back to native automatic width (`0`) instead of being forwarded to Tcl.

## Reported critical issues that do not reproduce

- `player.py` is not truncated at `# SDL_`; the complete module compiles.
- `ui_kit.py::_display_columns()` is complete and returns `widest`; the module compiles.
- `settings_tab.py` is complete; the module compiles.
- The project does not use CustomTkinter runtime widgets. `HAS_CUSTOMTKINTER = False` intentionally; the historical `CTk*` names are native Tk/ttk compatibility wrappers.

## Other reviewed reports

- `listen_last_completed_book()` compares the `updated` string, but the writer always stores `%Y-%m-%d %H:%M:%S`; lexicographic ordering is chronological for this fixed format.
- Rights-restricted Knigavuhe books intentionally have no tracks. Analysis and button-state code checks `restricted` and prevents downloading the blocked recording while still exposing legal alternative narrations when present.
- First-run output mode changes are tied to the user's explicit M4B choice in the wizard; this is expected onboarding behavior.
- `CTkTextbox._text_paste()` already reads the clipboard **before** deleting the selection, so clipboard failure does not destroy selected text.
- `_parent_bg()` uses a lightweight `ttk.Style` wrapper; no correctness issue or measurable repaint regression was reproduced.
- SettingsTab uses `ensure_app_string_var()` for rebuild-sensitive variables and the application initializes the remaining UI state before constructing tabs.

## Verification

- New targeted tests: 8/8 passed.
- Full suite: **214 passed**.
- `python -m compileall audioknigi`: OK.
- `python audioknigi_gui.py --ci-selftest`: **CI SELFTEST: OK (4.9.9)**.
