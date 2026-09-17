# Audit 4.8.22

## Confirmed / fixed

- Small-screen scaling could still require an 800 px minimum on a display narrower than 800 px. Minimum width/height are now capped by the usable screen dimensions.
- `normalize_audio_var` was a legacy compatibility value that could lag behind `normalization_mode_var`; it is now an automatically derived mirror.
- Unfinished-source discovery only recognized `_source*.mp3`; it now also recognizes repair sources and common audio container suffixes, with one final-file directory scan per directory.
- The CTk accessibility fallback matched an exact list of class names; it now tolerates CTk wrapper suffixes while excluding non-interactive CTk controls.
- Prismatoid keeps its official `prism` import, plus a defensive `prismatoid` fallback for alternate packaging.
- Tk base scaling now rejects implausible values and can fall back to physical pixels-per-inch.

## False positives / already correct

- `requirements.txt` is a separate file; no dependency line is concatenated with Python code.
- `ui_kit.py` is complete and `AccessibleLabel` is not truncated.
- The official Prismatoid distribution currently packages the Python module as `prism`; `from prism import BackendId, Context` is therefore the primary correct import.
- `single` normalization is intentionally supported by the FFmpeg backend.
- Accessibility polling already tracks/cancels its Tk `after()` callbacks during shutdown.
- The downloader currently creates `_source*.mp3` internally; broader suffix recognition is future-proofing and recovery hardening.
- The runtime normalization variables are worker snapshots by design; only the legacy UI boolean required continuous synchronization.

## Validation

- `python -m compileall -q audioknigi tests`: OK.
- `tests/test_audit_4822.py`: 7/7 passed.
- Audit regression modules: 137/137 passed.
- Additional Tk/UI pytest regression group: 23/23 passed (all tests reached PASS; the legacy combined process may retain a Tk callback after pytest summary, so Tk-heavy groups are normally isolated).
- Selected script-style smoke suites for core, accessibility, DnD, hardening, maintenance, threading, queue UI, search, user experience and visual UI: 10/10 passed.
