# AudioKnigi Downloader 4.12.16 — Event Bus Hardening

## Fixed

1. **Queued UI callback diagnostics**
   - `UIEventBus._drain()` no longer uses `traceback.print_exc()`.
   - Callback failures are written to the rotating `app.log` through `log_exception()` with full traceback context.
   - The callback label uses only module/qualified function name, avoiding argument/value leakage.

2. **The UI event pump cannot die because one callback failed**
   - Tk `after()` scheduling is performed in a `finally` block.
   - A callback exception, or even a failure inside the diagnostic logger, does not stop the next drain tick.
   - This specifically protects PyInstaller `--windowed` builds where `sys.stderr` may be unavailable.

3. **Queue item pause/resume preserves semantic state**
   - `QueueItem` now stores `status_code_before_pause` alongside `status_before_pause`.
   - Resuming a `retry_pending` item restores `retry_pending`, not generic `pending`.

4. **404/410 playlist refresh is truly once per book run**
   - Once `_process_book()` has refreshed the public page/playlist, later missing media parts can be skipped explicitly but cannot trigger another full refresh during the same run.

## Release hygiene

The source ZIP is generated after removing `__pycache__`, `*.pyc`, `.pytest_cache`, `.venv`, `build`, and `dist` artifacts.

## Validation environment

The source/regression suite was executed in the available Linux validation environment on Python 3.13.5. Windows packaging remains strictly pinned to CPython 3.14.7 x64 by `build_exe*.bat`, `build_ci.ps1`, and GitHub workflows. A Linux source test is not represented as a Windows 3.14.7 execution.
