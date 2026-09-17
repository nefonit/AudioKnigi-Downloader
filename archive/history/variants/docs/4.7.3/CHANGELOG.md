# Changelog

## 4.7.3

- Removed Book/Track/QueueItem `.get()` and subscript access from the typed runtime path; compatibility mapping access remains only for legacy callers.
- `MappingDataclass` now advertises read-only `Mapping` semantics instead of `MutableMapping`; field deletion raises `TypeError` instead of silently assigning `None`.
- Added regression coverage proving the shipped `dnd.py` is complete/compilable and HTTP session rotation survives `session.close()` failures.
- Fixed empty/directory cover paths so Pillow is never asked to open `Path("")` / a directory.
- Windows PowerShell notification fallback now uses hidden/no-window process flags.
- Increased the default Audiobookshelf library-scan timeout from 20s to 120s.
- Added queue-state `RLock`, typed QueueItem access, per-book runtime snapshots and a structural run snapshot to prevent UI/worker state races.
- Moved periodic player-position JSON writes off the Tk main thread into a single coalescing background writer; shutdown performs a synchronized final flush.
- Fixed template expansion so braces inside real book/author/track data (for example `{Remix}`) are preserved.
- Hardened template input handling for `None`/non-mapping tracks and books, and only treats extensions literally present in the template as format directives.
- Hardened tray icon creation for older Pillow versions and made each tray generation use private start/stop events so a slow old backend cannot poison a later `show()`.
- Improved ttk fallback compatibility: `CTkSwitch.get()`, CTkFrame height preservation, and owner-only tooltip `<Destroy>` handling.
- Added `tests/test_hardening.py` and wired it into CI/release workflows.

## 4.7.2

- Standardized Book/Track use in the application core on typed dataclass attribute access; legacy mapping access remains compatibility-only.
- Fixed disk-space preflight for not-yet-created target folders by checking the nearest existing parent; unknown free space no longer silently bypasses the check.
- Fixed ttk Treeview colors in `system` appearance mode by using CustomTkinter's effective Light/Dark mode.
- Made JSON persistence thread-safe and atomic with a process-wide `RLock` plus `os.replace()`.
- Disabled speed-graph spline smoothing until at least three data points exist.
- Blocked queue deletion/clearing while the queue worker is active and fixed DnD insertion-slot calculations for top-to-bottom moves.
- Kept strict slotted dataclasses intentionally; no undeclared runtime fields are written to Book/Track/QueueItem.
- Moved unfinished-download startup scanning to a daemon worker, validated output paths and bounded directory depth.
- Backup restore now reapplies audio, normalization, templates, bandwidth, integration, UI and language settings to live variables.
- First-run wizard preserves an existing pure `m4b` output mode.
- Cover caches now use stable URL/path keys and prune stale images after queue/history changes.
- Template engine safely handles missing/non-numeric track indices, target extensions and mixed Windows path separators.
- Tooltips now hide on `<Destroy>` to prevent orphan popups.
- Tray startup/shutdown is synchronized to prevent show/hide races and phantom icons.
- Added `tests/test_maintenance.py` and wired it into CI/release smoke tests.

## 4.7.1.3

- Fixed `TclError: image "pyimageN" doesn't exist` when a previous cover preview was cleared.
- CTkLabel image replacement is now image-first and text-second.
- The native Tk image slot is cleared before CTkImage replacement to recover from stale Tcl image handles after DPI/theme redraws.
- Applied the same safe image lifecycle to the completion/result cover card.
- Added a regression test that simulates a stale Tk image handle.

- Range segments now continue automatically when a CDN/proxy returns a capped partial 206 response (for example 3 MiB).
- Interrupted Range responses preserve already-written bytes and retry from the first missing byte.
- Added regression coverage for server-capped Range responses.

## 4.7.1.1

- Fixed delayed UI error callbacks capturing Python exception variables after the `except` block had exited.
- Fixed all five affected callbacks in analysis, download, recheck and Audiobookshelf paths.
- Added an architecture regression guard that rejects unsafe exception-variable capture inside deferred lambda bodies.

## 4.7.1

- Renamed the internal package from `audioknigi_v46` to stable `audioknigi`.
- Moved runtime version to `audioknigi.__version__` / `audioknigi/version.py`.
- Added `pyproject.toml` with dynamic version metadata.
- Standardized documentation as `README.md` and `RELEASE_SETUP.md`.
- Moved smoke/regression scripts to version-neutral `tests/` modules.
- Routed Audiobookshelf HTTP through the shared retry-enabled session.
- Added explicit architecture tests for HTTP timeouts and GUI worker-thread rules.
- Added rotating privacy-sanitized application logs (1 MB × 3 backups).
- Bounded the last crash report and kept it privacy-sanitized.
- Added an explicit `.part` single-stream resume regression test.

## 4.7.0

- First-run wizard, listening-position resume, library covers, duplicate detection, site-structure diagnostics, Help Center, accessibility and RU/UK/DE/EN localization foundation.
