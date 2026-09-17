# Audit — Qt Migration Phase 9

Date: 2026-09-06

## Scope

Feature-parity audit between the stable Tk frontend and the PySide6/Qt Widgets migration branch. The audit focused on user capabilities, persisted state and downloader behavior rather than pixel/implementation identity.

## Findings and fixes

1. Added a formal parity matrix in `audioknigi/qt/feature_parity.py` and made critical parity a regression-tested invariant.
2. Ported advanced downloader settings, templates and Audiobookshelf connection testing to Qt.
3. Ported narration-variant selection and first-available narration recovery.
4. Added supported clipboard-URL detection/paste flow and legacy action hotkeys.
5. Added GUI-independent unfinished `resume.json` discovery and Qt continuation workflow.
6. Added history open/redownload/delete/clear plus JSON/CSV export.
7. Added validated backup/restore for settings, history, player positions and Qt queue.
8. Added direct URL→queue and clear-queue actions.
9. Added per-track context actions.
10. A second parity pass found the legacy “Одним MP3” capability was still functionally missing. Implemented it in the GUI-neutral `DownloadService` using the mature resume/Range/cancel path and added a real FFmpeg/local-HTTP integration test.
11. Extended the frozen accessibility contract to the new Phase 9 controls.

## Intentional/non-blocking differences

Not counted as critical parity blockers:

- old separate Easy Mode — Qt intentionally uses one consolidated workflow;
- queue drag-and-drop — accessible Up/Down controls provide the same ordering capability;
- legacy MP3 event voice sounds — deferred to avoid bringing `pygame` back into the clean Qt runtime;
- full Qt localization ru/uk/de/en — deferred;
- decorative cover/card presentation — deferred.

## Regression result

- Full active suite: **580/580 passed** in non-overlapping groups.
- Qt migration Phase 1–9: **68/68 passed**.
- Static Qt import graph: **32 project modules, 0 legacy frontend paths**.
- Full-MP3 real download integration: pass.
- `compileall`: pass.

## Stable Tk branch

Fourteen key legacy files/build manifests were compared byte-for-byte against Phase 8 and all are unchanged. No Phase 9 feature was implemented by patching the stable Tk UI.

## Conclusion

**Critical functional parity is achieved.** Qt is now a promotion candidate rather than a feature-incomplete preview. Final promotion remains blocked only by the Windows frozen-build and live NVDA/JAWS acceptance gates defined in Phase 8.
