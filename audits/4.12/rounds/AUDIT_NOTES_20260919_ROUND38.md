# Round 38 — Audioknigi multi-author titles and keyboard focus accessibility (2026-09-19)

Round 38 addresses two Windows verification findings after Round 37.

## Audioknigi multi-author title normalization

- Added a dedicated parser for the site form `Author 1, Author 2 - Title`.
- The parser requires at least two comma/semicolon-separated person-like author chunks, making it much safer than treating arbitrary text before a dash as authors.
- The reported site label `Бурносов Юрий, Бурносова Татьяна - Тоннельная крыса` now yields title `Тоннельная крыса` and authors `Бурносов Юрий, Бурносова Татьяна`.
- Search-card, page-title and structured/JSON-LD author signals are merged and deduplicated instead of overwriting one another.
- Direct URL analysis uses the same multi-author normalization, so Easy and Advanced modes receive the same clean `Book.title`/`Book.author`.
- The multi-author parser intentionally does not treat ordinary dashed titles such as `Гарри Поттер — Философский камень` as a multi-author prefix.

## Keyboard/accessibility follow-up

- Added an explicit deterministic Tab/Shift+Tab chain for Easy mode, from mode buttons through the universal input, actions, quality/output controls, results, narration selector, annotation and secondary actions.
- Hidden/disabled result-only controls stay in the chain definition but Qt skips them natively until they become available.
- Advanced mode continues from the mode selector to the native tab widget; page controls retain Qt-native traversal order.
- Read-only Easy annotation and technical session-log editors use `setTabChangesFocus(True)` so Tab does not become trapped inside the text view.
- Added high-visibility keyboard focus styling across system/light/dark themes for `QPushButton`, text/spin/combo edits, plain text views, tables, lists, checkboxes, sliders and the tab bar.
- Focus uses a thick amber border so the indicator differs by both color and shape, including on blue primary buttons.
- The accessibility audit now explicitly includes the Easy narration selector and Easy annotation text view as required/focusable controls.

## Verification

- Round 38 focused regressions: **7 passed**.
- Current pytest suite excluding the nested historical wrapper: **506 passed, 0 failed**.
- Historical wrapper: **1 passed**.
- Effective current pytest contract: **507 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=263`, `known_shape_incompatibilities=120`, `resolved=0`).
- Full parity: **PASS 61/61**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **OK**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.

## Environment note

The CI/container image used for this source audit does not include PySide6, so the final visual focus appearance still requires the normal Windows GUI/NVDA/JAWS acceptance check. The stylesheet/tab-order contracts and all source-level accessibility audits are covered by automated regression tests.
