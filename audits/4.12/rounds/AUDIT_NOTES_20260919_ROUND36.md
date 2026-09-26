# Round 36 — Easy search width, source metadata and Audioknigi relevance (2026-09-19)

Round 36 addresses Windows UI feedback from the Easy-mode search screen and verifies title/annotation contracts across all supported sources.

## UI

- Easy-mode center card now grows substantially wider on desktop windows (`860` minimum, `1500` maximum) and receives a dominant layout stretch factor.
- The seven-column search table remains scrollbar-free: Title/Author/Narrator share the flexible width, while number/status/variant/source columns remain content-sized.
- Long titles continue to wrap and rows resize to content.

## audioknigi.com.ua titles and search relevance

- Canonical title cleanup removes site URLs and SEO tails such as `аудиокнига слушать онлайн`.
- Independently parsed author metadata can now remove a multi-word author prefix even when the site omits a dash, e.g. `Бурносов Юрий Тоннельная крыса` → `Тоннельная крыса`.
- The existing one-word ambiguity guard remains: `Александр I` is not reduced to `I` merely because the author is `Александр`.
- After detail-page hydration every Audioknigi result is rechecked against the actual query. Results with no matching title/author/narrator are discarded even if their metadata request failed.
- Regression examples for query `Крыса` explicitly reject `Четыре всадника`, `Большие друзья. Музыкальные сказки`, and `Как удвоить объем памяти`.

## Annotation contract

- Audioknigi now prefers semantically marked visible synopsis blocks, then labelled visible `Краткое содержание` / `Описание` / `Аннотация`, then structured Book JSON-LD, and only finally a non-SEO meta description.
- Audioknigi SEO text containing listen/download/site boilerplate is rejected.
- Knigavuhe continues to prefer its visible `book_description` block; SEO-only meta descriptions are now rejected if no real visible synopsis exists.
- PoleKnig keeps the Round 34 visible-synopsis-first contract and SEO filter.
- Both Easy and Advanced interfaces render the same canonical `Book.description` produced by analysis, so source fixes apply identically to both modes.

## Verification

- Round 36 focused regressions: **10 passed**.
- Relevant provider/layout/previous-round regressions: **58 passed** before the full run.
- Current pytest suite excluding nested historical wrapper: **494 passed, 0 failed**.
- Historical wrapper: **1 passed**.
- Effective current pytest contract: **495 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=264`, `known_shape_incompatibilities=119`, `resolved=0`).
- Full parity: **PASS 61/61**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **OK**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.
