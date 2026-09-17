# AudioKnigi Downloader

**Current version: 4.8.12**

### Search accuracy in 4.8.2

- Search now mirrors the site's current form exactly: `GET https://audioknigi.com.ua/search?text=<query>`.
- Queries can be an author surname (for example `Сандерсон`) or a book title.
- Result parsing merges duplicate cover/title links and rejects unrelated `/audio-*` links from sidebars/recommendations unless the requested words are present in the book label.
- Minimum query length is 3 characters, matching the website form.


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

## Modern universal interface

There is no separate screen-reader mode. The visible interface is the accessible interface. Since 4.8.0, the runtime widget tree uses native Tk/ttk controls and containers only; `ttkbootstrap` supplies the modern visual theme without replacing controls with Canvas-drawn buttons or fields. The core dark palette is WCAG-AA friendly, controls have visible focus, Treeviews use larger rows and zebra striping, and buttons keep explicit text names even when an icon is shown.

On Windows, `prismatoid` is loaded lazily and talks directly to a running NVDA or JAWS instance; if neither reader is running, the app produces no extra speech. Important status/progress announcements are throttled. See `ACCESSIBILITY.md` and `MODERN_UI.md`.

## Threading rule

Tkinter/ttk runs on the main GUI thread. Page analysis, downloads, cover fetching, queue processing, Audiobookshelf connectivity tests and file checks are launched in worker threads. Workers send UI changes through the event bus instead of performing network work on the GUI thread.

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
py tests/test_audit_477.py
py tests/test_audit_478.py
py tests/test_range.py
py tests/test_network_integration.py
py tests/test_audio.py
py tests/test_reliability.py
py tests/test_user_experience.py
py tests/test_accessibility.py
py tests/test_modern_accessible_ui.py
py tests/test_audit_481.py
py tests/test_audit_4810.py
py tests/test_audit_4811.py
```

GitHub Actions runs the complete test suite on Windows.

## Version history
- **4.8.12** — refreshed native Tk 9.1+ accessibility names on late registration, made tray hiding non-blocking, hardened history against mapping records, normalized `configure({...})` compatibility across native CTk wrappers, added Linux Cyrillic-layout physical edit shortcuts, and resolved ttk Notebook parent backgrounds from the active style.
- **4.8.11** — made live chapter timing updates self-marshalling to the Tk thread, hardened clipboard focus scheduling, made interrupted-download recovery safe with partially constructed UI variables, and cleared stale resume selections before multi-book queue restore; added regression coverage for download-error busy cleanup and complete `ui_kit.py` imports.
- **4.8.10** — fixed native Tk/tkinterdnd2 Drag-and-Drop integration, stale queue indices, resume/path normalization, nested scroll ownership, rapid tray re-show, application-owned Tk variables and PhotoImage interpreter ownership; hardened theme/width handling and logical tab shortcuts.
- **4.8.9** — hardened notifications, player state, templates, resume/history, native UI-kit reconfiguration, dynamic scrolling, tray lifecycle, Search/Settings/Queue interactions, while preserving all 4.8.8 interface fixes.
- **4.8.8** — completed the advanced UI audit: labeled Search results and scrollbars, kept Search/Queue/History actions visible, added full tooltips/accessibility names, explained the two progress bars, renamed file verification, added History backup/restore controls, and rebuilt the mini-player so Play/Pause/Stop cannot be pushed off-screen by long filenames.
- **4.8.7** — fixed reproducible Tkinter `RecursionError` during widget teardown and event re-entry; removed unsafe tooltip `<Destroy>` callbacks and nested `update_idletasks()` geometry processing while preserving the 4.8.6 timing fix.
- **4.8.6** — fixed empty Start/End/Duration columns for one-file-per-chapter PlayerJS playlists: parses duration/length/time metadata, uses measured local MP3 duration as a display fallback, best-effort probes missing remote durations with ffprobe, and refreshes timing cells while downloads are verified.
- **4.8.5** — added Ctrl+Z/Ctrl+Y undo-redo to native input fields (including Cyrillic Windows layouts), fixed Help/child windows opening with mixed light/dark surfaces, themed menus/tooltips/preview windows, and made the simple dashboard responsive + vertically scrollable so captions stay visible at 100–200% UI scale.
- **4.8.4** — fixed the Python 3.14 Tkinter recursion crash, completed Ctrl+C/Ctrl+V handling for Cyrillic Windows layouts, fixed remaining native-Tk sizing/clipping issues, and made dark/light theme switching recolor all native surfaces.
- **4.8.3** — restored Ctrl+C/Ctrl+V/Ctrl+X/Ctrl+A editing in all native fields, fixed ttk pixel-width migration that clipped/overflowed Russian UI text, added table scrollbars, and made Queue controls responsive.
- **4.8.2** — site-accurate `/search?text=` search, query-aware result filtering, duplicate-link merging, and sidebar/recommendation rejection.
- **4.8.1** — accessibility/UI polish: persistent field examples, native ttk focus cleanup, restored keyboard-aware scrolling for Settings, and audit regression coverage.
- **4.8.0** — Modern Accessible UI: native Tk/ttk runtime, ttkbootstrap theming, WCAG-AA palette, roomier Segoe UI typography, Treeview zebra/density polish, text-named actions and tab-focus improvements.
- **4.7.10** — settings lifecycle hardening: safe partial initialization, guarded persistence, and trace cleanup on tab destruction/rebuild.
- **4.7.9** — auto-download busy-state handoff hardening, adaptive mode-button styling for native ttk/future CTk implementations, and worker-safe output-mode lookup.
- **4.7.8** — runtime/UI edge-case hardening: source-index-independent track rows, queue pause-status preservation, null-safe resume manifests, player-position self-initialization, safer history image insertion, direct numeric template indices, accessibility naming and partial-settings initialization guards.
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
