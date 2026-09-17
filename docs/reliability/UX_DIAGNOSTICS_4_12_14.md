# AudioKnigi Downloader 4.12.14 — UX & diagnostics

## Simple-mode narration choice

After analysis, the simple-mode confirmation card now displays **Озвучка** when multiple recordings are available. The control shares the same `narration_var`, availability map and URLs as the advanced Book tab. Selecting another reader re-analyzes that exact recording before download. A single-recording book keeps the row hidden.

## Table scrollbars and narrow layouts

Treeview vertical/horizontal scrollbars use explicit AudioKnigi styles so Windows/ttkbootstrap cannot fall back to a bright system scrollbar after a theme change. Keyboard hints on the simple search area and advanced Search tab update their wrap length from the actual available width.

## Slider values

Bandwidth and event-sound volume retain visible live values. Bandwidth uses an explicit numeric representation, including `0 МБ/с — без лимита`; event-sound volume remains a percentage.

## Detailed error logging

`app.log` now includes timestamp, level, thread, module, function and line number. Log rotation is 5 MB with five backups. Unhandled Tk callback, background-thread and main-thread exceptions are captured with traceback. High-level recovered errors also preserve traceback context while the UI continues to show friendly messages. Privacy sanitization remains enabled for secrets, URLs and user-profile paths.

See `audits/4.12/ERROR_HANDLING_AUDIT_4_12_14.md` for the all-module exception-handling audit.
