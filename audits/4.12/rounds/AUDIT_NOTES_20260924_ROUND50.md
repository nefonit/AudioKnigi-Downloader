# Round 50 UI synchronization / AudioKnigi annotation notes — 2026-09-24

Round 50 is based on the supplied Round 49 archive and addresses the Windows screenshot showing the Advanced **Book** tab before analysis, plus Easy/Advanced state synchronization and noisy `audioknigi.com.ua` annotations.

## Confirmed fixes

- **Advanced Book tab before analysis:** the introductory and input labels now keep fixed vertical policies while the empty-state panel owns the spare vertical stretch. This prevents Qt from distributing a tall window's unused height across ordinary `QLabel` rows. After analysis the empty state is hidden and the chapter table continues to own `stretch=1`, preserving the already-good analysed layout.
- **Easy / Advanced universal input synchronization:** `easy_input` and `book_url_edit` now mirror each other live with a recursion guard. Switching modes therefore keeps the same query/URL visible. The existing output-folder and quality synchronization remain unchanged, and analysis results already populate both presentations from the same `current_book`.
- **AudioKnigi real synopsis extraction:** detail pages are now parsed around the heading-like line ending in `краткое содержание`, not the earlier marketing sentence that merely mentions “прочесть краткое содержание”. The fixed SEO bridge (`…описание и краткое содержание, исполнитель…, слушайте бесплатно онлайн…`) is removed, and capture stops before listen/reviews/comments/other-recordings/recommendations sections.
- **AudioKnigi broad-container fallback:** generic `shortstory` / `full-text` style containers are retained only as fallback and rejected when multiple technical metadata labels remain, preventing Author/Reader/Series/Added/Genre/player chrome from becoming the annotation.

## Regression coverage

Round 50 adds focused checks for:

- stable Advanced pre-analysis stretch ownership and post-analysis table stretch;
- bidirectional Easy/Advanced universal-input wiring;
- a realistic AudioKnigi page containing app promotion, Author/Reader/Series/Added/genres before the synopsis and player data after it;
- avoiding the top marketing phrase as a false synopsis anchor;
- preserving the older clean semantic `book-description` fallback.

## Verification

- Full pytest suite: **617 passed, 0 failed**.
- Round 50 + directly related Round 48/Round 36 regressions: **21 passed**.
- Historical regression audit: **PASS** (`passed=255`, `known_shape_incompatibilities=128`, `resolved=0`).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **OK** (75 project modules reachable, no legacy frontend path).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity audit: **PASS 61/61**.
- `compileall`: **PASS**.
