# Audit 4.8.10

This release validates the follow-up audit against the uploaded 4.8.9 archive and fixes the confirmed issues.

## Confirmed and fixed

- Native Tk + `tkinterdnd2` adapter: `TkinterDnD.require()` alone did not add the Python `DnDWrapper` methods to ordinary Tk/ttk widgets, causing `drop_target_register` to fall through to `_tkinter.tkapp` on Windows.
- Stale queue Treeview indices in move/priority/pause commands.
- Multi-book resume `selected_indices` type normalization.
- Case-insensitive unfinished-download directory matching on Windows.
- Application-owned fallback `StringVar` lifecycle and stale-variable probing.
- Nested scrollable widgets keeping ownership of mouse-wheel events.
- Fractional-string historical widths.
- Immediate `_CURRENT_DARK` synchronization when appearance mode changes.
- Rapid tray hide/show now queues a re-show instead of silently failing while still preventing overlapping native tray loops.
- Redundant player saved-position label assignment.
- Explicit Tcl/Tk master ownership for Pillow/Tk `PhotoImage` objects.
- Logical tab keys for global Queue/History/Search shortcuts.
- Explicit `MappingDataclass.__slots__ = ()`.

## Verified as already safe / false positives

- `_clipboard_offer_after`, `_last_clipboard_offer`, `last_completed_folder`, and `speed_history` are initialized in `AudioKnigiApp.__init__` before their callbacks are installed.
- `AudioKnigiApp.t()` exists.
- `effective_track_duration(... or 0)` guards unknown durations.
- `DownloaderMixin._book_folder()` uses `runtime_output_dir`; the analysis worker does not read `output_var.get()` there.
- ID3 save failures are already caught and logged by `_write_id3`.
- The reported `ui_kit.py` unexpected-EOF/syntax error was an artifact of a truncated source excerpt. The shipped file is complete and compiles.
- `MappingDataclass` did import under Python 3.13 before this change; explicit empty slots were nevertheless added to remove inherited per-instance `__dict__` and make the slots contract unambiguous.
- Template rendering fixes from 4.8.9 remain intact.

## Validation

- `python -m compileall`: passed.
- `python audioknigi_gui.py --ci-selftest`: passed as version 4.8.10.
- Full test suite under Linux/Xvfb: **52 passed**, with one pre-existing PytestCollectionWarning for `TestDownloader.__init__` in `tests/test_range.py`.
- Added `tests/test_audit_4810.py`: 15 focused checks covering this audit.
- Six-second GUI smoke launch under Xvfb stayed alive without traceback; exit 124 was the intentional timeout stop.

The available validation runtime is Python 3.13.x on Linux/Xvfb. Windows/Python 3.14.3 remains the target-platform validation for Tk/tkdnd behavior.
