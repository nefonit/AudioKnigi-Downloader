# NVDA / JAWS accessibility — 4.12.27

## What was wrong
In Advanced mode the post-start focus routine targeted the Simple-mode URL entry even though that control was hidden. On Windows/Tk 8.6 this could leave keyboard focus on the root window, so NVDA/JAWS users pressing Tab could receive no useful announcement at startup.

## What changed
- Initial focus is chosen from the active UI mode: Advanced starts on the visible advanced URL entry; Simple starts on the visible simple URL entry.
- Tab and Shift+Tab use an application-managed traversal list containing only visible, viewable, enabled interactive widgets.
- On FocusIn the app announces accessible name, role, state and value through the NVDA/JAWS Prismatoid bridge.
- Controls created after startup are registered when they first receive focus.
- `Ctrl+Shift+F12` refreshes the bridge and performs a screen-reader self-test.
- `app.log` records `ACCESSIBILITY STATE`, `ACCESSIBILITY FOCUS`, backend connection and backend-unavailable diagnostics.

## Windows dependency
The Windows requirement is `prismatoid>=0.18.2,<0.19`. Build scripts upgrade requirements in the build environment and verify that the NVDA/JAWS backend API can be imported.

## How to test on Windows
1. Start NVDA or JAWS before AudioKnigi Downloader.
2. Launch the app.
3. Press Tab and Shift+Tab. The reader should announce each visible control and its state/value.
4. Press `Ctrl+Shift+F12`. A working bridge speaks a confirmation. If it cannot connect, the app shows a warning.
5. If speech still fails, close the app and send `app.log`; the ACCESSIBILITY lines show whether the reader process was detected and whether Prismatoid acquired the backend.

## Test-environment note
Source regressions in the development container run on Linux/Xvfb, not on a real NVDA/JAWS Windows desktop. The final Windows EXE must therefore still be validated with actual NVDA and JAWS.
