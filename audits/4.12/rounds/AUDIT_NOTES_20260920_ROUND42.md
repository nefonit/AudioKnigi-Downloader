# Round 42 — Windows system theme and external focus frame (2026-09-20)

Round 42 is driven by real Windows screenshots plus Windows 10 feedback.

## System theme

- The previous `system` mode mixed application QSS with native `palette(base)`, `palette(mid)` and `palette(button)` roles. On Windows 10/11 dark configurations this produced unstable contrast and inconsistent card/input colors.
- System mode now prefers Qt `QStyleHints.colorScheme()` for the Windows light/dark decision, falls back to native palette luminance when unavailable, and maps the result onto the same stable production light/dark tokens used by the explicit themes.
- The app also listens for `colorSchemeChanged` while System mode is active, so Windows appearance changes refresh the stable tokens without requiring a restart. This avoids palette-role combinations that made secondary text and settings panels difficult to read.

## Settings layout

- Removed the redundant `Режим` selector from `Настройки → Внешний вид и звук`. The top Simple/Advanced segmented switch is now the single UI-mode control. Saving Settings preserves the currently active mode directly.
- Fixed the centered Settings card width policy: it now has an 820 px minimum, 1180 px maximum, expanding size policy and a stronger center-layout stretch factor. This addresses the one-third-width card and horizontal clipping seen in the screenshots.

## Event sound checks

- Found a real semantic bug: `Проверить голос` called `app_ready`, and `app_ready` belongs to `SYSTEM_ONLY_EVENTS`, so both test buttons could reach Windows `MessageBeep`.
- Renamed the first button to `Проверить звук события`. It now plays the packaged `search_complete.mp3` through a dedicated `play_media_only(..., force=True)` path. Missing/invalid media never falls back to `MessageBeep`.
- `Проверить системный звук` now remains explicitly tied to `play_system("app_ready")`, i.e. native Windows system sound.
- Both checks report success/failure through the status bar.

## External keyboard focus

- Removed focus-state QSS that changed each control's own border/padding.
- Added `KeyboardFocusFrameManager` using Qt `QFocusFrame`. The frame follows the focused control externally, is transparent to mouse input, and uses the existing 2 px warm-amber focus color.
- Inner editors of combo/spin controls are normalized to the outer control so the visual focus target matches what the user operates. The manager now clears stale wrappers safely when dialogs/menus are destroyed, avoiding a second call into an already deleted C++ `QFocusFrame`.
- Accessible names/IDs and Tab order are unchanged.
- The frozen/source accessibility audit no longer requires the retired Settings `ui_mode` combo ID; the active segmented control is represented by `ui_mode_easy`, `ui_mode_advanced`, and `ui_mode_stack`. This fixes the Windows build self-test failure `missing widget id: ui_mode`.

## Verification

- Full pytest suite: **537 passed, 0 failed**.
- Round 38–42 UI contracts: **37 passed**.
- Historical regression audit: **PASS** (`passed=256`, `known_shape_incompatibilities=127`, `resolved=0`).
- Qt localization audit: **PASS** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **PASS**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **PASS** (79 modules).
- Unused-import audit: **PASS** (32 implementation modules).
- Full parity: **PASS 61/61**.
- `compileall`: **PASS**.
- This container does not include PySide6, so the final visual/runtime behavior of `QFocusFrame` and the Windows 10 system-theme rendering must be acceptance-tested on the packaged Windows build.
## Windows system-theme follow-up

- Windows visual acceptance found a mixed-palette regression in System theme: Qt selected dark QSS tokens while the restored native standard palette left QScrollArea/viewports light.
- System theme now follows the OS light/dark scheme but applies one coherent light or dark application palette, so styled and palette-painted widgets cannot disagree.
- Live `colorSchemeChanged` refresh uses the same coherent-palette rule.



## Light-theme visual accessibility follow-up

- Light and System-light now use a 2 px `#0066cc` external `QFocusFrame`; Dark and System-dark retain the established warm amber `#e5a93c` ring. This removes the low-contrast yellow-on-white focus treatment without changing focus geometry or Tab order.
- Light cards use a slightly stronger `#d1d9e2` border so white cards remain visually separated from the `#f3f5f8` window background without introducing shadows.
- Light table selection uses a slightly softer `#0d74de`, and rows gain a subtle `#edf4fc` hover state before selection. Dark table selection remains unchanged.
