# Audit 4.8.19

## Confirmed false positives

- `actions.py`, `app.py`, `_full_worker`, `download_full`, and `SearchMixin` are complete and compile; reported EOF/SyntaxError findings came from truncated excerpts.
- `AudioKnigiApp` provides `t()` and `_update_bandwidth_label()`. Player helpers `_player_position_key()` and `_player_select_current()` are provided by `PlayerMixin`, which is part of `AudioKnigiApp`.
- Prismatoid is intentionally imported as `from prism import ...` on Windows.
- `_strip_ctk_kwargs()` exists in `ui_kit.py`.
- Backup history validation, empty-folder cover protection, and queued tray notifications were already present in 4.8.18.
- `os.walk(..., followlinks=False)` prevents the unfinished-download scan from following directory symlinks.
- First-run `output_mode` supports MP3/M4B/Both; unchecking M4B correctly selects MP3. OGG/FLAC are not `output_mode` choices in this application.

## Changes made

- AccessibilityManager now owns/cancels scheduled Tk callbacks during close.
- Tooltip/resource cleanup added to MainTab, HistoryTab, and EasyHome.
- EasyHome uses the common live StringVar helper for app-owned variables.
- History double-click ignores empty table space and activates the exact row under the pointer.
- Settings rebuilds are trace/autosave-idempotent, shortcut wrapping is width-debounced, and secret masking uses `*`.
- Queue drag remains targetable above/below occupied rows.
- Unsupported tray mode is shown disabled in Settings.
- Search tie-breaking prefers shorter equally relevant labels; inline punctuation is reconstructed without an artificial space.

## Verification

- `python -m compileall -q`: pass.
- Main pytest run: `132 passed, 2 deselected`; the two deselected legacy Tk tests both pass in fresh Tcl/Tk processes.
- New audit test plus those two legacy tests: `5 passed`.
- Script-style smoke/audit modules: 27/27 pass when run with the project root on `PYTHONPATH`.
