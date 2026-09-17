# Qt-only Phase 16 audit — deep downloader/network/runtime hardening

Date: 2026-09-07

## Scope

Reviewed the four user-supplied audit notes covering downloader/core/download-engine, network/source parsers/models/i18n, Qt runtime/accessibility/application, and main-window/player/queue/search/theme behavior. Every claim was checked against the Phase 15 Qt-only source before modification.

## Confirmed and fixed

1. Active subprocess registry now uses weak references consistently and ffprobe processes are unregistered after completion.
2. Loudnorm measurement and split processing use consistent input-side seek semantics.
3. `.part.assembling` is included in partial cleanup.
4. Transfer metrics are reset through `finally`; resume-manifest persistence failures are surfaced.
5. Duplicate preflight requires validated-ready tracks.
6. HTTP sessions are long-lived and profile-generation-aware; browser session persistence refreshes subsequent thread-local sessions.
7. Proxy half-close and forwarding path handling are hardened.
8. Nested provider-level search executor was removed and cancellation plumbing was added.
9. Queue persistence preserves legacy flat tasks and avoids `dataclasses.asdict()` where model `to_dict()` is the contract.
10. Accessibility announcement starvation/thread-affinity, selection semantics and bulk AccessibleTextRole invalidation are fixed.
11. Theme changes preserve the scaled application font; speed graph rejects NaN/inf.
12. Player provisional-duration resume clearing and EndOfMedia restart behavior are fixed.
13. Focus-trace CLI, first-show/maximize order, event-sound player lifecycle and runtime parity semantics were hardened.
14. Downloader split progress now uses the translation key rather than a hard-coded Russian progress string.

## Claims classified as inaccurate or overstated

- Cloudflare bootstrap SNI was already set correctly through `server_hostname`; no SNI patch was applied.
- PoleKnig JS scanning could be expensive but did not contain the claimed literal infinite loop.
- Adaptive-range worker parking did not establish the alleged deadlock under the current queue/worker termination logic.
- Queue DnD `pop`/`insert` logic already supports the last logical row; no index-shift patch was applied for that claim.
- Some audit items described Python/Qt behavior too categorically (for example `sys.excepthook` and intermediate media duration). We hardened the relevant lifecycle without relying on the inaccurate premise.

## Regression evidence

- `pytest -q tests`: **55 passed**.
- `tools/full_parity_audit.py --require-legacy-retired`: **PASS 61/61**.
- `tools/qt_import_audit.py`: **39 reachable project modules; no legacy frontend path**.
- `python -m compileall -q audioknigi audioknigi_qt.py tools`: **PASS**.

The Qt-only retirement invariant remains intact; no Tk runtime was restored.
