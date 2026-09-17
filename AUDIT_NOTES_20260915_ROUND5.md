# Audit notes — Round 5 (2026-09-15)

## Confirmed defects fixed

1. **Knigavuhe cancellation propagation** — `enrich_search_variants()` now re-raises `Cancelled` instead of silently replacing the worker result with the original row.
2. **Rights-restricted search rows** — both title hydration and narration-variant enrichment preserve `availability="restricted"` when the page contains the provider's restriction markers.
3. **Empty version labels** — `version_label("")` now returns an empty string rather than `"v"`.
4. **Full-MP3 source retention** — when the source is already MP3/copy-compatible and `delete_source=False`, the final MP3 is copied and the original is retained as a visible `(... исходник).<ext>` file. Disk preflight now reserves space for both files.
5. **MP3/VBR bitrate detection** — ffprobe now requests `format=bit_rate` and uses it when stream-level `bit_rate` is unavailable (`N/A`).
6. **BookFlow default consistency** — the fallback for a missing `runtime_delete_source` attribute is now `True`, matching settings/downloader defaults.
7. **Auto-Chunker telemetry race** — comparison/update of the shared `last_target` state is protected by the progress lock; logging remains outside the lock.
8. **Packet validation robustness** — ffprobe requests both PTS and DTS and accepts the first numeric timestamp, so DTS-only damaged/odd MP3 streams are not automatically classified as truncated.
9. **Playlist BOM handling** — playlist bytes are decoded with `utf-8-sig`, and the parser additionally strips a leading BOM before `json.loads()`.
10. **Runtime translation prefix** — removed the generic `Обрабатываю полный файл` prefix fallback because the concrete message already has a regex translation; this prevents mixed-language suffixes after future text changes.
11. **Accessibility descriptions** — added DE/EN/UK translations for the four missing descriptions reported in the audit (book input, resume recovery, analyze action, restart-required scale hint).
12. **Queue URL duplicate detection** — active-queue comparisons now use `normalize_supported_url()` so scheme-less and canonical URLs cannot be added as separate copies of the same book.
13. **Search-result narration preservation across redirects/canonicalization** — pending search and analyzed book URLs are compared canonically before narration variants are copied.
14. **Easy/Advanced input synchronization** — `easy_add_another_book()` now clears both the Easy input and the advanced book URL field.
15. **History redownload UX** — choosing Redownload from History is treated as the user's explicit confirmation; after re-analysis, an exact duplicate is deleted and downloaded without asking the same question a second time.

## Reviewed but intentionally not changed

- **`self.request._track_index(track)`**: the audit initially called this nonexistent, but the same report later correctly identifies `DownloadRequest._track_index()` as present and functional. This is an encapsulation/style concern, not a runtime `AttributeError`.
- **Chrome/User-Agent date comment**: `2026-09-12` is not an anachronism for this build; the current release date is 2026-09-15.
- **PoleKnig author fallback inside grouped variants**: the grouping key prevents an empty-author representative from sharing a normal multi-URL author group, so changing this line does not fix a demonstrated loss path. No behavioral change was retained.
- **Sequential provider search**: parallelizing all providers is a product/performance architecture change with rate-limit/cancellation implications, not a correctness fix, so it was not introduced in this hardening round.
- **Direct-URL `narration_variants` for audioknigi.com.ua**: a directly pasted book URL has no search-result context from which to obtain alternative narrations. No speculative extra provider search was added.
- **`copy.deepcopy(request)` in `DownloadWorker`**: the UI path already normalizes/clears non-serializable native cover objects before constructing the worker, as the report itself later notes.
- **Onboarding `audio_preset="copy"` + `normalization_mode="two_pass"`**: runtime media profile selection deliberately disables stream-copy when normalization is active; no functional contradiction occurs at encode time.
- **Duplicate keys between `runtime_exact.json` and `legacy_literals.json`**: these catalogs serve different translation entry points (`localize_runtime_text` vs `ui_text`). A broad catalog consolidation would be a larger migration, not a targeted runtime fix.
- **Playwright `playlist_response is None` guard**: requests does not normally return `None`; the harmless guard is retained because archived compatibility tests explicitly require the defensive source shape.

## Verification

- Round 5 focused regressions: **8 passed**.
- Full current pytest suite: **238 passed, 0 failed**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=113`).
- Historical regression audit: **PASS** (`passed=271`, `known_shape_incompatibilities=112`).
- Undefined-global audit: **OK** (77 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`.
- Full parity audit: **PASS 61/61**.
- Static Qt import-boundary audit: **OK** (73 project modules reachable, no legacy frontend path).

The Windows/PyInstaller executable build itself is not runnable in this Linux environment. Round 4's clean-interpreter circular-import regression remains part of the full suite and continues to pass.
