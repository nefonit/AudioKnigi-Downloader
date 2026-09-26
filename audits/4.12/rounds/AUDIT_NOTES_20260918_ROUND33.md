# Audit notes — Round 33 (2026-09-18)

Round 33 validates the pasted audit against the current Round 32 source and applies the user-requested Easy-mode search layout improvement.

## Confirmed and fixed

- Easy-mode center card maximum width increased from 900 to 1180 logical px; search rows now word-wrap and resize to contents so long book titles can remain visible on a second line without a horizontal scrollbar.
- Knigavuhe logical-book grouping now exposes all unique narrators, matching PoleKnig/Audioknigi behavior.
- `fmt_size(0)` now reports `0.0 B`; negative/invalid sizes remain unknown (`—`).
- Template placeholders are case-insensitive (`{author}`, `{BOOK_TITLE}`, etc.) while unknown placeholders remain untouched.
- An empty Playwright cookie list no longer erases a previously valid Cloudflare cookie file/count; fresh browser headers can still update the session profile.
- loudnorm first-pass JSON scanning uses a 512 KiB bounded stderr tail for noisy/partially damaged media.
- Fallback-source logs distinguish a failed primary source from a failed secondary mirror.
- Saving a cover in a new format removes stale `cover.jpg/jpeg/png/webp` alternatives first.
- Shared-source middle chapters with missing/invalid next boundaries emit an explicit diagnostic rather than silently looking normal while FFmpeg runs to EOF.
- Audioknigi search query input is stripped/empty-guarded and search HTML uses UTF-8-SIG decoding consistently.
- Knigavuhe emergency fallback analysis is capped at the top 8 scored candidates.
- Duration-probe cleanup always terminates registered ffprobe children and releases the executor without an 18-second blocking wait.
- Filesystem-root unfinished-download scan depth increased from 5 to 8.
- Queue drag/drop maps the event position into viewport coordinates before `rowAt()`.
- Ctrl+D now uses the same adaptive primary-download action as the visible button, preserving a user's selected subset of chapters.
- Batch URL analysis errors are logged and advance automatically instead of presenting a modal error for every failed URL.
- Opening an exact duplicate folder now synchronizes `last_completed_book` with the current book.
- Historical regression subprocess timeout increased to 240 seconds.
- Release/changelog baseline dates aligned to 2026-09-18.
- Removed the redundant runtime-exact Audiobookshelf Library-ID literal. The regex-shadowed skipped-parts prefix is intentionally retained as a translated fallback/static-audit completeness rule.

## Reviewed and intentionally unchanged

- `DownloadRequest.track_index()` already accepts Track objects, mappings and raw int/string scalars; the mixed call sites are valid.
- The proposed proportional disk-space reduction was not applied: in the current analysis path `Book.remote_size` is populated only when the book has one unique source file. For a shared-source book, downloading one chapter can still require the whole source file, so duration-proportional source sizing would dangerously underestimate required space.
- The reported trailing-space double-extension case is already handled by `safe_name(...).strip(". ")`, and `.ogg`/`.opus` are already in `AUDIO_EXTENSIONS`.
- Audioknigi pagination was not added because the pasted report does not establish a verified current pagination contract for that site.
- Provider-level parallel search was not introduced in this bug-fix round because it materially changes progress/error ordering and deserves dedicated performance testing, especially after the recent Windows worker-thread fixes.
- "Previous track restarts current chapter after 2–3 seconds" is a UX preference, not a correctness bug, and was left unchanged.
- The CPython 3.14 private `_wmi` workaround remains guarded by `hasattr` and a bootstrap self-test; replacing it requires validation on the target Windows/Python release.

## Verification

- Round 33 focused regressions: **34 passed**.
- Full pytest suite: **463 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI/help/onboarding/accessibility complete).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=264`, `known_shape_incompatibilities=119`, `resolved=0`).
- `compileall`: **PASS**.
