# AudioKnigi Downloader

**Current version: 4.7.1.1**

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
py tests/test_range.py
py tests/test_network_integration.py
py tests/test_audio.py
py tests/test_reliability.py
py tests/test_user_experience.py
```

GitHub Actions runs the complete test suite on Windows.

## Version history

- **4.7.1** — package/version cleanup, standard repository layout, rotating privacy-safe logs, network timeout/session audit.
- **4.7.0** — first-run wizard, player resume, library covers, duplicate detection, crash report, help center, accessibility and i18n foundation.
- **4.6.x** — user-friendly/visual refresh.
- **4.5.x** — CI/CD, metadata and standalone release pipeline.
