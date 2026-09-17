# AudioKnigi Downloader 4.12.31 — NVDA/JAWS editor, layout-independent hotkeys and search-focus audit

## Scope

This audit follows a user report that typed book/author text was not read by NVDA/JAWS with `Insert+Up`, global shortcuts could depend on the current keyboard layout, and a completed search should move/announce focus in the results table.

## Findings and fixes

### 1. Typed editor value was not reliably available to standard reader commands

The Simple-mode universal editor is a native `ttk.Entry`. Prismatoid already supplied application speech, but it is not the Windows UI Automation value provider for that widget. On Windows, Tk 8.6 accessibility exposure can therefore be insufficient for a reader's standard current-line/value command.

Fixes:

- enabled the Windows `tk-uia` provider at application startup before child widget creation;
- added explicit accessible name/description to the universal editor;
- synchronized project semantic names into `tk-uia` when Tk native accessibility is unavailable;
- added `AccessibilityManager.announce_focused_editable_text()` as a Prism-backed fallback if `Insert+Up` reaches the application.

### 2. Global Ctrl+letter shortcuts were keysym-dependent

`Ctrl+L`, `Ctrl+D`, `Ctrl+F`, `Ctrl+Q` and `Ctrl+H` had ordinary Tk letter bindings. Those can stop matching when a Windows Russian/Ukrainian layout produces a Cyrillic keysym.

Fix:

- added a generic physical-key handler using Windows virtual-key codes;
- retained ordinary Latin bindings as the primary path and suppresses duplicate execution;
- added Cyrillic semantic fallbacks for the non-Windows test/runtime path;
- confirmed existing editor shortcuts `Ctrl+C/V/X/A/Z/Y` already use layout-independent VK handling.

### 3. Search focus move lacked explicit speech

The application already moved keyboard focus to the results table after successful search. The move was not explicitly announced.

Fix:

- after results render, the first row is selected/focused as needed;
- focus moves to the Simple or Advanced results Treeview;
- NVDA/JAWS receives an explicit announcement: focus moved to the table, result count, and Up/Down usage hint.

### 4. Frozen EXE could not rely only on source-level dependency declaration

Because the accessibility provider must exist inside a PyInstaller `--windowed` executable, the build now:

- installs `tk-uia>=0.8.0,<0.9` on Windows;
- explicitly uses `--collect-all tk_uia`;
- copies `tk-uia` distribution metadata;
- verifies the version/import during Windows build preflight;
- verifies the provider again in the finished EXE via `--accessibility-import-selftest`.

### 5. Repository build documentation

The supplied MASTER archive had accidentally lost the active `docs/build/` files while `docs/INDEX.md` and the architecture regression still referenced them. All five build documents were restored from the previous correct MASTER archive, and `RELEASE_SETUP.md` was updated for 4.12.31 / Prismatoid 0.18.2 / tk-uia 0.8.x.

## Automated validation

New/expanded regression coverage validates:

- explicit accessible editor semantics;
- typed-value speech fallback;
- Insert+Up fallback path;
- Windows virtual-key behavior with Cyrillic keysyms;
- Simple and Advanced search focus/announcement;
- graceful Windows UIA provider enablement;
- dependency declaration;
- PyInstaller collection and frozen self-test integration.

Focused accessibility/build group: **40/40 passed**.

Complete active project suite: **470/470 passed**.

Breakdown of the final full run: **136 + 127 + 114 + 53 + 40 = 470**.

## Platform limitation

The automated environment is Linux/Xvfb. It validates Tk behavior, code paths and build configuration, but cannot emulate real Windows UI Automation or confirm how an installed NVDA/JAWS version intercepts `Insert+Up`. A real Windows reader smoke test is therefore still the final acceptance check for this specific accessibility behavior.
