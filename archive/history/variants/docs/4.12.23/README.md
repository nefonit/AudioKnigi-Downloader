# AudioKnigi Downloader


### Звуки событий

Начиная с 4.10.2 программа поддерживает языковые пакеты коротких звуковых подсказок. В 4.10.4 английский пакет полностью покрывает все 17 зарегистрированных событий; при английском интерфейсе для каждого события используется английская запись. Звуки можно отключить, изменить громкость и проверить в **Настройки → Звуки программы**; они используют отдельный канал и не заменяют файл во встроенном мини-плеере.

### Поддерживаемые сайты
- `audioknigi.com.ua`
- `knigavuhe.org` — поиск через `/search/?q=...`, загрузка доступных книг по страницам `/book/...`.
- `poleknig.com` — поиск через `?q=...` плюс автоматическое раскрытие пагинации каталога найденного автора `/authors/<id>?p=...`, страницы книг `/books/<id>`, открытые плейлисты PlayerJS.

Поиск во вкладке «Поиск» работает сразу по трём источникам. Страницы, удалённые/ограниченные самим сайтом по просьбе правообладателя, программа не обходит.

**Current version: 4.12.23**






## 4.12.23 — Audit Hardening & Adaptive Range Recovery

- Audited the reported `bootstyle`/CustomTkinter concerns against the real source. `CTk*` names are native Tk/ttk compatibility wrappers; `CTkButton` consumes `bootstyle` and maps it to ttk styles, so external CustomTkinter remains intentionally absent.
- Centralized the application title through `brand.DISPLAY_NAME`; screen-reader ready announcements no longer hard-code the product name.
- Moved the `DragDropMixin` documentation string to the actual class docstring position while retaining defensive `getattr` fallbacks for lightweight hosts.
- `load_json()` now shares the same in-process `_JSON_LOCK` as atomic `save_json()` writers, preventing a reader from racing an application-owned JSON replacement.
- Removed the dead MP3-only `output_mode` local and stopped mutating escaped slashes before `json.loads()`; standard JSON parsing handles `\/` directly.
- Improved Auto-Chunker recovery: workers parked after a downshift no longer terminate permanently, and sustained recovered throughput can raise active Range concurrency back toward the configured initial level.
- Added a root-coordinate fallback for focus auto-scroll when Tk parent-name traversal is unavailable in an unusual widget hierarchy.
- Hardened responsive layout discovered during the wider regression run: simple mode now bases stacking on the current DPI-scaled natural widths of main/sidebar panels, quality cards use the actual main-panel width, and the advanced Book header reserves the full natural width of the one-button bulk selector at 125%+ scaling.
- Verified reported false positives: no `search_tab.py` SyntaxError, no `[source: ...]` artifact in requirements/Python, Treeview zebra tags are configured and assigned, tray hiding still requires the main window to be `iconic`, and compatibility aliases reference the same widget rather than duplicate state.

See `AUDIT_HARDENING_4_12_23.md` for the item-by-item classification.


## 4.12.22 — One Toggle Bulk Selection Button

- Replaced the two separate **«Выбрать все»** / **«Снять все»** controls above the advanced Book parts table with one state-aware toggle button.
- When every part is selected, the button reads **«Снять все»**; after clearing the selection it immediately changes to **«Выбрать все»**.
- If the user manually changes individual part checkboxes, the button text and screen-reader accessible name are synchronized with the actual selection state.
- The action still updates 100+ parts in one operation and preserves keyboard selection via Space.

## 4.12.21 — Hidden Media Processes & Maximized Startup

- FFmpeg and FFprobe launch with Windows `CREATE_NO_WINDOW` plus a `STARTUPINFO/SW_HIDE` fallback so media processing does not flash terminal windows above the GUI on Windows 10/11.
- Hidden-process handling covers media-tool validation, duration/codec probes, conversion/splitting and loudness analysis.
- The main window starts maximized and uses the operating system work area, current monitor resolution, DPI scaling and taskbar reservation instead of a hard-coded fullscreen size.
- Restoring from the tray returns the application to the maximized layout; `DISPLAY START` diagnostics record the detected screen and Tk scaling.
- Windows EXE build scripts remain strictly pinned to **CPython 3.14.7 x64**.

## 4.12.20 — MP3-only and Complete Help Center

- Removed the M4B output path from the current application. AudioKnigi Downloader now has one final audio format: **MP3**. Legacy saved output-format values are ignored safely and are no longer exposed in the UI.
- Removed the output-format selector, M4B preview/build/tagging branches, M4B queue/resume state and M4B-specific onboarding/settings text.
- Audited the application keyboard bindings and documented the supported shortcuts in one Help Center reference: global navigation, tab switching, quality presets, search/history/parts actions, combobox keys and standard text editing shortcuts.
- Rebuilt the Help Center as a scrollable, topic-based user manual covering quick start, supported sources, simple/advanced modes, Book tab, narration choice, mini-player, downloads/duplicates/cancel, queue, history, quality, every settings group, files/metadata, backups, accessibility, shortcuts, diagnostics and recovery.
- Source validation may use a different local Python/runtime; the Windows EXE build remains pinned to **CPython 3.14.7 x64**.

### Automatic duplicate protection and reliable Cancel in 4.12.19

The Book tab no longer exposes a separate “Проверить скачанные файлы” action. Before a full-book download starts, the app automatically verifies existing output and compares saved metadata with the currently analyzed book. If the same book from the same source is already complete and metadata matches, a modal offers to open the folder, download again, or do nothing. This is shared by simple mode, advanced mode, and auto-download.

Cancel now has explicit one-shot UI feedback and actively closes currently streaming HTTP responses. FFprobe duration probes also observe cancellation. A blocking provider-page connection can still take until the current operating-system/network call returns, but no later download/processing stage is allowed to continue after the cancel flag has been observed.

### Stable retry source mapping and duration verification in 4.12.18

- Partial retries keep temporary source files bound to their original book-wide source slot. Retrying chapters 2, 3 and 5 therefore uses `_source_02.mp3`, `_source_03.mp3` and `_source_05.mp3` rather than renumbering the subset.
- `app.log` records DEBUG `source_mapping` events so support can reconstruct exactly which temporary source file fed each chapter.
- MP3 verification accepts up to 5 seconds of duration drift caused by playlist rounding, encoder delay/padding or VBR metadata. Large mismatches still fail verification and trigger repair/error handling.
- Windows EXE build remains pinned to CPython 3.14.7 x64.

### Bulk part selection and one-button mini-player in 4.12.17

- Advanced **Книга** tab keeps **Выбрать все** and **Снять все** directly above the parts table, so a 100-part book can be reduced to one wanted part without clearing 99 checkboxes manually.
- The bulk-selection controls follow the same busy/book availability state as selective download controls.
- The mini-player now has one primary transport button: **▶ Воспроизвести** changes to **⏸ Пауза** while audio is playing; pausing changes it back to **▶ Воспроизвести**, and pressing it again resumes from the saved current position.
- **■ Стоп** remains separate and returns the primary button to **▶ Воспроизвести**. Natural track completion does the same.
- Older internal references to `player_pause_btn` remain as an alias to the single visible play/pause button for compatibility; no second Pause button is rendered.
- Windows EXE builds remain pinned to CPython 3.14.7 x64.

### Event-bus reliability and queue-state consistency in 4.12.16

- `UIEventBus._drain()` no longer writes callback exceptions to `stderr`. Every queued UI-callback failure is routed to `app.log` with a full traceback and a privacy-safe callback label.
- The Tk `after()` pump is re-armed from `finally`, so one broken UI callback cannot permanently freeze later `self.ui(...)` status/progress/queue updates in a PyInstaller `--windowed` build.
- Per-item queue pause now preserves both the localized display text and the semantic `status_code`; `retry_pending` returns as `retry_pending` after resume instead of being flattened to `pending`.
- HTTP 404/410 recovery now has one page/playlist refresh budget per book-processing run. After that refresh, additional unavailable parts may be explicitly skipped, but another full refresh is not started.
- Release archives are produced without `__pycache__`, `.pyc`, `.pytest_cache`, build output or virtual environments. `make_source_release.py` enforces and validates those exclusions. The Windows EXE build remains pinned to CPython 3.14.7 x64.
- Source/regression tests for this release were executed in the available Linux validation environment (Python 3.13.5); Windows 3.14.7 correctness is enforced by build-script/runtime guards and must be verified by the actual Windows build.

### Full book-flow diagnostics in 4.12.15

`app.log` now records the complete lifecycle of every processed book using structured `BOOK FLOW` events. Support can see analysis, the selected narration, selected parts, source download/reuse, FFmpeg processing, verification, cover/tags, sidecars, source cleanup, history persistence and the final completion result. Detailed per-track success events use DEBUG level so the visible application log remains concise. Failures in the main download and full-MP3 workers include a full traceback.

### UX, narration choice and diagnostics in 4.12.14

- Simple mode now shows an **Озвучка** selector in the pre-download confirmation whenever the same book has multiple narrators/recordings; it uses the same variants as the advanced Book tab and re-analyzes the selected recording before download.
- Treeview tables use explicit AudioKnigi vertical/horizontal scrollbar styles so dark mode is not replaced by bright Windows/ttkbootstrap scrollbars after theme changes.
- Settings slider values stay visible next to the controls; bandwidth shows a concrete numeric value (`0 МБ/с — без лимита`, `25 МБ/с`, etc.) and event-sound volume shows percent.
- Search/simple-mode keyboard hints resize their wrap length with the available width instead of being clipped in narrow windows.
- `app.log` now records thread, module, function and line number, uses DEBUG-level file diagnostics, keeps 5 × 5 MB rotated logs, and captures full tracebacks for unhandled Tk, worker and main-thread failures. Key recoverable boundaries also log traceback context.
- All 40 Python modules were statically audited for exception handling; bare `except:` is forbidden by regression test. See `ERROR_HANDLING_AUDIT_4_12_14.md`.
- Windows EXE builds remain pinned to Python 3.14.7 x64 with the validated real FFmpeg/FFprobe bundle.

### Logic and localization hardening in 4.12.13

- Workflow status logic uses semantic state kinds rather than searching Russian words inside arbitrary messages, so status badges remain correct in Russian, Ukrainian, German and English and book titles cannot accidentally trigger error/downloading colors.
- Simple/advanced mode uses stable internal `easy` / `advanced` keys; localized labels are presentation only.
- Queue items use stable `status_code` values instead of parsing localized status strings.
- Books with 100+ parts use three-or-more digit numbering automatically (`001`, `002`, … `100`), including `{Track_Number}` templates.
- Completion size and Listen actions scan subfolders recursively, so CD1/CD2 layouts are supported.
- Accessibility Tk scheduling is marshalled to the main UI thread when called from workers.
- Drag-and-Drop hint updates include the simple-mode target, media-URL de-duplication is linear-time, and metadata fallback prefers structured JSON-LD instead of generic JavaScript `name` fields.
- Windows EXE builds remain pinned to Python 3.14.7 x64 and keep the real FFmpeg/FFprobe bundle checks.

### Safe shutdown fix in 4.12.12

- Closing the app on Python 3.14/Tk 8.6 no longer reports the benign teardown race `_tkinter.TclError: can't delete Tcl command`.
- Only this exact error is ignored, and only while the application is already shutting down; unrelated Tcl errors remain visible.
- Repeated close events are ignored after the first teardown begins.
- Session state is still written as `running: false` before the root is destroyed.

### Real FFmpeg bundle fix in 4.12.11

- Windows builds no longer embed the Chocolatey `bin\ffmpeg.exe` / `ffprobe.exe` shim launchers.
- The build resolves and validates the actual FFmpeg binaries before passing them to PyInstaller.
- At runtime bundled FFmpeg/FFprobe are probed with `-version`; a broken bundled tool is skipped in favor of a working system copy.
- This fixes PyInstaller `_MEI...\ffmpeg.exe` exits with code `4294967295` and empty stderr.

### Missing-part choice in 4.12.10

- If a direct audio file is still missing after the automatic playlist refresh, the app now asks what to do instead of always stopping the whole book.
- **Остановить загрузку** is the safe default action.
- **Пропустить часть и продолжить** skips only the affected unavailable part(s) and continues the remaining selected tracks.
- A shared missing source can map to multiple chapters; the dialog lists every affected part before skipping.
- Incomplete books finish with an explicit warning and queue status **Готово с пропуском**, so a partial download is never presented as fully complete.

### Automatic playlist refresh after HTTP 404/410 in 4.12.9

If a short-lived CDN/audio URL expires during a download, AudioKnigi Downloader now re-analyzes the public book page, obtains a fresh playlist, removes only disposable `_source/.part/.seg` files, and retries the selected parts once. A second 404/410 is reported as a genuinely unavailable media source instead of repeatedly retrying the stale address.

### FFmpeg compatibility and diagnostics in 4.12.8

- "Original quality" now uses stream-copy only when the downloaded audio stream is actually MP3.
- AAC/M4A/unknown codecs are converted to a compatible MP3 instead of failing during muxing.
- If an MP3 stream-copy still fails, the affected track is retried once with `libmp3lame`.
- Every FFmpeg invocation is written to `app.log`; failures include return code and complete stderr for diagnosis.
- Windows builds remain pinned to Python 3.14.7 x64.

### Direct folder selection in simple mode in 4.12.7

- **Шаг 3. Папка сохранения → Изменить** opens the native folder chooser immediately.
- The selected destination is shared with the advanced Book tab and saved normally; simple-mode users no longer need to open Advanced Settings just to change the folder.

### Scale migration and dropdown scrolling in 4.12.6

- A clean profile starts at **100% UI scale**. Existing profiles that still contain the legacy automatic `125%` value are migrated to 100% once.
- A migration marker prevents repeated resets: after migration, a user can manually select 125% (or another supported scale) and that explicit choice is preserved.
- Scrolling while a native dropdown is open still closes the dropdown immediately, but no longer forces the page upward. The original wheel direction is preserved.

### Default 100% scale in 4.12.3

- The clean-profile default changed from 125% to **100% UI scale** and was centralized in `DEFAULT_UI_SCALE`.
- Version 4.12.6 adds the one-time migration needed for profiles that had already persisted the old automatic 125% value.

### Audit hardening in 4.12.2

- Screen-reader polling is idempotent: rebuilding UI no longer starts duplicate 5-second probe chains, duplicate speech uses a true sliding debounce window, and root widgets no longer trigger an unnecessary empty-parent lookup.
- The first onboarding screen is fully localized in Russian, Ukrainian, German and English.
- Clipboard-link prompts are guarded against re-entry while the modal dialog is open; dependency and Drag-and-Drop state reads tolerate partially initialized hosts.
- Knigavuhe search hydrates a missing author even when a reader was already parsed, preserving author-oriented search accuracy.
- Player resume state is cleared when the user seeks back to the beginning; legacy M4A/AAC files can be opened in the system player.
- PoleKnig title selection prefers real descriptive titles over short catalogue badges, and the fallback PlayerJS parser now walks balanced nested JavaScript objects instead of splitting them with a flat brace regex.
- Empty history folders no longer fall back to the application's current working directory when looking for cover art.
- Native compatibility wrappers now convert `CTkOptionMenu.configure(width=...)` pixel widths and proxy `pack_configure` / `grid_configure` / `place_configure` through `CTkScrollableFrame`'s public viewport.

### User-friendly workflow in 4.12.0

Version 4.12.0 keeps the full advanced toolset but makes the default workflow understandable without reading a manual:

- **One universal field** on the simple home screen accepts a book title, an author name, or a supported URL. Plain text searches all three providers; a supported URL opens that book directly.
- The mode switch is named **Простой режим / Расширенный режим**, with a separate **Расширенные возможности** button on the simple dashboard.
- First-run onboarding starts with two clear choices — search by title/author or use an existing link — and explains the basic three-step flow.
- Simple-mode failures are recovery cards with a next action such as **Повторить**, **Найти книгу**, **Помощь**, or **Перейти к доступной озвучке** instead of dead-end dialogs.
- Narration choices can show **доступно / недоступно** when the provider exposes that state; restricted recordings offer a direct jump to the first available alternative.
- Search tables hide raw URLs by default and show a concise **Статус** column; the URL remains available through the context menu.
- Selecting a book shows a pre-download summary with title, author, reader, number of parts, and destination folder before the user confirms **Скачать книгу**.
- Progress uses human workflow phrases such as **Получаем информацию о книге**, **Скачиваем книгу**, **Проверяем файлы — 12 из 48**, and **Готово**.
- The completion card states how many parts were downloaded and the destination folder, with direct actions to listen, open the folder, or find another book.
- **F1** opens help for the current workflow (search, queue, settings, files/history, or downloading).

The advanced tabs, queue, detailed chapter controls, templates, logs, and existing accessibility behavior remain available.


### Audit hardening in 4.9.9

- AudioKnigi reader names are cleanly separated from the following genre label.
- Missing downloaded/history folders are reported instead of silently recreated.
- Narration search cache objects are not mutated during book analysis.
- Stale off-screen window geometry and legacy `px` width strings are handled safely.

### Audit hardening in 4.9.8

- Restores the queue pause button label after a run finishes or is cancelled.
- Search relevance recognises ASCII, en dash and em dash author/title separators.
- History serialisation normalises optional `None` metadata to empty values.
- Cover rendering accepts either raw image bytes or an already decoded Pillow image.
- Easy mode uses its visible drag-and-drop hint as the actual DnD target.
- Quality-card wrapping avoids redundant configure cycles and layout timer cleanup uses the owning widget.

### Reliability hardening in 4.9.7

- Full-source audit confirmed that the reported truncated `actions.py`, `player.py`, `tray.py`, and `settings_tab.py` errors were artifacts of incomplete source excerpts, not errors in the archive.
- Knigavuhe parsing is more defensive around `BookController.enter(...)`, old narration layouts, and future semantic-tag changes.
- Supported links without an explicit scheme are normalized safely.
- First-run and Help Center text now follows the selected RU/UK/DE/EN interface language.
- Partial UI/recovery states no longer fail when an optional Tk variable or image cache has not been initialized.

### Search behavior in 4.9.6

For `audioknigi.com.ua`, the reader column is populated for both single-recording and multi-recording books. Detail metadata is fetched in parallel before duplicate recordings are merged.

- Search results include **Озвучек** — the number of available recording variants.
- `audioknigi.com.ua`: separate pages of the same Title + Author are collapsed into one logical row; their narrators remain selectable after opening the book.
- `knigavuhe.org`: the current ``Другие озвучки`` block is counted from the detail page, including multiple distinct recordings by the same reader.
- Reader labels are resolved from alternative pages when needed; duplicate reader names are shown as `вариант 1`, `вариант 2` instead of anonymous `Вариант N`.
- Default download folders add the reader/variant suffix when a book has multiple recordings, preventing one narration from overwriting another.

### Search behavior in 4.9.4

- `audioknigi.com.ua`: **Название** contains only the book title and **Автор** contains the author.
- `knigavuhe.org`: current search cards are read structurally as **Название / Автор / Чтец**.
- Knigavuhe search pagination is followed automatically. The desktop table keeps a 100-result ceiling, which currently corresponds to up to 10 Knigavuhe pages at 10 books per page.
- Results matched only by a reader/performer are omitted; alternative recordings of the same book are selected later via **Озвучка**.

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
- `audioknigi/downloader.py` — provider dispatch, resumable HTTP Range downloads, Auto-Chunker, FFmpeg/FFprobe processing.
- `audioknigi/knigavuhe.py` — Knigavuhe search and BookController/legacy MP3 parsing.
- `audioknigi/poleknig.py` — PoleKnig search, pagination, metadata and PlayerJS playlist parsing.
- `audioknigi/sources.py` — supported-site URL recognition and normalization.
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
py tests/test_knigavuhe_490.py
py tests/test_audit_4812.py
py tests/test_audit_4813.py
py tests/test_audit_4814.py
py tests/test_audit_4819.py
py tests/test_audit_4820.py
py tests/test_audit_4821.py
py tests/test_audit_4822.py
```

GitHub Actions runs the complete test suite on Windows.

## Version history
- **4.8.21** — hardened normalization-mode validation while preserving legacy `single` loudnorm, made onboarding focus and early scale application component-safe, hardened malformed cover-cache keys and Settings trace ownership, normalized scrollregion comparison, and regression-tested destroy cleanup semantics without reintroducing Tk `<Destroy>` recursion.
- **4.8.20** — made queue startup/retry single-worker and item-identity-safe; made the Range size threshold configurable and persistent; clarified byte-rate metrics; synchronized the player “now playing” label; made wizard-close persist “skip onboarding”; hardened cover hashing and Text copy/cut; and replaced tab `<Destroy>` bindings with safe destroy wrappers to preserve cleanup without Tk teardown recursion.
- **4.8.19** — cancelled accessibility polling callbacks on shutdown; added tooltip lifecycle cleanup to Main/History/Easy views; made History double-click operate only on the row under the pointer; reused the shared live `StringVar` helper in EasyHome; made Settings rebuild traces/autosave idempotent and reduced redundant wrap recalculation; normalized secret masking to `*`; improved queue drag beyond the first/last row; made tray unavailability explicit in Settings; refined search tie-breaking toward shorter equally relevant labels while preserving inline punctuation.
- **4.8.18** — hardened backup/history validation, queued tray notifications during icon restart, localized duplicate-book choices, added standalone-safe Actions translation fallback and i18n format warnings, disposed Settings tooltips, unified guarded settings saves, made scale selection immediate, removed the Tk width 15/16 discontinuity, and made Linux edit shortcuts logical-layout-first with Cyrillic and X11 fallbacks.
- **4.8.17** — unified live `StringVar` creation across Settings, Queue and Search tabs; retained adaptive hotkey wrapping, deterministic queue drag bindings and tooltip cleanup; made quality-card descriptions responsive at 200% DPI.
- **4.8.16** — hardened the embedded player against SDL startup false-stops; made lazy queue locking race-safe; added CTk light/dark color-pair support; preserved year `0` in templates; normalized Linux wheel scrolling; hardened Queue/Search Tcl-variable lifecycle and tooltip cleanup; removed additive duplicate queue drag bindings; and made Settings shortcut-help wrapping responsive.
- **4.8.15** — verified the reported source truncations were false positives; isolated context-part MP3 mode so it no longer leaks into later downloads; synchronized paused seeking in the embedded player; routed M4B/M4A/AAC to the system player; localized the M4B first-run switch; hardened unfinished-scan and completion UI teardown; expanded the CTk compatibility API (`configure(variable=...)`, switch select/deselect/toggle, progress get, tab delete, geometry info proxies); removed 500 ms scroll-tree polling in favor of creation-time ancestor notification; normalized macOS trackpad scrolling/Command-key undo behavior; preserved inactive button styles; and hardened tooltip unmap behavior.
- **4.8.14** — hardened settings/runtime numeric parsing, made Tk DPI scaling absolute instead of cumulative and responsive at high scale, serialized screen-reader backend refresh/announcements, added classic `tk.*` value/state accessibility and wrapper-native paths, hardened clipboard/completion/queue/resume/history edge cases, preserved falsey log values, stabilized player shutdown/seeking and pygame compatibility, declared `plyer`, disabled threaded pystray on macOS, and added 4.8.14 audit coverage.
- **4.8.13** — added debounced autosave for folder/track templates and Audiobookshelf text fields, hardened SettingsTab Tk-variable creation so it never silently returns `None`, rooted friendly Settings variables in the application Tcl interpreter, documented/labelled the Queue Drag-and-Drop target, and made Search double-click select the exact row under the pointer before opening it.
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
