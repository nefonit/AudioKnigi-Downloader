# AudioKnigi Downloader 4.12.37 — quality-gate and parser hardening

Date: 2026-09-13

## Scope

Follow-up review of the 4.12.36 structured Qt-only tree focused on the audit tools themselves, parser edge cases, recovery bookkeeping, source-provider constants, localization and accessibility contracts.

## Confirmed fixes

- `tools/exception_audit.py` now identifies every broad silent handler by `path:function:handler#occurrence`. This prevents a second handler in the same function from inheriting an earlier approval. `except: pass` and `except BaseException: pass` are included. The allowlist was migrated from 73 function-level keys to 113 exact reviewed occurrences.
- `tools/unused_import_audit.py` now traverses module-level compound statements (`if`, `try/except/else/finally`, loops, `with`, `match`) while intentionally skipping function/class-local lazy imports. Quoted type annotations are treated as legitimate references.
- Windows acceptance propagates the hidden `--allow-non-windows` contract through candidate validation, status refresh, automated/manual reporting and final status.
- Qt localization source scanning accepts keyword-form `ui_text(..., russian_text=...)`; Qt import audit no longer carries an identity alias table.
- Qt self-test DeferredDelete flushing uses a positional call first and has keyword/no-argument fallbacks for binding differences.
- Sidecar duplicate matching returns `False` rather than raising for a malformed current `Track.index`. History-change callbacks run through the engine callback safety boundary.
- Knigavuhe JavaScript argument parsing recognizes ES6 backtick strings. Provider/parser host names reuse the canonical host constants from `sources.py`.
- Expired media recovery can infer the missing selected chapter from a plain `requests.HTTPError` response URL when `track_indices` metadata was not attached.
- FFprobe parsing validates that `streams` is a non-empty list whose first item is a mapping before reading codec fields.
- Diagnostic settings sanitization removed a redundant branch; queue recovery treats empty or fully-invalid legacy selected-index lists as whole-book recovery.
- Added the missing Ukrainian dotted search prompt, localized the Audiobookshelf secret-field accessibility description, added `easy_book_cover` to the required accessibility contract, and advanced the runtime marker to `qt-only-4.12.37`.

## Reviewed without behavior change

- `_is_transient_error` remains in the downloader flow as a compatibility/source-boundary helper used by archived source-shape regressions; removing it would add no runtime benefit.
- Full replacement of every literal domain inside user-facing messages was not attempted; only provider/parser identity constants were centralized. Human-readable error text intentionally remains explicit.
- Existing hidden compatibility controls in the Qt UI remain intentional parity/accessibility contract objects.

## Validation

Working-tree validation before packaging:

- `python -m pytest -q` — 135 passed.
- `python tools/full_parity_audit.py --root . --require-legacy-retired` — PASS 61/61.
- `python tools/qt_localization_audit.py --root .` — OK (ru/uk/de/en).
- `python tools/qt_import_audit.py` — OK, 72 project modules, no legacy frontend path.
- `python tools/exception_audit.py` — PASS, 113 exact reviewed broad silent handlers.
- `python tools/unused_import_audit.py` — OK, 31 implementation modules.
- `python tools/undefined_global_audit.py` — OK, 76 package modules.
- `python tools/historical_regression_audit.py` — PASS, 273 archived tests; no unexpected regression.

The final archive is re-extracted and validated again before release.
