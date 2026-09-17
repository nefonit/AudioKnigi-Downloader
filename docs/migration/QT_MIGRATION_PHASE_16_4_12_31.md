# Qt Migration Phase 16 — deep audit hardening

Phase 16 is a Qt-only maintenance/hardening release based on four detailed source audits after Phase 15. The goal is not feature expansion: it is to harden downloader, network, search, queue and Qt runtime behavior while preserving the strict 61/61 legacy-to-Qt capability inventory.

## Confirmed fixes

- `download_engine.py` initializes active subprocesses as `weakref.WeakSet`; ffprobe registration is explicitly unregistered on completion.
- FFmpeg loudnorm measurement and non-copy splitting use consistent input-side `-ss` placement before `-i`.
- Partial cleanup includes `.part.assembling`; single-download transfer metrics are reset in `finally`.
- Resume-manifest save failures are surfaced instead of silently ignored.
- Duplicate preflight requires `ready == total`, not merely `existing == total`.
- HTTP sessions are no longer rotated every 24 acquisitions; session profile generation invalidates thread-local sessions after browser-cookie/profile persistence. Connection pools were enlarged for the real concurrency profile.
- Proxy relay preserves the reverse stream after TCP half-close and forwarded request paths are normalized defensively.
- Search service no longer wraps already-concurrent providers in another executor and accepts cancellation.
- Queue persistence accepts legacy flat items as paused `needs_analysis` tasks and uses model `to_dict()` serialization.
- Accessibility announcements avoid resetting an active polite timer and marshal cross-thread speech safely; table focus uses `QItemSelectionModel`.
- Theme switching preserves the application font, speed graph drops non-finite samples, bulk track selection invalidates `AccessibleTextRole`.
- Player resume is not erased on provisional duration events and Play after `EndOfMedia` seeks to zero.
- Bare `--qt-focus-trace` is an explicit argument error; first show/maximize ordering is stable.
- Event sounds no longer reuse one source-swapping player for overlapping short cues.
- Inventory parity and runtime acceptance are now distinct: inventory remains 61/61, runtime validation must be supplied separately.

## Audit claims not accepted literally

The audit reports were treated as evidence, not as patches to apply mechanically. In particular:

- SNI was already supplied with `wrap_socket(..., server_hostname=...)`; no corrective change was needed there.
- The PoleKnig JavaScript scanner had a performance concern but not the claimed literal infinite loop.
- Adaptive-range worker parking did not reproduce the described deadlock.
- Existing queue `pop()/insert()` end-drop semantics already allowed the last position; unrelated queue lifecycle/cancellation paths were hardened instead.

## Verification

- Active Qt-only tests: **55/55 PASS**.
- Strict capability audit after legacy retirement: **61/61 PASS**.
- Qt import boundary: **39 reachable project modules / 0 legacy frontend paths**.
- `python -m compileall`: **PASS**.

Windows frozen EXE and NVDA/JAWS acceptance remain required for a release binary.
