# AudioKnigi Downloader 4.12.0 — User Friendly

This release focuses on making the default workflow self-explanatory while preserving the existing advanced controls and accessibility architecture.

## What changed

1. **Universal input** — the simple home field accepts title, author, or URL.
2. **Clear modes** — “Простой режим” and “Расширенный режим”, plus “Расширенные возможности”.
3. **Goal-based first run** — search for a book or use a link; then a short three-step explanation.
4. **Actionable errors** — recovery cards provide Retry, Find, Help, or another narration instead of only an error dialog.
5. **Narration availability** — known variants are marked available/unavailable and restricted recordings can jump to an accessible variant.
6. **Simplified search** — raw URLs are hidden; Status summarizes availability/variant count; Copy URL remains in the context menu.
7. **Pre-download confirmation** — title, author, reader, part count, and destination are shown before download.
8. **Human progress** — technical worker messages are translated into understandable workflow states.
9. **Clear completion** — the result card reports N/N parts and the destination folder, with Listen / Open folder / Find another actions.
10. **Contextual F1 help** — help opens on the section matching the current workflow.

## Compatibility

- Existing advanced tabs, queue, chapter selection, M4B, templates, history, event sounds, and provider backends are preserved.
- Native Tk/ttk accessibility remains the baseline; no Canvas-only controls were introduced.
- Ctrl+D in simple mode no longer bypasses the pre-download confirmation.

## Regression coverage

A dedicated 4.12.0 test module covers universal routing, mode labels, simplified search, confirmation, restricted narration recovery, human progress, completion, contextual F1 help, onboarding, and Ctrl+D behavior.


## Final UI hardening

- The version badge is kept on the compact subtitle row so it is not clipped at 125–200% scaling after live theme changes.
- The unavailable Drag-and-Drop hint is deliberately short enough to remain readable at high UI scaling.
- Direct Tk-root destruction cancels pending `after` callbacks and closes the UI event bus, so repeated GUI lifecycles do not leave stale Tcl jobs behind.

## Validation

- 255 pytest regression cases pass when the GUI suite is run in isolated Tk batches (required by the Xvfb test environment).
- Four legacy executable GUI smoketests pass separately.
- `compileall` and `--ci-selftest` pass for version 4.12.0.
