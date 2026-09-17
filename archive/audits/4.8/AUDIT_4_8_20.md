# Audit 4.8.20

## Verified false positives

- `ActionsMixin.context_download_part()` is complete; the reported EOF fragment was truncated input.
- `CTkTabview.add()` is complete and stores the new frame after calling `Notebook.add(...)`.
- `_update_bandwidth_label()` exists on `AudioKnigiApp`.
- The application imports Prismatoid through its installed Python module name `prism`; this remains intentional.

## Confirmed fixes

1. **Transfer-rate semantics** — `record_transfer_metrics()` now names its input `speed_bytes_per_sec`, matching `SlidingSpeedMeter`, which measures downloaded bytes over time. The UI continues to display MiB/s.
2. **Range threshold** — `segment_threshold_mb` is no longer overwritten with `16`. It has a live Tk variable, is persisted/restored, and is exposed in Advanced Settings as 4/8/16/32/64 MiB.
3. **Queue single-worker guarantee** — `start_queue()` acquires the running state under the queue lock before starting a thread. Repeated Start/Retry calls return without starting another worker. A run-generation token protects final cleanup.
4. **Stable queue status updates** — worker callbacks update the `QueueItem` by object identity instead of assuming the original list index is still valid. Completion counters are read under the same lock.
5. **Priority toggle** — disabling priority restores the book's previous queue position.
6. **Player label** — starting playback from the track tree updates the label to `Сейчас играет: <file>`.
7. **First-run close behavior** — closing the wizard is treated as “skip onboarding” and persists `first_run_complete`, avoiding an unwanted wizard on the next launch.
8. **Cover payload keys** — cache hashing supports bytes, strings, objects with `tobytes()`, and generic payload representations.
9. **Textbox selection handling** — copy/cut checks whether a selection exists before accessing Tk `sel.*` indices.
10. **Tk teardown recursion** — tab/view cleanup no longer relies on `<Destroy>` event bindings. A small `install_destroy_cleanup()` wrapper invokes cleanup before the widget's real `destroy()` method. This keeps tooltip/trace cleanup deterministic and avoids the Tk event-substitution recursion reproduced by `test_tk_recursion_487.py`.

## Regression verification

- New audit tests: `tests/test_audit_4820.py` — 8 passed.
- Audit regression group (`4810` through `4820` plus `489`) — 119 passed.
- Timing / Tk recursion / advanced UI controls / theme regression checks were also run in fresh Xvfb/Tk processes; the targeted groups passed.
- Script-style smoke checks passed for maintenance, queue UI, threading, Range resume, user experience, visual UI, accessibility, DnD, core, friendly UI, and modern accessible UI.
- `compileall`, `--version`, and `--ci-selftest` are part of the final release check.
