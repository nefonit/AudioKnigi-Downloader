# Reported issues verification and hardening

Verified against the Branded TTKBootstrap archive.

## Fixed
- `show_m4b_preview`: track index is normalized with `safe_int` before `:02d`.
- `set_busy`: queue state uses `getattr(..., False)`.
- Context single-part MP3 override: generation token prevents a stale worker `finally` from overwriting newer runtime options.
- Accessibility Treeview announcements now calculate position among the selected item's siblings, including nested nodes.
- `_parent_bg`: themed ttk widgets resolve style backgrounds without expected `TclError` probes.
- MainTab comments/grid metadata and QueueTab unused imports were cleaned up.

## Verified as not present / intentional
- `audioknigi/__init__.py` is valid Python; the Windows `prismatoid` marker is in `requirements.txt`.
- `apply_tree_zebra` is defined in `audioknigi/ui_kit.py`.
- `ui_kit.py` is complete and does not end with `font=`.
- `AudioKnigiApp.copy_last_crash_report` exists.
- `CTkButton` intentionally ignores historical CustomTkinter pixel widths and lets native ttk auto-size captions; regression tests enforce this to prevent clipping under DPI scaling.
- `CTkOptionMenu` now uses a selective Tcl-level unbind helper. Python 3.11/3.12 accepted `funcid`, but their implementation could remove the whole sequence binding; the helper preserves unrelated callbacks and matches Python 3.13+ semantics.
