# AudioKnigi Downloader 4.12.5 — Keyboard & Validation UX

This release makes the simple workflow usable without a mouse and fixes the hidden empty-field warning.

## Empty universal field

Pressing **Find or open** with an empty Step 1 field now opens a centered modal dialog. The primary action **Go to field / Перейти к полю** closes the dialog and focuses the input. Enter activates the primary action; Esc closes the dialog. Screen readers receive the validation message immediately.

## Keyboard navigation

- Tab / Shift+Tab — next / previous focusable control.
- Enter / keypad Enter — activate focused AudioKnigi buttons; open selected search result.
- Space — native button / checkbox activation.
- Ctrl+L — focus the main universal input.
- Alt+1…5 — Book, Search, Queue, History, Settings.
- Ctrl+Tab / Ctrl+Shift+Tab — next / previous advanced tab.
- Shift+F10 — context menu for search results.
- F4 or Alt+Down — open a dropdown.
- Esc — close an open dropdown/dialog first; otherwise cancel the active operation.
- F1 — context-sensitive help.

The implementation stays on native Tk/ttk controls so NVDA/JAWS/Prismatoid accessibility is preserved.
