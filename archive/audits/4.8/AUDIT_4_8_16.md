# Audit 4.8.16

## False-positive findings verified against the shipped 4.8.15 archive

- `audioknigi/actions.py` is complete; `_full_worker()` does not end at `TIT2(encoding=` and the module compiles.
- `AudioKnigiApp.t()` is defined in `app.py`; `ActionsMixin` intentionally relies on the host application for localization.
- `audioknigi/ui_kit.py` is complete; `CTkTextbox`, `_install_edit_shortcuts()` and `apply_tree_zebra()` are present.
- Prismatoid is the distribution name, while the Python wheel exposes the `prism` package; `from prism import BackendId, Context` remains correct.
- `_show_completion_actions()` already guards optional easy-mode cover widgets.
- `context_download_part()` already restores the previous runtime output mode in a `finally` block.
- `_player_select_current()` exists in `PlayerMixin`.
- Queue worker status/progress calls are thread-safe because `ActionsMixin.set_status/set_stage/set_progress` marshal their Tk work through `self.ui(...)`.
- `CTkTextbox` already notifies its scrollable ancestor.
- The app initializes `_queue_lock` before UI construction; 4.8.16 additionally hardens the mixin's lazy fallback.
- macOS tray mode remains intentionally disabled because pystray/Cocoa requires the process main thread, already owned by Tk.
- `customtkinter` is not a runtime dependency: `ui_kit.py` is a native Tk/ttk compatibility layer that only preserves historical `CTk*` names.

## Confirmed fixes

1. **Embedded player startup race** — `get_busy()` is ignored as an end-of-track signal during the short SDL warm-up window after play, unpause or seek.
2. **Queue lock fallback** — concurrent lazy access cannot create different `RLock` instances.
3. **Partial queue runtime snapshots** — missing runtime attributes now use stable defaults (`number`, `mp3`, `copy`, `off`).
4. **CTk color tuples/lists** — theme helpers choose the light or dark entry before passing a color to Tk.
5. **Template year zero** — numeric `0` is preserved as `"0"`.
6. **Linux wheel speed** — X11 Button-4/Button-5 now scroll one unit per notch.
7. **Queue/Search variable lifecycle** — stale/missing StringVars are validated and recreated against the active Tcl interpreter.
8. **Queue drag bindings** — fresh Treeview handlers replace rather than append duplicate callbacks.
9. **Tooltip lifecycle** — tabs explicitly dispose tooltip bindings on rebuild, without binding each tooltip owner to `<Destroy>`.
10. **Settings help wrapping** — shortcut text uses the actual current content width.

## Validation

- New 4.8.16 audit tests: **13 passed**.
- Existing suite was run in fresh Tk/Xvfb process groups to avoid cross-test Tcl `after` accumulation.
- Group results: **52 + 42 + 4 + 6 + 4 + 9 = 117 passed**.
- `python -m compileall`: passed.
