# Audit notes — Round 29 (2026-09-18)

Windows screenshot verification after Round 28 showed that Easy-mode search results were correct and responsive, but the seven-column results table exceeded the narrow center card and required a horizontal scrollbar.

## Fix

- Preserved the established centered Easy-mode card width (`setMaximumWidth(900)`) for historical UI compatibility.
- Kept all seven search columns visible; no search metadata is hidden in Easy mode.
- `Название`, `Автор`, and `Чтец` use stretch sizing and share remaining width.
- `№`, `Статус`, `Озвучки`, and `Источник` use content-sized sections.
- Disabled the Easy-mode horizontal scrollbar and disabled word wrapping to keep rows compact.
- Long visual cell text uses right-side ellipsis; the underlying model still provides complete text and accessible descriptions to assistive technology.
- Advanced-mode search table behavior is unchanged.

## Verification

- Added Round 29 regression coverage for responsive Easy-mode search columns and no-horizontal-scroll behavior.

## Verification

- Round 29 focused regressions: **2 passed**.
- Full pytest suite: **420 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.
