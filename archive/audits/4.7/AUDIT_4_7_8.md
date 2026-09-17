# Audit 4.7.8

This release was prepared from the user-supplied 4.7.7 ZIP, not from isolated source snippets.

## Confirmed fixes

- Track selection/toggling no longer assumes `Track.index == list position + 1`; Treeview rows use independent UI IDs and map directly to Track objects.
- Player position persistence tolerates alternate/minimal hosts that did not pre-create `player_positions`.
- Item-level queue pause restores the status that existed before pausing, including `Ожидает повтор`.
- `continue_unfinished()` tolerates `selected_indices: null` and malformed individual values.
- History rows without a cover omit the `image` Treeview option.
- `_safe_track_index(5)` now returns `5`.
- EasyHome native controls receive `accessible_name` before returning to native keyboard behavior.
- Friendly output settings tolerate a partially initialized app.
- Bundled executable resolution requires an actual file.

## Reports that did not reproduce in the shipped 4.7.7 ZIP

- `core.py` was not truncated and compiled successfully.
- The Simple/Advanced buttons are not CustomTkinter `CTkButton` objects at runtime: since 4.7.6 the compatibility `CTkButton` class subclasses native `ttk.Button`, so `style=` is valid.
- The accessibility manager already sees all current interactive CTk-compatible controls because those wrappers are native Tk/ttk widgets. 4.7.8 nevertheless adds a conservative class-name fallback for future true CustomTkinter interactive controls.
- The Windows notification fallback is intentionally best-effort; inability to display a toast does not affect downloads.

## Regression coverage

`tests/test_audit_478.py` covers the fact-checks and the confirmed fixes above and is executed by CI and release workflows.
