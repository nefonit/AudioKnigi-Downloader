# Audit 4.7.10

This release was produced from the exact uploaded 4.7.9 ZIP.

## Confirmed and fixed

1. `SettingsTab._speed_changed()` called `_save_settings()` unconditionally. It now checks for a callable persistence hook.
2. Settings `trace_add` callbacks had no explicit destruction lifecycle. 4.7.10 tracks the variables and trace IDs per SettingsTab instance, removes old traces during rebuild, and detaches them when the settings container is destroyed.
3. `SettingsTab` assumed `segment_count_var` and `output_mode_var` always existed. The tab now repairs missing/invalid variables with safe Tk `StringVar` fallbacks.

## Reported issues that were not present in the uploaded archive

1. `app.py` is not truncated. The exact file compiles successfully and ends with complete class methods.
2. `AudioKnigiApp.t()` exists and delegates to `i18n.tr(self.language, key, **kwargs)`, so `self.t(...)` calls in `ActionsMixin` are valid for the application class.
3. The CTkLabel fallback font behavior is cosmetic and does not prevent rendering or accessibility.

## Regression coverage

`tests/test_audit_4710.py` verifies source compilation, the translation helper, guarded speed persistence, automatic variable repair, trace installation/removal, and child-vs-container Destroy filtering.
