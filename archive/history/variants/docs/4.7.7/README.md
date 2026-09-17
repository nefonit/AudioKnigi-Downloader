# AudioKnigi Downloader

**Current version: 4.7.7**

Windows desktop application for analyzing, downloading and organizing audiobooks. The project uses a modular package named `audioknigi`; the package name is deliberately version-independent. The application version has a single Python source of truth: `audioknigi/version.py` (`audioknigi.__version__`). `pyproject.toml` reads the same value dynamically.

## Quick start

```powershell
py -m pip install -r requirements.txt
py -m playwright install chromium
py audioknigi_gui.py
```

FFmpeg/FFprobe must be available in `PATH` for source-mode development. The release build can bundle them.

## Architecture

- `audioknigi/` — application package without version in its import path.
- `audioknigi/downloader.py` — requests-first parsing, resumable HTTP Range downloads, Auto-Chunker, FFmpeg/FFprobe processing.
- `audioknigi/player.py` — mini-player and saved listening positions.
- `audioknigi/storage.py` — history, settings, backups, resume manifests and library metadata.
- `audioknigi/event_bus.py` — thread-safe UI message queue.
- `audioknigi/ui/` — UI tabs/components.
- `audioknigi/logging_utils.py` — privacy-sanitized rotating application log.
- `tests/` — smoke/regression tests with version-neutral filenames.

## Universal accessibility

There is no separate screen-reader mode. The visible interface is the accessible interface: interactive controls are native Tk/ttk widgets, while CustomTkinter is used for visual containers/cards. On Windows, `prismatoid` is loaded lazily and talks directly to a running NVDA or JAWS instance; if neither reader is running, the app produces no extra speech. Important status/progress announcements are throttled. See `ACCESSIBILITY.md` for the keyboard and testing contract.

## Threading rule

Tkinter/CustomTkinter runs on the main GUI thread. Page analysis, downloads, cover fetching, queue processing, Audiobookshelf connectivity tests and file checks are launched in worker threads. Workers send UI changes through the event bus instead of performing network work on the GUI thread.

## Network reliability

All application HTTP traffic goes through retry-enabled `requests.Session` objects. Sessions carry a User-Agent, explicit connect/read timeouts, retry policy and persisted browser cookies/profile. Interrupted media downloads use HTTP `Range` and `.part` files for resume.

## Logs and privacy

`%APPDATA%/AudioKnigiDownloader/app.log` uses `RotatingFileHandler` with a 1 MB limit and 3 backups. URLs, home-directory paths and obvious API keys/tokens/Authorization values are sanitized before they are written. `last_crash_report.txt` is overwritten rather than appended, so it cannot grow indefinitely.

## Tests

```powershell
py tests/test_core.py
py tests/test_architecture.py
py tests/test_maintenance.py
py tests/test_hardening.py
py tests/test_audit_474.py
py tests/test_audit_475.py
py tests/test_range.py
py tests/test_network_integration.py
py tests/test_audio.py
py tests/test_reliability.py
py tests/test_user_experience.py
py tests/test_accessibility.py
```

GitHub Actions runs the complete test suite on Windows.

## Version history
- **4.7.7** — audit hardening after the 4.7.6 accessibility release: safe model serialization without deep-copying GUI images, explicit empty-cover handling, stronger privacy path masking, typed interrupted-queue restore, normalization/output UI synchronization, robust language selection, CTkLabel-aware accessibility labels, and more explicit WinRT toast construction.

- **4.7.6** — universal accessibility: a single visual UI for sighted users and JAWS/NVDA users, native interactive Tk/ttk controls, real radio buttons inside quality cards, automatic Prismatoid NVDA/JAWS output with no TTS fallback/toggle, semantic focus/table/tab announcements, 10% progress announcements and forward support for Tk 9.1 `tk accessible`.
- **4.7.5** — runtime edge-case hardening: safe untitled-book filenames/tags, explicit cover payload handling, UI-thread publication of search results, explicit Windows Runtime toast activation, robust natural-end player position handling, and guaranteed template folder fallback.
- **4.7.4** — audit hardening: safer keyboard focus handlers, synchronized friendly/advanced network presets, stable Tk variables, child-Unmap filtering, safe HTML parsing, Audiobookshelf URL normalization, PowerShell-safe notifications, strict dataclass mapping keys, cancellable first-run wizard, thread-safe player positions, corrupted-setting recovery, template edge cases, fallback UI/Tooltip and tray retirement hardening.
- **4.7.3** — runtime hardening: strict typed model access, queue locking/snapshots, non-blocking player-position persistence, template edge-case fixes, hidden Windows notifications, tray/fallback-UI robustness and Audiobookshelf timeout hardening.
- **4.7.2** — maintenance hardening: atomic JSON, disk-space preflight, async recovery scan, queue/DnD fixes, backup restore and cache robustness.
- **4.7.1** — package/version cleanup, standard repository layout, rotating privacy-safe logs, network timeout/session audit.
- **4.7.0** — first-run wizard, player resume, library covers, duplicate detection, crash report, help center, accessibility and i18n foundation.
- **4.6.x** — user-friendly/visual refresh.
- **4.5.x** — CI/CD, metadata and standalone release pipeline.
