# AudioKnigi Downloader 4.8.7 — Tkinter recursion hardening

- Removed `update_idletasks()` from scaling/responsive-layout and clipboard callbacks.
- Replaced idle-time responsive relayout with a debounced timer and a reentrancy guard.
- Added hysteresis around the responsive breakpoint to prevent stack/unstack oscillation.
- Added reentrancy guards to scrollable-frame `<Configure>` callbacks.
- Removed the root `<Map>` clipboard binding that received mapping events from descendants.
- Debounced clipboard focus checks without repeated cancel/re-arm cycles.
- A `RecursionError` is no longer followed by a modal `messagebox` nested event loop.
- Preserved 4.8.6 timing-column fixes and 4.8.5 theme/undo fixes.

## Reproduced root cause

A full `AudioKnigiApp()` teardown reproduced `RecursionError` inside `tkinter._substitute`.
The trigger was the tooltip owner's `<Destroy>` binding: its callback called Tk operations while Tk was already recursively destroying the widget tree. The owner `<Destroy>` binding was removed; application-level destruction now completes without a callback recursion.
