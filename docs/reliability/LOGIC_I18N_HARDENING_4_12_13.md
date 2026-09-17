# AudioKnigi Downloader 4.12.13 — Logic & i18n Hardening

This release turns several UI-text-derived decisions into stable internal state.

## Confirmed fixes

- Semantic workflow status kinds replace broad Russian substring scanning.
- UI mode is stored as `easy` / `advanced` and localized only for display.
- Queue outcomes use a stable `status_code`.
- Accessibility polling/scheduling is marshalled to the Tk main thread when invoked elsewhere.
- Track numbering widens automatically for books with 100+ parts.
- Completion size and Listen actions use recursive file discovery for nested disc folders.
- Simple-mode Drag-and-Drop hint is refreshed after target registration.
- Playlist de-duplication uses a set while preserving order.
- Metadata fallback prefers JSON-LD Book/Audiobook/CreativeWork data and ignores unrelated JavaScript `name` properties.
- Native Tk `unbind(sequence, funcid)` is preferred before the legacy Tcl-script fallback.
- Player-position shutdown waiting is bounded.

## Audit findings intentionally not changed

Several reported syntax/truncation issues were artifacts of copied or truncated snippets rather than the actual 4.12.12 ZIP: `split_one` and `Tooltip` are complete, no `[source: ...]` markers or requirements lines are embedded in Python modules, registered ttk styles exist, and Cyrillic keysyms are normalized before lookup.

## Build

Windows standalone builds remain pinned to CPython 3.14.7 x64 and retain the real FFmpeg/FFprobe validation/bundling introduced in 4.12.11.
