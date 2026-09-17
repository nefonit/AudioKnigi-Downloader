# 4.12.23 — Reported-Issues Audit & Hardening

This audit was performed against the actual 4.12.22 source archive, not pasted fragments.

## Confirmed and fixed

1. **Brand hard-code in accessibility** — confirmed as an architecture inconsistency. `APP_TITLE` now aliases `brand.DISPLAY_NAME`, and the screen-reader ready announcement uses `DISPLAY_NAME`.
2. **`DragDropMixin` docstring placement** — confirmed. The string was a no-op class expression after `_dnd_easy_mode`; it is now the class docstring.
3. **JSON reader/writer synchronization** — `save_json()` was already atomic (`temp + os.replace`) and serialized by `_JSON_LOCK`; `load_json()` now takes the same re-entrant lock for consistent in-process read/write ordering.
4. **Dead `output_mode = "mp3"` in `_estimate_required_space`** — removed.
5. **Redundant playlist JSON slash replacement** — removed from the `json.loads()` path. Escaped JSON slashes are parsed natively by Python.
6. **Auto-Chunker only downshifted permanently** — improved. Parked workers remain available and the controller can scale concurrency back up after sustained throughput recovery.
7. **`_logical_y()` hierarchy fragility** — parent traversal remains the normal path, with a root-coordinate fallback when Tk cannot resolve an intermediate parent path.
8. **DPI-responsive squeeze found during broad regression** — not part of the original report, but confirmed by an existing test. Simple-mode reflow now uses DPI-scaled natural panel widths, and the advanced parts header reserves the bulk-toggle button width before laying out its descriptive label.

## Checked and not current bugs

- **`bootstyle` passed to `CTkButton`**: not a CustomTkinter call. `ui_kit.CTkButton` is a project class derived from `ttk.Button`; it pops `bootstyle` and maps it to project/ttkbootstrap styles.
- **Missing `customtkinter` dependency**: intentional. Since 4.8 the runtime tree is native Tk/ttk. Historical `CTk*` names are compatibility APIs only; `HAS_CUSTOMTKINTER` is deliberately `False`.
- **`prismatoid` merged with Python/source markers**: not present in the archive. `requirements.txt` contains a valid PEP 508 environment marker and `audioknigi/__init__.py` is normal Python.
- **`search_tab.py` truncated string / SyntaxError**: false for the archive. `compileall` succeeds and the file ends with complete strings/statements.
- **DnD mixin requires attributes that may be missing**: `_dnd_easy_mode()` uses `getattr` and stable defaults, including support for lightweight test hosts.
- **Tray `<Unmap>` hides on workspace changes**: tray hiding is delayed and requires the main application widget itself to report `state() == "iconic"`, plus an active queue and enabled tray setting.
- **Treeview zebra code is incomplete**: `apply_tree_zebra()` calls `tag_configure`, and history/search/queue/book rows assign `row-even` / `row-odd` tags on insertion.
- **Linux edit hotkeys rely only on Cyrillic keysym names**: no. Logical Latin/Cyrillic keysyms are tried first and physical X11 keycodes are a fallback.
- **`ensure_app_string_var()` unexpectedly crashes background workers**: all current call sites are UI-construction paths. Failure after both root and fallback Tk masters reject `StringVar` means the UI interpreter is not usable; explicit failure is safer than returning a broken placeholder.
- **Compatibility aliases can diverge**: `select_all_tracks_btn` and `player_pause_btn` are aliases to the exact same widget objects, not separate controls/state.
- **Broad `except Exception: pass` means every error is hidden**: the codebase still uses best-effort suppression heavily around widget teardown, optional OS integration, accessibility probes and cleanup. This is intentionally separate from operational failures, which are routed to `app.log` / `BOOK FLOW` / global Tk-thread handlers. The 4.12.14 exception audit remains the baseline for this policy; bare `except:` remains forbidden.

## Validation

- Full Python compilation (`compileall`) passes.
- The complete pytest collection is executed in four Xvfb-safe groups; final release result: 376/376 tests passed.
- Focused 4.12.23 regression tests cover each confirmed fix.
- Existing keyboard, UX, shutdown, FFmpeg, media refresh, source mapping, duplicate/cancel, event-bus and reliability regressions are rerun before release.
- Windows EXE build remains pinned to CPython 3.14.7 x64. Source tests in this environment are not represented as a Windows EXE run.
