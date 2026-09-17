# AudioKnigi Downloader 4.12.20 — MP3-only and Complete Help Center

## MP3 is the only output format

The current application no longer exposes or executes an M4B workflow. The output-format selector, preview, M4B builder/tagging path, M4B queue/resume state and related onboarding/settings controls were removed. Existing installations that still contain an old output-format preference are migrated to the current MP3-only behavior.

## Keyboard audit

The runtime bindings were audited against `ActionsMixin`, Book/Search/History tables, combobox behavior, accessible buttons and text controls. The Help Center now documents global navigation, direct tab access, quality shortcuts, context menus, part toggling, search/history activation, combobox operation and standard editing shortcuts.

## Complete Help Center

The Help Center is now a scrollable topic-based user manual. It explains: supported sources/search, simple and advanced modes, the Book tab and narration selection, bulk part selection, mini-player, downloads and duplicate protection, cancel behavior, queue, history, quality, all settings groups, folders/naming/metadata, backup/restore, accessibility, every documented shortcut, app.log/BOOK FLOW diagnostics and interrupted-download recovery.

## Build note

Windows EXE build scripts remain hard-pinned to CPython 3.14.7 x64. Source tests may be executed in the available Linux environment; that is not represented as a Windows EXE validation.
