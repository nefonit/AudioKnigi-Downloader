# Audit 4.7.7

This audit was performed against the actual uploaded **4.7.6 Universal Accessibility ZIP**, not incomplete source snippets.

## Confirmed false positives

- `audioknigi/app.py` is complete and compiles. It contains `player_time_var`, UI construction, startup bindings, and the rest of `AudioKnigiApp`.
- `AudioKnigiApp.t()` exists and delegates to `i18n.tr()`, so the `self.t(...)` calls in `actions.py` are valid.
- `QueueItem` is mapping-compatible, so `x["url"]` was not a runtime `TypeError`; nevertheless, restore code now uses the typed `x.url` style for consistency.
- The PowerShell WinRT notation for `XmlDocument` commonly uses `Windows.Data.Xml.Dom.XmlDocument` as both type and WinRT assembly name. 4.7.7 makes the path more explicit by constructing the WinRT object directly with `::New()`.
- The language settings combo intentionally stores the display label and `change_language()` maps it to a code. 4.7.7 additionally accepts an already-normalized code.

## Confirmed fixes

- Safe `MappingDataclass.to_dict()` without `dataclasses.asdict()` deep-copying GUI/native image objects.
- Explicit empty-cover-payload handling.
- Native/forward-slash home path masking in privacy logs.
- Normalization state synchronization when restoring a single interrupted book.
- Reverse synchronization of the friendly MP3/M4B selector.
- Safer speed-label initialization.
- CTkLabel-aware nearby-label discovery for NVDA/JAWS semantic announcements.
- Explicit WinRT object construction in the PowerShell toast fallback while keeping user text Base64-only.

## Regression coverage

`tests/test_audit_477.py` covers these findings and is executed in both CI and release workflows.
