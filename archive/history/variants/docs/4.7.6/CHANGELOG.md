# Changelog

## 4.7.6

- Made accessibility inherent to the single interface: there is no screen-reader-mode setting or alternate UI.
- Interactive controls are always native Tk/ttk widgets even when CustomTkinter is installed; CustomTkinter remains visual-only for cards, covers and layout.
- Replaced clickable-only quality cards with real native radio buttons while preserving the visual card design and mouse-wide click target.
- Added automatic Windows NVDA/JAWS direct-output integration through Prismatoid; it only acquires NVDA/JAWS backends and never falls back to SAPI/TTS.
- Re-detects a reader started/restarted after the app, without restart or user configuration.
- Added semantic focus descriptions, checkbox/radio state, tree-row position, notebook tab selection and restrained live status announcements.
- Progress speech is throttled to 10% milestones to avoid repetitive output.
- Added runtime support for Tk 9.1 `tk accessible` when present while remaining compatible with CPython 3.14's bundled Tk 8.6.
- Added `ACCESSIBILITY.md` and `tests/test_accessibility.py`; CI/release jobs now enforce the universal-accessibility contract.

## 4.7.5

- Normalize missing book titles to `audiobook` before full-MP3/M4B filenames and Mutagen tags.
- Explicitly handle empty tuple cover payloads.
- Publish completed search-result lists on the UI thread instead of incrementally mutating shared state in the worker.
- Explicitly activate Windows Runtime toast types in the PowerShell fallback while keeping user content Base64-transported.
- Track the last valid player position so natural end-of-track clears resume state even when pygame immediately returns `-1`; unexpected early stops preserve resume state.
- Guarantee a non-empty `audiobook` fallback folder for templates.

## 4.7.4

- Made keyboard focus decoration exception-safe for dynamic CustomTkinter cards.
- Kept friendly speed presets synchronized with the advanced segment-count control and made queue/search Tk variables persistent across tab rebuilds.
- Standardized Treeview `show` values and made the track context-menu master explicit.
- Ignored child `<Unmap>` events so tab/layout changes cannot accidentally trigger tray minimization.
- Hardened metadata parsing for `html=None`; retained the verified source-mode resource path and disk helper.
- Normalized Audiobookshelf URLs without a scheme and kept the long 120-second scan timeout.
- Removed PowerShell interpolation of notification text by transporting escaped toast XML as Base64.
- Restricted MappingDataclass mapping keys to declared dataclass fields only.
- Closing the first-run wizard no longer marks setup complete.
- Made player-position lock creation, snapshots and mutations thread-safe while retaining asynchronous disk writes and synchronous shutdown flush.
- Hardened logging home-path masking and corrupted numeric setting recovery.
- Preserved a track title of `0`, hardened folder-template edge cases, fallback widget option translation, Tooltip teardown and late tray-stop behavior.
- Added `tests/test_audit_474.py` and wired it into CI/release workflows.

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
