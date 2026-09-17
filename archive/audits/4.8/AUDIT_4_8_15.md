# Audit 4.8.15

## False positives verified

- `ActionsMixin.download_full()` is complete; no `args=(self.current_` truncation exists in the supplied archive.
- `app.py` and `ui_kit.py` compile successfully; `apply_tree_zebra()` and the complete `CTkTextbox` implementation are present.
- Prismatoid is the distribution name, while its Python wheel packages the importable module as `prism`; `from prism import BackendId, Context` remains correct.
- `Track` uses the `index` field, and `_safe_track_index()` already accepts integer-like strings.
- The tray is already disabled on macOS in this native-thread implementation.
- The light-theme `#ffffff` foreground mapping is intentionally retained because the application uses white text on accent/danger/success surfaces; globally remapping white would break contrast on those controls.
- SettingsTab's Destroy cleanup already compares both object identity and Tcl path text, and its autosave timer is cancelled during trace disposal.

## Confirmed fixes

- Context-menu single-part downloads restore the previous runtime output mode after the isolated MP3 operation.
- Completion actions no longer require `easy_result_cover` to exist.
- Paused seek now repositions the pygame decoder and remains paused until Resume.
- M4B/M4A/AAC are handed to the system player rather than the embedded SDL_mixer path.
- First-run M4B switch text is localized in all four shipped languages.
- Unfinished-scan UI application safely tolerates missing/destroyed widgets.
- Root-level nearby-label lookup stops cleanly when there is no grandparent widget.
- `CTkOptionMenu.configure(variable=...)` maps to ttk `textvariable`.
- CustomTkinter-only arguments such as `hover`, `switch_width`, `checkbox_width`, and `activate_scrollbars` are ignored safely by the native compatibility layer.
- `CTkScrollableFrame` exposes `pack_info`, `grid_info`, and `place_info`.
- The recurring 500 ms full descendant scan was removed. Late CTk-compatible children notify the nearest scrollable ancestor at creation time, preserving dynamic wheel/focus binding without permanent polling.
- macOS small mouse/trackpad deltas are accumulated before a Tk scroll unit is emitted.
- macOS Command-modified keypresses no longer create ordinary Entry undo snapshots before the Command-specific handler runs.
- `CTkSwitch` now supports `select`, `deselect`, and `toggle`; `CTkProgressBar` supports `get`; `CTkTabview` supports safe `delete`.
- `set_button_active()` remembers and restores the original inactive ttk style.
- Tooltip owners hide tips on `Unmap`, and delayed show checks `winfo_exists()`/`winfo_ismapped()` without adding a risky `<Destroy>` callback.

## Validation

- `python -m compileall -q .`: passed.
- New 4.8.15 audit tests: 15 passed.
- Full regression suite under Xvfb/Tk: 104 passed, 1 pre-existing pytest collection warning (`TestDownloader` has `__init__`).
