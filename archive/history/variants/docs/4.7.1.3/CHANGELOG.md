# Changelog

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
