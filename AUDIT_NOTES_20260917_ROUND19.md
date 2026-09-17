# AudioKnigi Downloader 4.12.42 — Round 19 audit follow-up (2026-09-17)

Base: Round 18.

## Confirmed fixes

- PoleKnig URL contracts are now consistent for both `-slug` and `/slug` forms. `is_supported_url()`, `normalize_supported_url()` and `poleknig._canonical_book_url()` all accept slash-slug book URLs and canonicalize them to `/books/<id>`.
- `_history_metadata_matches_book()` and sidecar duplicate checks now use `_book_field()` consistently, preserving Mapping/dict compatibility.
- `_split_track()` infers duration from the next chapter only when both chapters reference the same source file, preventing cross-file truncation/overrun in multi-source books.
- `_download_single()` now finalizes `.part` through `replace_with_retry()`, matching the Windows Defender/sharing-violation hardening already used by segmented/full-MP3 paths.
- Final source cleanup in `book_flow.py` uses `unlink_with_retry()` so transient Windows locks do not strand large temporary source files.
- The audioknigi relative `.pl.txt` extraction regex is syntactically balanced and covered by compile/tests.
- Knigavuhe fallback selection no longer immediately accepts a narrator-less candidate when the original narrator is known; it first prefers a candidate with a compatible narrator and retains the unknown-narrator result only as a last fallback.
- Easy Mode now treats ordinary search text as non-stale after a selected result has been analyzed; stale protection is applied only when the field actually contains a URL.
- Player “file not found” and “player error” dialogs now localize their titles/body through the Qt localization layer.
- F1 / the “Горячие клавиши” menu action opens the dedicated `shortcuts` help topic. Shift+F1 remains contextual help.
- Full-MP3 creation now passes `selected_indices=None`, using the documented whole-book selection contract rather than materializing every track index.

## Reviewed but not changed

- `DownloadRequest.track_index()` already accepts scalar `int`/`str`, mappings, and Track-like objects; the earlier raw-string bug was fixed in Round 17.
- `runtime_auto_chunk_min_kbps` is a compatibility alias whose historical name is misleading; changing its units would break existing extensions. Runtime/persisted canonical units remain KB/s.
- The 30-second proxy half-close is bounded and intentional; `socketserver` owns the client request socket lifecycle, so an extra `client.close()` in the handler is not required for normal cleanup.
- `ProbeMixin` calling BookFlow helpers is an architectural composition dependency of the Downloader facade, not a confirmed production AttributeError.
- The disk-space estimate issue needs a concrete failing multi-source accounting case before changing reserve semantics; no speculative rewrite was made.
- `Track_Title` fallback to book title remains a documented behavioral choice from earlier rounds; changing it would alter filenames and existing tests.
- The leading-space runtime-exact tray strings and Undo/Redo literals are context-specific localization entries, not changed without a demonstrated wrong call site.

## Verification

- Focused Round 19 regressions: 8/8 passed.
- Full pytest: 360/360 passed.
- Historical regression audit: PASS — 268 passed, 115 known source-shape incompatibilities, 0 newly unresolved failures.
- Exception audit: PASS — 109 reviewed broad exception passes.
- Undefined global audit: OK — 77 modules.
- Unused import audit: OK — 32 implementation modules.
- Qt localization audit: OK — ru/uk/de/en, help topics complete, onboarding complete, accessible names translated.
- Full parity: PASS — 61/61.
- Qt import audit: OK — 73 project modules reachable, no legacy frontend path.

Windows/PySide6/PyInstaller frozen build was not executed in this Linux environment.
