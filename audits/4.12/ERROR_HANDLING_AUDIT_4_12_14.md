# Error-handling audit — 4.12.14

Static audit of every Python module under `audioknigi/` after the 4.12.14 diagnostics changes.

## Summary

- Python modules checked: **40**.
- `try` blocks: **691**.
- exception handlers: **699**.
- broad `Exception`/`BaseException` handlers: **626**.
- pass-only handlers: **376**.
- bare `except:` handlers: **0** (enforced by regression test).
- all modules parse/compile successfully (enforced by regression/compile checks).

## Policy after this audit

- Unhandled Tk callbacks, background threads, and main-thread failures are written to `app.log` with traceback, thread, module, function, and line number.
- High-level recoverable boundaries (analysis, provider search, queue item processing, backup/restore, ID3/M4B/sidecars, Audiobookshelf) now also write traceback context before showing a friendly UI message or continuing.
- Best-effort UI cleanup, widget teardown, optional accessibility calls, and visual refresh fallbacks may remain silent to avoid turning expected Tk destruction races into log spam.
- Low-level network/integration functions are allowed to fail fast when their callers own the user-facing recovery and logging policy (for example `integrations.py`).

## Per-module counts

| Module | try | handlers | broad | pass-only |
|---|---:|---:|---:|---:|
| `audioknigi/__init__.py` | 0 | 0 | 0 | 0 |
| `audioknigi/accessibility.py` | 36 | 35 | 34 | 21 |
| `audioknigi/actions.py` | 110 | 110 | 102 | 70 |
| `audioknigi/app.py` | 59 | 60 | 57 | 33 |
| `audioknigi/brand.py` | 0 | 0 | 0 | 0 |
| `audioknigi/core.py` | 20 | 20 | 16 | 5 |
| `audioknigi/crash_report.py` | 1 | 1 | 1 | 1 |
| `audioknigi/dnd.py` | 13 | 13 | 12 | 7 |
| `audioknigi/downloader.py` | 81 | 89 | 63 | 33 |
| `audioknigi/event_bus.py` | 4 | 4 | 3 | 1 |
| `audioknigi/event_sounds.py` | 10 | 10 | 9 | 7 |
| `audioknigi/help_center.py` | 3 | 3 | 3 | 3 |
| `audioknigi/i18n.py` | 1 | 1 | 1 | 0 |
| `audioknigi/integrations.py` | 0 | 0 | 0 | 0 |
| `audioknigi/knigavuhe.py` | 15 | 15 | 13 | 4 |
| `audioknigi/library_visuals.py` | 4 | 4 | 3 | 0 |
| `audioknigi/logging_utils.py` | 3 | 3 | 3 | 3 |
| `audioknigi/models.py` | 1 | 1 | 1 | 1 |
| `audioknigi/notifications.py` | 3 | 3 | 3 | 2 |
| `audioknigi/onboarding.py` | 11 | 11 | 11 | 11 |
| `audioknigi/player.py` | 23 | 23 | 22 | 10 |
| `audioknigi/poleknig.py` | 25 | 24 | 22 | 4 |
| `audioknigi/queue_manager.py` | 18 | 20 | 17 | 7 |
| `audioknigi/search.py` | 19 | 19 | 18 | 9 |
| `audioknigi/sources.py` | 2 | 2 | 2 | 0 |
| `audioknigi/storage.py` | 22 | 22 | 15 | 8 |
| `audioknigi/templates.py` | 3 | 3 | 1 | 1 |
| `audioknigi/tray.py` | 17 | 17 | 14 | 9 |
| `audioknigi/ui/__init__.py` | 0 | 0 | 0 | 0 |
| `audioknigi/ui/easy_home.py` | 33 | 32 | 32 | 25 |
| `audioknigi/ui/history_tab.py` | 2 | 2 | 2 | 1 |
| `audioknigi/ui/main_tab.py` | 3 | 2 | 2 | 2 |
| `audioknigi/ui/production_ui.py` | 0 | 0 | 0 | 0 |
| `audioknigi/ui/queue_tab.py` | 1 | 1 | 1 | 1 |
| `audioknigi/ui/search_tab.py` | 5 | 4 | 4 | 3 |
| `audioknigi/ui/settings_tab.py` | 19 | 19 | 19 | 15 |
| `audioknigi/ui_kit.py` | 124 | 126 | 120 | 79 |
| `audioknigi/ui_state.py` | 0 | 0 | 0 | 0 |
| `audioknigi/version.py` | 0 | 0 | 0 | 0 |
| `audioknigi/visuals.py` | 0 | 0 | 0 | 0 |

Pass-only counts are not automatically defects: most are local defensive fallbacks around Tk widget destruction, optional libraries, and non-critical visual/accessibility enhancements. Fatal/user-visible operation boundaries are logged separately as described above.
