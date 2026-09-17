# Qt-only Phase 18 resource lifecycle audit — 2026-09-07

## Scope

Follow-up audit after Phase 17 covering downloader subprocess ownership, browser-session refresh, source fallback identity, Knigavuhe/PoleKnig cancellation, Mapping contracts, system sounds, URL validation, queue invariants and Qt shutdown.

## Fixed

- FFmpeg subprocess unregister/cleanup.
- Per-Range-subrequest HTTP profile refresh boundary.
- Fallback `DownloadRequest.book` identity.
- Duplicate browser-profile condition.
- Defensive non-dataclass field cache.
- Non-waiting cancellation-aware search/hydration pools.
- Strict concrete-book URL validation.
- Queue `None` list serialization and needs-analysis priority guard.
- Re-entrant close/shutdown behavior and missing-media modal ownership.
- Daemonized Windows system sound dispatch.
- Accessibility coalescing delay.
- Redundant output-directory assignments.

## Not reproduced / no code change required

- MIME label `text/x-python` as a filesystem filename.
- Missing `task_requires_analysis` import/export.
- `_split_track` unbound `out`.
- Invalid Knigavuhe `cancel_event` keyword signature.
- Last compact shared-source track requiring a synthesized end timestamp.

## Verification

See Phase 18 migration document and `tests/test_phase18_runtime_resource_hardening_41231.py`.
