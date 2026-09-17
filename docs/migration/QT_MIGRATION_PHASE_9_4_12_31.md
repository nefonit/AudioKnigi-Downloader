# Qt Migration Phase 9 — Critical Functional Parity Audit

Date: 2026-09-06

## Goal

Compare the stable Tk interface with the staged PySide6/Qt Widgets interface capability-by-capability, close the remaining blocking feature gaps, and record intentional/non-blocking differences explicitly rather than claiming pixel-for-pixel parity.

The stable Tk launcher remains available and unchanged. Phase 9 does **not** switch the default launcher yet; Windows NVDA/JAWS acceptance from Phase 8 is still a promotion gate.

## Result

**Critical functional parity is complete.** The Qt branch now covers every capability classified as required for the primary day-to-day workflow. A formal parity matrix lives in `audioknigi/qt/feature_parity.py` and is regression-tested.

The matrix deliberately distinguishes:

- `native` — capability is available in the Qt workflow;
- `intentional-difference` — the same user goal is served by a different, accessibility-friendly workflow;
- `deferred` — non-blocking presentation/localization extras that do not prevent normal use.

## Phase 9 additions

### 1. Advanced downloader settings

Qt now exposes the operational settings that previously existed only in the legacy UI:

- naming mode;
- audio preset/quality;
- normalization mode;
- segment count and segmented-download threshold;
- automatic chunk threshold;
- bandwidth limit;
- ID3/cover embedding;
- sidecar metadata;
- temporary/source cleanup;
- parallel processing for a shared source;
- custom folder and track filename templates.

The settings continue to use the shared persisted settings schema and feed the headless `DownloadService` rather than a Tk widget adapter.

### 2. Audiobookshelf integration

Qt now includes:

- enable/disable refresh after download;
- server URL;
- API key;
- library ID;
- connection test and library lookup.

The API key editor is marked as a secret field for accessibility metadata.

### 3. Narration variants

Books with multiple available recordings now expose a Qt narration selector. The selected variant can replace the current analyzed book without routing through legacy Tk controls.

A dedicated **first available narration** action is also present for blocked/unavailable variants.

### 4. Clipboard-supported URL workflow

Qt can paste the current clipboard URL directly into the book editor and can react when the application becomes active with a supported audiobook URL in the clipboard.

Legacy keyboard parity for the main navigation/action gestures is retained, including `Ctrl+D`, `Ctrl+Q`, `Ctrl+H` and `Escape` alongside the Phase 8 shortcuts.

### 5. Unfinished-download recovery

`audioknigi/services/library_service.py` adds a GUI-independent `resume.json` scanner.

Qt can discover unfinished book folders, reconstruct the saved URL/selected indices/download settings and continue the operation through the same analysis + headless download path. Existing `.part`/Range resume behavior remains owned by the mature downloader core.

### 6. History actions and export

The Qt history tab now supports:

- open downloaded folder;
- download the book again;
- delete one history entry;
- clear history;
- export JSON;
- export CSV.

History import/export helpers remain GUI-independent.

### 7. Backup and restore

Qt can create and restore a ZIP backup containing the currently available shared application state:

- `settings.json`;
- `history.json`;
- `player_positions.json`;
- `qt_queue.json`.

Restore validates every known member **before** overwriting current files. A malformed backup therefore cannot partially replace valid settings/history first and fail afterward.

### 8. Queue parity

Phase 9 adds:

- URL → queue workflow without first manually building a queue item;
- clear queue action;
- preservation of the Phase 4 pause/resume/retry/priority/reorder behavior.

Drag-and-drop reorder is intentionally not required for parity because the explicit **Up/Down** controls are keyboard- and screen-reader-friendly and provide the same ordering capability.

### 9. Track context actions

The analyzed-track table now provides contextual actions for a single part:

- download the selected part only;
- play/open a downloaded part;
- open the current book folder;
- copy the selected media URL.

### 10. “One MP3” capability

A second audit pass found a real blocking omission: the legacy **Одним MP3** action for books whose chapters share one physical source file.

Phase 9 adds this to the headless downloader itself rather than calling `ActionsMixin`.

`DownloadService.download_full_mp3()`:

- requires exactly one shared source URL across the analyzed tracks;
- uses the existing resume/Range/cancel path;
- writes one final `<Book title>.mp3`;
- applies ID3/title/author/cover metadata when enabled;
- writes the normal history record;
- returns the target file through `DownloadResult.target_file`.

A real integration regression generates a valid MP3 with FFmpeg, serves it over a local HTTP server, downloads it through the headless engine and verifies the produced file/history.

## Formal parity matrix

### Native / critical workflow

- three-source search;
- book analysis;
- narration variants;
- selected-track download;
- one-file full MP3 download when supported;
- per-track actions;
- `.part` / `resume.json` recovery;
- persistent queue, pause/resume/retry/priority;
- direct URL queueing and queue clear;
- history actions and JSON/CSV export;
- backup/restore;
- advanced download settings;
- templates;
- Audiobookshelf;
- clipboard workflow;
- Qt Multimedia player/resume positions;
- native Qt tray;
- Light/Dark/System themes;
- native Qt accessibility contract.

### Intentional differences

- **Legacy Easy Mode:** Qt uses one consolidated workflow instead of maintaining two duplicate screen hierarchies.
- **Queue drag-and-drop:** explicit Up/Down controls are retained because they are more deterministic for keyboard/NVDA/JAWS users.

### Deferred, non-blocking

- legacy MP3 event voice sounds (`pygame` is intentionally not reintroduced into the clean Qt runtime);
- full ru/uk/de/en Qt localization;
- decorative legacy cover/card presentation.

These are documented as deferred rather than silently counted as finished.

## Accessibility contract

The Phase 8 frozen accessibility self-test was extended to cover the new persistent interactive controls, including narration, resume, full-MP3, history actions, queue URL/clear, advanced settings, Audiobookshelf and backup/restore controls.

No custom Tk/Prism/FocusIn bridge is introduced into the Qt runtime.

## Stable Tk protection

The following files were compared byte-for-byte against Phase 8 and are unchanged:

- `audioknigi_gui.py`;
- `audioknigi/app.py`;
- `audioknigi/actions.py`;
- `audioknigi/accessibility.py`;
- `audioknigi/ui_kit.py`;
- `audioknigi/player.py`;
- `audioknigi/queue_manager.py`;
- `audioknigi/tray.py`;
- `audioknigi/downloader.py`;
- `audioknigi/storage.py`;
- `requirements.txt`;
- `build_exe.bat`;
- `build_exe_fixed.bat`;
- `build_ci.ps1`.

## Verification

- Complete active repository suite executed in non-overlapping groups: **580/580 passed**.
- Qt migration Phase 1–9 focused suite: **68/68 passed**.
- Real FFmpeg + local HTTP integration test for the new full-MP3 engine: pass.
- Static Qt import audit: **32 project modules reachable, 0 paths into the legacy Tk frontend**.
- Python compile checks: pass.

The Linux work environment still cannot perform the final Windows frozen-build/NVDA/JAWS speech acceptance. Those remain mandatory before changing the default launcher.

## Promotion status

Phase 9 changes the project status from **feature-incomplete Qt preview** to **critical-functional-parity Qt candidate**.

Do not make Qt the sole/default launcher until the Phase 8 Windows gates pass:

1. Qt EXE build succeeds;
2. runtime frozen self-test reports `OK`;
3. accessibility frozen self-test reports `OK`;
4. Playwright → Edge frozen self-test reports `OK`;
5. NVDA acceptance matrix passes;
6. JAWS acceptance matrix passes.
