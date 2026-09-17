# Qt Migration Phase 17 — audit follow-up hardening

Phase 17 follows the four post-Phase-16 audits plus the explicit queue/search/theme review. It keeps the tree Qt-only and preserves the 61/61 capability inventory while tightening invariants that are difficult to cover with UI-only testing.

## Confirmed fixes

- Legacy flat queue snapshots remain visible as `needs_analysis`, but are now structurally non-runnable even if a UI status is accidentally changed to `retry`.
- Qt Retry/Resume/Pause-toggle explicitly reject tasks that lack an analyzed Track snapshot.
- Queue completion distinguishes true completion from paused/error/re-analysis work that still needs user action.
- Search dedupe uses `normalize_supported_url`; Audioknigi trailing-slash duplicates collapse to one identity.
- Audioknigi metadata removes an already-known author prefix from a combined `Author - Title` label.
- Knigavuhe variant hydration accepts and checks `cancel_event`; BookAnalysisService passes its event through.
- `MappingDataclass` is now a real read-only `Mapping`; field names are cached per model class.
- HTTP pool overflow is non-blocking (`pool_block=False`).
- Parked segmented-download workers return cleanly on cancellation instead of printing unhandled daemon-thread tracebacks.
- Stage-4 verify/tag progress uses `status_checking_progress` localization.
- Invalid `--qt-focus-trace` arguments are reported through crash-report/stderr and return code 2 before QApplication creation.
- Known source URLs without a scheme but with an explicit port are accepted.
- Event-sound language changes dispose old players; Windows system beeps run through a single background executor.
- Manual output-dir edits are synchronized between Settings, Book and Easy mode.
- Removing the final queue row moves keyboard focus to the queue URL-add control.
- Theme switching tracks the applied style explicitly instead of relying on style `objectName()`.
- AccessibleAnnouncer preserves the first polite operation status and coalesces subsequent updates.

## Audit items intentionally not changed

- FFmpeg `-ss` before `-i` plus `-t` as an output option is valid: `-t` means output duration, not an absolute source timestamp.
- `.assembling` cleanup already runs after Python unwinds the `with open(...)` context, so the file handle is closed before the outer `except` unlinks it.
- A final compact PlayerJS chapter with `start` and no `end` is intentionally split from its start to EOF.
- The reported IPv6 proxy failure was not reproduced from the current parser; numeric IPv6 is recognized and CONNECT bracket syntax is handled.
- The player seek audit itself confirms `load()` resets `_resume_after_stop_ms`; no cross-file seek leak exists.

## Release gates

- active Qt-only tests
- strict full parity: 61/61
- Qt import boundary: zero legacy paths
- `compileall`
- final Windows offscreen accessibility self-test and NVDA/JAWS acceptance remain required for the built EXE.
