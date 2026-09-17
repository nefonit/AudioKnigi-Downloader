# 4.12.41 quality-gate, queue-mode and diagnostics hardening

This round verified the 2026-09-15 audit against the 4.12.40 release and applied only confirmed fixes.

## Confirmed fixes

- Accessibility self-test diagnostics are printed on a failed accessibility contract and report lines cannot run into release metadata.
- Runtime self-test checks no longer depend on Python `assert`, so `python -O` does not disable acceptance checks.
- PyInstaller extension names retain package paths in the frozen-module audit.
- Static gates understand `__doc__`/`__annotations__`, qualified localization calls and pytest collection-error lines without broad substring false positives.
- Logging credential redaction no longer hides harmless token-related settings.
- HTML metadata has `og:title`/`title` fallbacks.
- Text sidecars are atomic, configured public URLs remain useful in support bundles, explicit history export is not silently capped at 500 rows, and search-result canonicalization clones rather than mutates provider objects.
- Provider analysis prefetches covers consistently, the shared search model is initialized before page builders, and search inputs retain focus semantics during background search.
- Queue tasks persist `selected` vs `full_mp3` mode and the UI can enqueue a one-MP3 job.

## Rejected or already-correct claims

- `requests==2.32.5` is a real PyPI release (2025-08-18); no dependency downgrade was applied.
- Chrome 153 is a real Stable release in September 2026; current User-Agent majors were not rolled back.
- `menu_utils.transient_menu()` is actively used by search, queue, history and track context menus.
- Qt history callbacks are emitted through `DownloadWorker.history_changed`, a Qt Signal, so the production GUI marshals the callback across threads rather than directly touching widgets from the download engine.
- The existing player-seek focus guard was retained because archived keyboard regression coverage depends on it and the reported mouse-style timing issue was not reproduced here.

## Verification target

See the release response for the final clean-ZIP test counts after packaging and re-extraction.
