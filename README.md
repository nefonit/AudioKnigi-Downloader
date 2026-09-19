# AudioKnigi Downloader 4.12.42 — Qt-only

AudioKnigi Downloader is a Windows-focused accessible PySide6/Qt application for searching, analyzing, downloading, organizing, and listening to audiobooks.

> **Runtime status:** Qt-only. The retired Tk/ttkbootstrap frontend is not part of the active source tree and `run.bat` has no legacy fallback.

## Supported sources

- `audioknigi.com.ua`
- `knigavuhe.org`
- `poleknig.com`

All three sources implement the common `SourceProvider` contract. Search, analysis, narration variants, resumable downloads, selected chapters, full-MP3 mode, history, queue, metadata/covers, and the built-in player are implemented in the GUI-independent `audioknigi` package where possible.

## Quick start from source

Requirements:

- Python 3.11+ for source/runtime compatibility
- Microsoft Edge for the Playwright fallback used by protected/dynamic pages
- FFmpeg and FFprobe in `PATH`, unless using a packaged build that bundles them

```powershell
py -m pip install -r requirements.txt
py audioknigi_qt.py
```

The normal Playwright path launches the installed Microsoft Edge channel; it does not require a separate Chromium download. On Windows, `run.bat` is the normal launcher. It prefers the packaged Qt executable when present and otherwise starts `audioknigi_qt.py`.

## Windows build

```powershell
py -m pip install -r requirements-qt-build.txt
.\build_qt_exe.bat
```

`requirements-release.txt` is the pinned dependency baseline used for reproducible release work. Source/runtime compatibility is Python 3.11+, while the official Windows CI/release toolchain is intentionally pinned to CPython 3.14.7 x64. The normal CI also exercises Python 3.11 so the minimum supported version is tested. The PyInstaller build explicitly includes `assets/` and the external `audioknigi/locales/*.json` catalogs.

Before release, the exact EXE should pass the Windows runtime/accessibility checks described in `docs/accessibility/ACCESSIBILITY.md` and `tools/qt_windows_acceptance.py`.

## Main features

- Multi-source search through a common provider registry, including narration variants.
- Selected-chapter and full-book downloads.
- HTTP resume and segmented Range downloading.
- FFmpeg/FFprobe conversion, splitting, loudness normalization, validation, tags, and covers.
- Persistent queue (including queued one-MP3 jobs), history, duplicate preflight, backup/restore, and CSV export.
- Built-in Qt Multimedia player with saved positions and chapter navigation.
- RU / UK / DE / EN localization loaded from external catalogs.
- Keyboard-first/native Qt accessibility for NVDA/JAWS workflows.
- System tray, media keys, clipboard link handling, templates, themes, scaling, and event sounds.
- Cloudflare DoH resolver plus localhost proxy support for browser/remote-probe DNS paths.
- One-click privacy-conscious diagnostic support ZIP from **Help → Diagnostics**.

## Architecture

The current repository is organized by responsibility instead of migration phase:

- `audioknigi/config/` — versioned settings schema and migrations.
- `audioknigi/download/` — media probe, source analysis, HTTP/range download, FFmpeg/media processing, and book flow. `audioknigi/downloader.py` is a compatibility facade.
- `audioknigi/download_engine.py` — GUI-neutral request orchestration, duplicate preflight, resume manifests and full-MP3 coordination built on the `download/` subsystems.
- `audioknigi/providers/` — common `SourceProvider` interface, adapters, and registry.
- `audioknigi/services/` — GUI-independent analysis/search/queue/library/player-position services.
- `audioknigi/diagnostics/` — redacted support-bundle generation.
- `audioknigi/locales/` + `audioknigi/i18n.py` — stable message-ID catalogs plus compatibility translation for older literals.
- `audioknigi/qt/mixins/` — focused main-window behaviors; `main_window.py` is composition/common state rather than a 4000-line controller.
- `tests/unit/`, `tests/integration/`, `tests/architecture/` — active tests grouped by behavior.
- `tests/fixtures/providers/` — deterministic sanitized source fixtures.
- `archive/` — historical tests, source variants, retired audits, and one-off migration tooling; never imported by the runtime.
- `audioknigi/qt_runtime_audit.py` — package-level runtime-boundary assertion used by source/frozen self-tests.
- `tools/` — active release and quality gates only.
- `audits/4.12/rounds/` — incremental current-branch review/fix evidence; historical material stays under `archive/`.

See `docs/architecture/PROJECT_STRUCTURE.md` for placement rules and the complete structure.

## Settings and compatibility

`settings.json` has a versioned schema. Migrations are centralized in `audioknigi/config/settings.py`; unknown keys are preserved. The historically misleading `auto_chunk_min_kbps` key is migrated to `auto_chunk_min_kbytes_per_sec` without changing the existing KB/s behavior.

## Localization

New code should use stable message IDs through `i18n.message()` / `i18n.tr()`. Existing Russian literal keys remain supported through `ui_text()` while they are migrated gradually. Catalogs are external JSON resources under `audioknigi/locales/` and are included in package/EXE builds.

## Diagnostics and privacy

**Help → Diagnostics → Create diagnostic bundle…** creates a support ZIP containing version/environment facts, redacted settings, bounded log tails, and queue status summary. API keys, cookies, passwords, audiobook media, book titles, full executable paths, and raw configured URLs are excluded/redacted.

## Testing and quality gates

Normal active checks:

```text
python -m pytest -q
python tools/full_parity_audit.py --root . --require-legacy-retired
python tools/qt_localization_audit.py
python tools/qt_import_audit.py
python tools/exception_audit.py
python tools/unused_import_audit.py
python tools/undefined_global_audit.py
python tools/historical_regression_audit.py
```

The historical-regression gate runs the archived pre-refactor suite from a temporary root. Source-shape assertions tied to the retired monolith are explicitly allow-listed, while any new failure among the historically passing tests fails the gate. This preserves behavioral regression value without forcing production code back into old file boundaries.

## Release licensing

The source tree currently does **not** declare a top-level application license. Before public distribution of a standalone executable, choose/document the AudioKnigi Downloader license and review the obligations of the exact bundled Qt, Mutagen and FFmpeg/FFprobe components. See `THIRD_PARTY_NOTICES.md` and `docs/development/RELEASE_LICENSING.md`. The release build copies these notices next to the EXE; that checklist is operational guidance, not legal advice.

## Accessibility

Persistent controls have stable accessibility identifiers, dynamic dialogs are covered by the accessibility contract, announcements are marshalled to the GUI thread, and Windows release checks include NVDA/JAWS-oriented runtime acceptance. The retired Tk-specific accessibility bridge is not part of the Qt-only dependency/runtime surface.

## Versioning and history

The Python version source of truth is `audioknigi/version.py`; runtime consumers import the consolidated metadata facade in `audioknigi/metadata.py`. Earlier migration phases remain under `docs/migration/`, `docs/history/`, and `archive/` as historical evidence only.

Release history is in `CHANGELOG.md`.
