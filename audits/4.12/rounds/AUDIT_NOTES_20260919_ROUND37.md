# Round 37 — Knigavuhe relevance and Audioknigi coauthors (2026-09-19)

Round 37 addresses two Windows verification findings after Round 36.

## Knigavuhe relevance

- The previous Knigavuhe hydration contract intentionally preserved web-site hits that matched only description, series or genre. In the desktop result table this produced visibly unrelated books.
- After detail-page hydration, Knigavuhe now retains only rows whose exposed title, author or narrator matches the user query.
- A small conservative Russian inflection allowance preserves useful forms such as `Крыса` matching `Крысы в стенах`.
- Regression examples for query `Крыса` explicitly reject `Крауч Энд`, `Дворец грез`, and `Кому жить на Руси хорошо`.
- Search by author/narrator remains supported because those fields participate in the same final relevance check.

## Audioknigi coauthor/title normalization

- Search-card author metadata is no longer discarded when JSON-LD/detail metadata supplies a different author.
- Authors are merged and deduplicated by normalized name tokens, so reordered forms of the same person do not duplicate.
- A title prefix is stripped only when that author was independently observed in the search card/structured metadata.
- This fixes the reported `Бурносова Татьяна - Тоннельная крыса` case: the table title becomes `Тоннельная крыса`, while the author column retains both the structured author and the card-detected coauthor.
- Ambiguous legitimate dashed titles remain protected; for example `Гарри Поттер — Философский камень` is not reinterpreted as author `Гарри Поттер`.

## Verification

- Round 37 focused regressions plus ambiguity guard: **6 passed**.
- Current pytest suite excluding the nested historical wrapper: **499 passed, 0 failed**.
- Historical wrapper: **1 passed**.
- Effective current pytest contract: **500 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=263`, `known_shape_incompatibilities=120`, `resolved=0`).
- Full parity: **PASS 61/61**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **OK**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.
