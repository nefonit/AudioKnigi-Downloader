# Audit 4.8.9

This release addresses the follow-up code audit performed against 4.8.8.

## Verified as already correct in 4.8.8

- `AudioKnigiApp.__init__` initializes `_clipboard_offer_after = None` before focus callbacks can use it.
- `AudioKnigiApp.t()` exists and delegates to the i18n translator.
- duration totals use `float(effective_track_duration(track) or 0)`, so unknown duration does not raise `TypeError`.

## Fixed in 4.8.9

- Correct Windows Runtime namespace in the PowerShell toast fallback and truthful success/failure result.
- Player Pause/Stop state after Stop and natural end.
- UTF-8 string handling in cover-payload cache keys.
- Localized first-run step counter.
- `MappingDataclass` ABC contract.
- Unknown template token preservation and metadata slash sanitization before folder path splitting.
- Orphan scanning for non-MP3 final formats.
- Template settings restored for multi-book interrupted queues and applied by queue runtime snapshots.
- Defensive history iid and parts parsing.
- Safe `CTkOptionMenu.configure(command=...)` callback replacement.
- Dynamic mouse-wheel/focus binding for late children of `CTkScrollableFrame`.
- `CTkSwitch.configure(variable=...)` variable tracking.
- Tray hide/show generation race.
- Search entry reference retention and double-click region filtering.
- Autosave for advanced connection-count/slow-threshold controls and preservation of manually chosen 2/4/8 stream count.
- Queue drag starts only from data cells.

## Regression coverage

- `tests/test_audit_489.py`: 14/14 passed.
- Related audit/core/UI regression set: 35/35 passed.
- Minimum-window/layout checks: 6/6 passed.
- Legacy script-style audit, maintenance, hardening, core and architecture checks passed under Xvfb where Tk requires a display.
- `python audioknigi_gui.py --ci-selftest`: OK (`4.8.9`).
- Six-second GUI smoke launch produced no traceback; the process was intentionally stopped by timeout while the window remained alive.

The available validation runtime is Python 3.13.5 on Linux/Xvfb. The code retains the Python 3.14/Tk recursion hardening from 4.8.7, but final Windows/Python 3.14.3 validation should still be performed on the target machine.
