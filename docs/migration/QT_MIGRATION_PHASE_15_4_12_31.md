# Qt Migration Phase 15 — data-contract and legacy cleanup

Phase 15 is a Qt-only maintenance release driven by a detailed source audit after the successful Phase 14 Windows accessibility startup self-test.

## Fixed

- Canonicalized `Book.cover_cache` as `(bytes, mime_type)` while keeping backward compatibility with old bare-byte queue snapshots.
- Qt book preview and queue cover rendering now extract image bytes correctly.
- Queue persistence now stores both `cover_cache_b64` and `cover_cache_mime`; restored covers remain valid for ID3/APIC embedding.
- Removed the dead `AudioKnigiApp` export from `audioknigi.__init__`.
- Removed the duplicate obsolete `_choose_output_dir` definition.
- Replaced the synthetic `_M` MIME object in queue URL drop handling with reusable string normalization.
- Removed retired Tk-only window-geometry helpers from `core.py`.
- Expanded the static accessibility contract to 125 required persistent controls and 8 dynamic modal IDs.
- Added regression coverage for cover round-trips, old queue snapshots, package API cleanup, accessibility coverage and retired Tk geometry APIs.

## Verification

- Active Qt-only tests: 26/26 PASS.
- Strict full parity: 61/61 PASS after legacy retirement.
- Qt import audit: 39 reachable project modules, 0 legacy frontend paths.
- `compileall`: PASS.

The Windows accessibility self-test must be rerun for Phase 15 because the required persistent control contract increased from 90 to 125 controls.
