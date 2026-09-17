# AudioKnigi Downloader


### Звуки событий

Начиная с 4.10.2 программа поддерживает языковые пакеты коротких звуковых подсказок. В 4.10.4 английский пакет полностью покрывает все 17 зарегистрированных событий; при английском интерфейсе для каждого события используется английская запись. Звуки можно отключить, изменить громкость и проверить в **Настройки → Звуки программы**; они используют отдельный канал и не заменяют файл во встроенном мини-плеере.

### Поддерживаемые сайты
- `audioknigi.com.ua`
- `knigavuhe.org` — поиск через `/search/?q=...`, загрузка доступных книг по страницам `/book/...`.
- `poleknig.com` — поиск через `?q=...` плюс автоматическое раскрытие пагинации каталога найденного автора `/authors/<id>?p=...`, страницы книг `/books/<id>`, открытые плейлисты PlayerJS.

Поиск во вкладке «Поиск» работает сразу по трём источникам. Страницы, удалённые/ограниченные самим сайтом по просьбе правообладателя, программа не обходит.

**Current version: 4.12.12**





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
- Player resume state is cleared when the user seeks back to the beginning, and M4B/M4A/AAC are consistently opened in the system player from either playback entry point.
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

The advanced tabs, queue, M4B tools, detailed chapter controls, templates, logs, and existing accessibility behavior remain available unchanged.


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
