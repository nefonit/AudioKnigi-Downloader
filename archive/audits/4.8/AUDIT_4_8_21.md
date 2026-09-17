# Audit 4.8.21

## Confirmed / fixed

- Added strict normalization mode validation while preserving the intentionally supported legacy `single` one-pass loudnorm path.
- Made `_apply_scale()` safe before `EasyHome` exists and centralized robust focus of the easy URL field after onboarding.
- Hardened malformed cover payload hashing so exceptional objects do not share an empty digest.
- Hardened Settings trace ownership/removal and removed duplicate `folder_template_var` setup.
- Canonicalized Canvas scrollregion comparisons.
- Hardened `install_destroy_cleanup()` for unusual explicit-owner calls without reintroducing `<Destroy>` bindings.
- Made player tick rescheduling safe for isolated mixin hosts.

## False positives / already correct

- `app.py` and requirements are separate, complete files; `compileall` passes.
- `normalization_mode="single"` is supported by the downloader and produces one-pass FFmpeg `loudnorm`; `two_pass` remains the quality mode used by the UI preset.
- `_update_bandwidth_label()` exists on `AudioKnigiApp`.
- `_apply_scale()` was already wrapped in exception handling; 4.8.21 additionally makes component access explicit.
- `easy_url_entry` is intentionally published on `AudioKnigiApp` by `EasyHome`; 4.8.21 also stores it on the component for future-proofing.
- Accessibility polling already tracks and cancels every scheduled Tk callback in `AccessibilityManager.close()`.
- `SearchTab` already checks `identify_row()` before opening a result.
- `CTkTextbox` already checks selection presence before copy/cut.
- `install_destroy_cleanup()` functions are stored on widget instances and therefore do not receive an implicit Python `self`; a regression test now proves both normal and unusual explicit-owner calls.
- Prismatoid is the distribution name; its Python module is `prism`.

## Validation

- `python -m compileall -q audioknigi tests`: OK.
- Audit regression 4.8.9–4.8.21: 130/130 passed.
- All collected pytest function tests: 153 passed in isolated Tk/Xvfb processes.
- Script-style smoke/audit modules: 27/27 passed.
- `--version`: 4.8.21.
- `--ci-selftest`: OK.
