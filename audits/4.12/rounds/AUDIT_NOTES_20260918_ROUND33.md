# Audit notes — Round 33 (2026-09-18)

Round 33 validates the pasted audit against the current Round 32 source and applies the requested Easy-mode search layout improvement.

## Confirmed and fixed

- Easy-mode center card maximum width increased from 900 to 1180 logical px; search rows now word-wrap and resize to contents so long book titles can remain visible on a second line without a horizontal scrollbar.
- Knigavuhe logical-book grouping now exposes all unique narrators.
- fmt_size(0) now reports 0.0 B; negative/invalid sizes remain unknown.
- Template placeholders are case-insensitive while unknown placeholders remain untouched.
- Empty Playwright cookie snapshots no longer erase a previously valid Cloudflare cookie file/count.
- loudnorm first-pass JSON scanning uses a 512 KiB bounded stderr tail.
- Fallback-source logs distinguish failed primary and secondary sources.
- Saving a cover in a new format removes stale cover sidecars with alternate extensions.
- Shared-source middle chapters with missing/invalid next boundaries emit an explicit diagnostic.
- Audioknigi search input is stripped/empty-guarded and decoded as UTF-8-SIG.
- Knigavuhe emergency fallback analysis is capped at the top 8 scored candidates.
- Duration-probe cleanup always terminates registered ffprobe children and releases the executor without an 18-second blocking wait.
- Filesystem-root unfinished-download scan depth increased from 5 to 8.
- Queue drag/drop maps the event position into viewport coordinates before rowAt().
- Ctrl+D now uses the same adaptive primary-download action as the visible button, preserving selected subsets.
- Batch URL analysis errors are logged and advance automatically instead of presenting a modal for every failed URL.
- Opening an exact duplicate folder synchronizes last_completed_book.
- Historical regression subprocess timeout increased to 240 seconds.
- Release/changelog baseline dates aligned to 2026-09-18.
- Removed the redundant runtime-exact Audiobookshelf Library-ID literal. The skipped-parts prefix is retained as a translated fallback/static-audit completeness rule.

## Reviewed and intentionally unchanged

- DownloadRequest.track_index() already accepts Track objects, mappings and raw int/string scalars.
- The proposed proportional disk-space reduction was not applied: remote_size is populated only when one unique source file backs the book, so selected chapters can still require the whole shared source.
- The reported trailing-space double-extension case is already handled by safe_name stripping and .ogg/.opus are already supported.
- Audioknigi pagination was not added because the report does not establish a verified current pagination contract.
- Provider-level parallel search was not introduced in this bug-fix round because it materially changes progress/error ordering and deserves dedicated performance testing.
- Previous-track restart-at-zero is a UX preference, not a correctness bug.
- The CPython 3.14 private _wmi workaround remains guarded by hasattr and a bootstrap self-test.

## Verification

- Round 33 focused regressions: **34 passed**.
- Full pytest suite: **463 passed, 0 failed**.
- Qt localization audit: **OK** (ru, uk, de, en; static UI/help/onboarding/accessibility complete).
- Exception audit: **PASS** (reviewed_broad_exception_passes=107).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (passed=264, known_shape_incompatibilities=119, resolved=0).
- compileall: **PASS**.
