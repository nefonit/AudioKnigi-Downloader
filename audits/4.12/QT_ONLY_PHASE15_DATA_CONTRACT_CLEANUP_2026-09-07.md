# Qt-only Phase 15 audit — data contract and residual legacy cleanup

## Confirmed findings

1. `cover_cache` was produced as `(bytes, mime)` but Qt preview and queue persistence treated it as bare bytes.
2. `audioknigi.__init__` still exposed the retired `AudioKnigiApp` symbol.
3. `AudioKnigiQtWindow._choose_output_dir` had two definitions; the earlier one referenced obsolete `output_dir_edit`.
4. Phase 13/14 controls were not all included in the required accessibility contract.
5. Queue drop parsing used an artificial runtime-generated MIME-like object.
6. `core.py` still contained three Tk-only geometry helpers unused by the Qt runtime.

## Resolution

- Added `normalize_cover_cache()` and `cover_cache_bytes()` to the model layer.
- Queue JSON persists cover bytes and MIME type and remains backward compatible with old byte-only snapshots.
- Downloader normalizes cached/fetched covers before ID3 writing.
- Removed dead package export, duplicate chooser, artificial MIME wrapper and Tk geometry helpers.
- Accessibility audit now requires 125 persistent controls and declares 8 dynamic modal identifiers.

## Results

- `pytest -q tests`: 26 passed.
- `tools/full_parity_audit.py --require-legacy-retired`: PASS 61/61.
- `tools/qt_import_audit.py`: 39 modules, no legacy frontend path.
- Python compileall: PASS.
