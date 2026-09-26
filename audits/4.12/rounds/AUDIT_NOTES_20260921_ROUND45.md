# Round 45 — Third external-audit hardening follow-up (2026-09-21)

Round 45 reviews the third external audit against the current Round 44 source tree. Findings were validated against actual package layout, runtime contracts, and existing regression coverage before any change was made.

## Confirmed fixes

- Existing pre-onboarding settings profiles no longer reopen the first-run wizard merely because the historic file lacks `first_run_complete`; genuinely new/empty profiles still start incomplete, and an explicit `false` remains authoritative.
- Support-bundle settings sanitization is recursive across nested mappings/lists/tuples. Secret-looking nested keys are redacted, and nested string/header values also receive the same path/credential cleanup used for logs.
- Support-log redaction now consumes complete quoted secret values such as JSON `"api_key": "abc def"` and preserves the surrounding quote style while replacing the secret.
- Root-relative AudioKnigi book routes are reconstructed correctly when a nested search page exposes `audio-123...` without a leading slash.
- Player-position state uses a short state lock plus a separate ordered persistence lock. Slow antivirus/disk I/O can no longer block position reads, while an older snapshot still cannot overwrite newer state.
- PoleKnig compact playlists no longer infer a zero-length chapter when adjacent per-file entries both start at `00:00`; only strictly increasing markers create an inferred timeline.
- Shared-source middle chapters with a missing/non-increasing next boundary now fail safely with `SharedSourceTimelineError` instead of letting FFmpeg duplicate the rest of the shared source to EOF.
- Windows media-key teardown guards a missing/zero HWND before pointer conversion.
- Output-directory fields still synchronize live, but expensive unfinished-download scans are scheduled after `editingFinished` (or an explicit folder-picker change), not on every typed character.
- The Qt Audiobookshelf connection-test worker uses a bounded 4-second request timeout so it fits inside the normal application exit grace window.
- Segmented Range download rejects a non-positive/unknown total size before any division or range geometry is calculated; the caller can fall back to ordinary downloading.
- Re-downloading a chapter first releases the same file from the built-in Qt player. If Windows still refuses deletion, the operation stops instead of starting FFmpeg against a locked destination.
- The player controller exposes a clean media-source unload path and the Player UI handles an empty source state explicitly.
- Keyboard seek events are coalesced through a short single-shot timer instead of issuing dozens of `QMediaPlayer.setPosition()` calls per second during key auto-repeat.

## Reviewed and intentionally unchanged

- Relative imports in `audioknigi.config`, diagnostics, and provider packages match the real repository hierarchy; the reported import failures assumed different file locations.
- `AppSettings` remains an intentional partial-overlay mapping for direct construction. Missing canonical keys are readable from defaults, while iteration/serialization preserves the explicitly supplied mapping shape required by existing compatibility tests.
- `ThreadPoolExecutor.shutdown(cancel_futures=True)` is supported by the project's declared Python >=3.11 runtime. Running HTTP work cannot be force-killed safely by `Future.cancel()`; no broad cancellation rewrite was introduced without a reproducible shutdown failure.
- `scan_unfinished()` keeps legacy `selected_indices=[] -> whole book` compatibility for old resume manifests. Queue persistence uses a different explicit-empty contract and remains unchanged.
- AF-specific DNS resolution keeps normal socket-family semantics: an `AF_INET` request is not silently converted into IPv6, while `AF_UNSPEC` already tries both.
- The local proxy's stalled-send timer resets after every successful send, so slow but progressing transfers are not terminated merely for lasting more than 20 seconds.
- The global JSON lock, queue batch-import UX, queue drop-coordinate theory, style-object lifetime, hidden compatibility controls, and provider-pool cancellation are broader architectural/performance topics rather than confirmed Round 45 correctness regressions.
- Easy-mode narration variants already refresh synchronously on table selection changes before activation, so the reported stale-combobox path was not reproduced.
- Missing-media dialogs are already rejected from the UI cancellation path and guarded against deleted Qt parents.
- English `Redo` for the bare `Повторить` literal is used by the text-edit context menu; download retry actions have separate explicit translations.

## Verification

- Round 45 focused regressions: **14 passed**.
- Full pytest suite: **574 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=255`, `known_shape_incompatibilities=128`, `resolved=0`). One historical static keyboard-seek contract is intentionally superseded by the new debounce behavior.
- Full parity: **PASS 61/61**.
- Qt import audit: **OK** (75 project modules reachable, no legacy frontend path).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.
