# Theme audit 4.12.31

Checked effective **Dark**, **Light**, **System-Light** and **System-Dark** rendering for the Simple dashboard and every Advanced tab.

## Fixed

- Simple-mode confirmation and recovery cards now have explicit light/dark color pairs.
- Semantic colors are split into readable outline/link colors and darker filled-control colors.
- Primary, success, info, warning and danger buttons have distinct normal, hover, pressed and disabled states.
- Filled/outline button text is kept at WCAG AA 4.5:1 or better in all tested states.
- Main control borders meet the 3:1 non-text contrast target against panel surfaces.
- The external 3-pixel keyboard focus ring is yellow in dark themes and dark blue in light themes.
- `system` theme polls Windows appearance and repaints the already-open application when it changes.

## Regression coverage

`tests/test_theme_contrast_system_41231.py` checks semantic button state contrast, visible state changes, control/focus contrast, hidden Simple-mode cards, live System-theme switching and all main UI text across Dark/Light/System-Light/System-Dark and all Advanced tabs.

## Final verification

- Full regression suite: **439/439 tests passed** under a virtual X display.
- Effective UI audit: **211 text-bearing/interactable widgets** inspected in each of Dark, Light, System-Light and System-Dark.
- Normal text contrast: no audited item below **4.5:1**; measured minimum **5.27:1**.
- Semantic buttons: **60 buttons per theme** checked in normal, hover, pressed and disabled states; no checked button state below **4.5:1**.
- Every checked semantic button has a visually distinct hover state and a distinct pressed state.
