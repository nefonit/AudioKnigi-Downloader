# Qt-only Phase 17 audit follow-up — 2026-09-07

## Scope

Reviewed the explicit queue/search/theme audit plus four attached follow-up audits covering core HTTP lifecycle, downloader/FFmpeg, Knigavuhe/PoleKnig/network DNS, Qt event sounds/accessibility/runtime, queue/player behavior and source URL parsing.

## Confirmed and fixed

1. `needs_analysis` queue tasks could be rewritten to `retry` by Qt UI actions: fixed in both service invariant and UI guards.
2. Search dedupe compared raw URLs: fixed with supported-source canonical identity.
3. Audioknigi combined author/title metadata could duplicate author in the title: fixed.
4. Theme reapply guard relied on `QStyle.objectName()`: replaced with explicit applied-style state.
5. Knigavuhe `_hydrate_narration_variant_readers` referenced undefined `cancel_event`: fixed and propagated.
6. Search/variant hydration cancellation coverage expanded.
7. `MappingDataclass` mixed immutable Mapping typing with mutation API and repeatedly allocated field-name tuples: made read-only and cached.
8. HTTP adapter `pool_block=True`: changed to non-blocking pool overflow.
9. Parked Range worker cancellation no longer raises uncaught `Cancelled` in a daemon thread.
10. Stage-4 verification messages now use i18n.
11. Bad focus-trace CLI arguments no longer silently crash a windowed build.
12. Known no-scheme URLs with explicit ports are parsed.
13. Event-sound language changes release stale players; system beep is off the GUI thread.
14. Queue exhaustion no longer reports completion while paused/error/re-analysis items remain.
15. Removing the last queue row has an accessible focus fallback.
16. Output-dir manual edits synchronize across the three UI surfaces.
17. AccessibleAnnouncer preserves the first polite message while coalescing progress.

## Reviewed but not reproduced / intentionally unchanged

- The dump label `text/x-python` is MIME metadata; actual source files are `queue_service.py` and `search_service.py`.
- FFmpeg input `-ss` + output `-t` does not make `-t` absolute; changing it based on that premise would be a regression risk.
- The `.assembling` unlink happens only after `with open` unwinds and closes the descriptor.
- Last compact-timeline chapter with no following marker intentionally ends at EOF.
- Current CONNECT/origin proxy parsing already recognizes numeric IPv6; no concrete failure from the cited path was established.
- The cited player seek scenario has no cross-file state leak because `load()` resets `_resume_after_stop_ms`.
