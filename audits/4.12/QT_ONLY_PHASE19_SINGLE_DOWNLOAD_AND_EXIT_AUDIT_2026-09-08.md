# Qt-only Phase 19 audit disposition — 2026-09-08

## Confirmed

- **Single-download session regression:** confirmed and fixed. `_download_single()` had `session.get()` with no local `session`.
- **Crash-safe fallback queue persistence:** confirmed as a recovery gap. Added `request_changed` callback and immediate Qt queue persistence.
- **Loudnorm brace-regex fragility:** hardened with structural JSON decoding.
- **System-sound sentinel accounting:** confirmed; sentinel now reaches `task_done()`.
- **Qt media child lifetime:** hardened with `deleteLater()` on cached players/outputs.
- **Nested standard dataclass serialization:** confirmed and fixed.
- **Direct create_application argv sanitation:** hardened.
- **Multiple-worker close lifecycle:** centralized cancellation/polling replaces repeated `finished.connect(self.close)`.
- **UI re-enable during exit:** cleanup slots now return after clearing worker references when exit is pending.
- **PoleKnig search timeout:** reduced from `(10, 35)` to `(6, 15)`.

## Already fixed before Phase 19 / repeated findings

- strict `is_supported_url()` book-path validation
- `task_requires_analysis` definition/export
- queue serializer tolerance for `tracks=None` / `narration_variants=None`
- output-directory field synchronization
- FFmpeg process unregister in `finally`
- Range subrequest HTTP-session reacquisition

## Rejected or not evidenced

- `text/x-python` as a physical source filename: false; it is dump metadata.
- `_split_track.out` UnboundLocalError: no reachable path.
- Knigavuhe `cancel_event` keyword TypeError: signatures already match.
- PoleKnig slug URLs as a current canonical format: not evidenced by the live site; current book pages use numeric IDs.
- final compact shared-source item `duration=None` as inherently wrong: without a later marker or separate authoritative endpoint, EOF is the only source-defined boundary.
- proxy TIME_WAIT as a Python socket leak: not a valid diagnosis.
