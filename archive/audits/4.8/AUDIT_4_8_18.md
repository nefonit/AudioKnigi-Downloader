# Audit 4.8.18

This release reviews the reported 4.8.17 findings against the actual shipped source and hardens persistence, tray lifecycle, localization, settings cleanup, and Linux edit shortcuts.

## Reported critical findings that were false positives

- `ActionsMixin.download_full/_full_worker` is complete; `actions.py` compiles and contains the complete ID3 block.
- `SearchMixin` is complete; `search.py` compiles without an EOF/SyntaxError.
- `AudioKnigiApp.t()` exists. 4.8.18 additionally gives `ActionsMixin` a safe `_tr()` fallback so the mixin no longer depends on that host method for its three translated messages.
- `_player_position_key()` and `_player_select_current()` are implemented by `PlayerMixin`; `AudioKnigiApp` inherits `PlayerMixin`.
- `Track.file` is the remote audio source URL used by `DownloaderMixin`, not the local output filename.
- The `prismatoid` distribution continues to use the runtime Python module `prism`; no import change was made.
- The SDL false-stop condition already had a startup grace in 4.8.17; the existing player regression test remains green.

## Confirmed fixes

- Deep history validation: malformed non-mapping records are rejected during backup restore, local corrupted history is sanitized at startup, and history rendering re-sanitizes before touching `Treeview`.
- Backup restore now parses and validates all JSON members before writing any of them, preventing a partial restore when a later member is malformed.
- `_add_history()` no longer searches the current working directory for `cover.jpg` when the book folder is empty.
- Tray notifications sent while an icon generation is starting/restarting are queued and delivered after the native icon becomes ready instead of being silently lost.
- Duplicate-book dialog action hints are localized in RU/UK/DE/EN.
- i18n formatting errors remain non-fatal but now emit a developer warning instead of failing silently.
- `context_copy_track_url()` validates the remote source URL before copying and uses clearer status text.
- `SettingsTab` now explicitly disposes its tooltip bindings on frame teardown in addition to cancelling traces/autosave timers.
- Technical dropdown persistence is routed through one guarded `_save_now()` helper.
- Selecting a UI scale now applies it immediately; the explicit Apply button remains as a keyboard/fallback action.
- The historical Tk width conversion no longer has the 15-character -> 2-character discontinuity: only the explicit 0/1 compatibility values are native character widths, while >=2 remains historical pixels.
- Linux edit shortcuts prefer logical keysyms (Dvorak/Colemak-safe), understand standard Cyrillic keysyms, and use X11 physical codes only as a final fallback.
- Simplified the search token regex (`\w+`) and removed unreachable history-cover cache identity fallback work.
- `LANGUAGES` is imported normally by storage instead of being hidden inside a broad local `try/except`.

## Deliberately unchanged

- The dynamic attribute names used by Settings trace installation are technical debt, not a runtime defect. They remain because replacing the already regression-tested trace lifecycle would create unnecessary risk.
- The player seek path keeps a defensive repeated file check; it is harmless and protects independently callable helpers.
- `type(None)` inside the primitive serialization tuple is valid Python and not a correctness issue.
- PowerShell toast remains a best-effort Windows fallback behind `plyer`; automatic AUMID registration is not introduced for a portable unpacked Python application.

## Verification

- `compileall`: pass.
- 131/131 collected pytest tests pass in fresh Xvfb/Tcl groups.
- 27 script-style smoke/audit modules pass when executed directly.
- Python/Tk recursion, DnD, timing columns, accessibility, themes, Linux Cyrillic shortcuts and 100-200% UI tests remain green.
