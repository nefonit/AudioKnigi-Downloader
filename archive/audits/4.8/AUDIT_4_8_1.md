# Audit 4.8.1

This audit was performed against the exact uploaded 4.8.0 ZIP, not clipped source excerpts.

## Reported issues that were not present in the ZIP

- `audioknigi/app.py` is complete and compiles; it does not end at `self.embed`.
- `audioknigi/ui/easy_home.py` is complete and compiles; `refresh_sidebar()` has a complete `"Ожидает"` fallback.
- `AudioKnigiApp.t()` exists and delegates to `i18n.tr()`.
- `AudioKnigiApp.on_bandwidth_slider(self, _value=None)` already accepts the value passed by a ttk Scale.
- Relative imports in `audioknigi/ui/*.py` are intentional package-internal imports; these modules are not standalone entry points.

## Confirmed improvements

- `placeholder_text` was silently discarded by the native `CTkEntry` compatibility wrapper. 4.8.1 preserves it as semantic metadata and renders persistent visible examples at the relevant call sites without contaminating the real `StringVar`.
- `EasyHome._keyboardize()` still contained a dead CustomTkinter border fallback. 4.8.1 relies on native ttk focus styling and bindings instead.
- During runtime verification, the Settings page was found to require roughly 1800 px of vertical content while the normal window is smaller. 4.8.1 restores a keyboard-aware scroll viewport; the Canvas is passive and not focusable, while all child controls remain native Tk/ttk widgets.

## Regression coverage

`tests/test_audit_481.py` verifies source completeness, the translation helper, slider callback signature, placeholder/StringVar separation, screen-reader description, native focus behavior, and Settings scrolling/focus-follow.
