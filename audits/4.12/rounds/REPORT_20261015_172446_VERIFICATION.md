# AudioKnigi Downloader 4.12.42 — audit of report dated 2026-10-15 17:24

Baseline: `Round90-full-check-20261013.zip` (the most recent complete source archive from the earlier review), compared with the corresponding current GitHub `main` files before editing. All changes below are minimal, compatibility-focused and included in this source snapshot.

## Findings, one by one

1. **Legacy string booleans in `config/settings.py`: CONFIRMED, FIXED.** `bool("false")` is true. The existing `_safe_bool` helper now handles legacy `normalize_audio`, including `"false"`, `"off"`, and `"0"`. This also fixes `AppSettings["normalize_audio"]` assignment through normalization. Tests cover both enabled and disabled aliases.
2. **Dictionary tracks in `download/probe.py` and expired-media error reporting in `download/book_flow.py`: CONFIRMED, TARGETED FIX.** The shared-source timeline check now reads `file`, `start`, `end`, `index` from Mapping or object. The damaged-source exception uses Mapping-aware `index` and `file`. A regression checks dictionary chapters with a truncated common audio source. **Scope:** other paths in book_flow may still assume concrete Track objects; this change does not promise arbitrary dictionary objects work everywhere in the downloader.
3. **FFmpeg `-t` with `-filter_complex`: NOT A BUG AS STATED.** In the actual command the flag appears after inputs, before the output, where FFmpeg treats it as an output duration limit. Verified against installed FFmpeg 7.1.5 using a generated WAV and filter_complex; output was 0.50 seconds, exit code 0. No change.
4. **`ThreadPoolExecutor.shutdown(cancel_futures=True)` on Python 3.8: NOT APPLICABLE to the supported project runtime.** The project uses Python 3.10+ syntax; removing the argument would not make the project runnable on Python 3.8. No change.
5. **Repeated `runtime_exact.json` keys: NOT REPRODUCED.** Parsed with `object_pairs_hook` detecting duplicate keys; there are 140 unique keys and zero duplicates at this revision. No change.
6. **Two newlines in the translated disk-space regex: PRESENT, DISPLAY DECISION.** The regex accepts one or more source newlines; localized error dialogs intentionally preserve a paragraph break. This is a formatting difference, not a crash or incorrect capture. Retained to avoid changing existing localization contracts without UI review.
7. **German `Wiedergabeliste` versus `Playlist`: CONSISTENCY IMPROVEMENT, APPLIED.** Standardized the runtime prefix translation to `Playlist`.
8. **`Отменить` translated as Undo/Rückgängig in legacy literals: CORRECT FOR ITS ACTUAL USE.** Its code usage is the text editor's Undo action in `qt/localized_context_menu.py`, whereas operation cancellation uses other message keys. Changing it to Cancel would break the meaning. No change.
9. **Other Python 3.8 `cancel_futures` cases: NOT APPLICABLE**, same as #4. No change.
10. **`library_service.scan_unfinished` skips corrupt track selections: REAL LIMITATION, NO UNSAFE AUTO-REPAIR.** Turning malformed/empty selections into `None` would mean *download the whole book*, which can cause unintended downloads. Preserve strict semantics pending an explicit recoverable-manifest UX design; backup damaged resume data when appropriate.
11. **Track Path serialization in `queue_service._item_to_dict`: NORMAL MODEL PATH WORKS.** `Track.to_dict()` normalizes `Path` to `str`. Verified JSON round trip with a `Track(local_path=Path(...))`. External third-party dataclasses without `to_dict()` remain a separate compatibility edge case.
12. **Legacy string boolean in `queue_service.task_from_dict`: CONFIRMED, FIXED.** Uses `_optional_persisted_bool` to avoid interpreting `"false"` as enabled. Covered by tests.
13. **Python 3.8 cancellation in provider modules: NOT APPLICABLE**, same as #4.
14. **Cloudflare client socket close: NO LEAK CONFIRMED.** `socketserver.BaseRequestHandler` and `ThreadingTCPServer` own and close the client request socket after handler execution. Upstream socket already closes in `finally`. Force-closing it a second time risks unintended interaction with the handler lifecycle.
15. **Duplicate files when `delete_source=False`: INTENTIONAL.** One is the output MP3, the other the retained original source; changing this would violate an explicit user preference.
16. **`MappingDataclass.to_dict()` Path conversion: VERIFIED.** Also tested through queue JSON serialization. No change.
17. **`WorkerUiRelay` and GUI thread: STATIC REVIEW / PRIOR COVERAGE ONLY.** No new regression established from this report; actual Qt queued connections need PySide6/Windows acceptance.
18. **QMediaPlayer cleanup and sound worker: STATIC REVIEW ONLY.** No reproducible defect furnished; Windows resource behavior remains unverified in this Linux environment.
19. **Accessibility focus handling, announcements and accessible IDs: STATIC REVIEW ONLY.** User-visible NVDA/JAWS behavior still requires Windows.
20. **Missing-media user decision timeout: INTENTIONAL 30-minute limit with cancellation checks.** No change.
21. **Player settings updated from UI controls: STATIC REVIEW.** Existing delayed persistence of volume and separation of worker state remain in place.
22. **Media seek resume: STATIC REVIEW.** Existing seekable check is sensible; actual WMF/DirectShow behavior remains a Windows-only acceptance check.
23. **QFocusFrame stylesheet and dynamic theme: STATIC REVIEW.** No new actionable defect established.

## Validation

- `pytest` on Linux, including the new October 15 regression module, was split into two complete groups to avoid unnecessary live-I/O stalls: **811 passed** in unit/integration tests excluding `test_accessibility.py` and `test_providers.py`; **156 passed** in `test_providers.py`; **967 passed, 0 failed** combined.
- An earlier focused check of settings, localization, privacy, queue/history, October 13 and October 15 regressions: **310 passed** (subset of the above, not an additional independent total).
- `python -m compileall -q audioknigi`: passed.
- `ffmpeg` output-duration placement with `-filter_complex`: passed locally.
- `runtime_exact.json` duplicate check: passed.
- `PySide6` unavailable; Qt accessibility tests, NVDA/JAWS acceptance, Windows Media Foundation playback and Windows socket behavior **not tested**.

## Remaining follow-up recommendations

Maintain strict 'invalid selection != entire book' semantics for any corrupted resume manifests. When testing on Windows, prioritize NVDA/JAWS announce/focus, tray shutdown, audio resume, and keyboard context menus. Review whether third-party plugin dataclasses with `Path` values require a generic serializer; production Track/Book models do not.
