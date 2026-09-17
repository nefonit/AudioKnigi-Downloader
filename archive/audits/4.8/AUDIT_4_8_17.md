# Audit 4.8.17

This release reviews the proposed ttk/ttkbootstrap tab-hardening changes against the actual 4.8.16 code.

## Confirmed and changed

- `StringVar` bootstrap logic was duplicated across Settings, Queue and Search. It is now centralized in `ui_kit.ensure_app_string_var()`.
- Existing stale Tcl variables are probed before reuse; application-root ownership is preferred and test hosts use the tab frame as fallback.
- The helper raises a clear initialization error rather than returning `None`.

## Already correct in 4.8.16

- Settings shortcut help already recalculates `wraplength` from the actual container width on `<Configure>`.
- QueueTab and SearchTab already bind `<Destroy>` and dispose tooltip resources.
- Queue Treeview drag handlers are already bound without `add="+"`, so rebuilding a fresh widget cannot stack duplicate Python callbacks.
- `ui_kit` uses native Tk/ttk widgets; ttkbootstrap is only the optional style engine.

## Additional regression fix

- A pre-existing 200% DPI regression was exposed by the full UI suite: quality-card descriptions could request more width than the reflowed card. Descriptions now recompute `wraplength` from the actual card width on `<Configure>`.

## Verification

- 120 collected tests passed in fresh Tk/Xvfb groups.
- `compileall`, `--version`, and `--ci-selftest` pass.
