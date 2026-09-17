# Qt frozen TOC audit fix — 2026-09-06

## Observed failure
The Qt one-file EXE itself was built successfully by PyInstaller 6.22.2, but the post-build gate stopped with:

`Legacy module leaked into Qt PyInstaller analysis: 'tkinter'`

The build command already passed `--exclude-module tkinter`, `_tkinter`, `ttkbootstrap`, and the other legacy frontend exclusions.

## Root cause
`Analysis-00.toc` is not just the collected module list. PyInstaller serializes the full `Analysis._GUTS` tuple into this file. That tuple contains both calculated TOCs (`pure`, `binaries`, and so on) **and input metadata**, including the `excludes` list itself.

The previous audit loaded the entire file as raw text and searched for the substring `'tkinter'`. Because `tkinter` intentionally appears in the exclusion metadata, the audit reported a false leak after a successful build.

## Fix
- Added `tools/qt_frozen_module_audit.py`.
- It parses `Analysis-00.toc` with `ast.literal_eval`.
- It inspects only real 3-field PyInstaller TOC entries whose type is a collected Python/module entry (`PYSOURCE`, `PYMODULE*`, `EXTENSION`).
- It ignores metadata-only occurrences such as the `excludes` list.
- `build_qt_ci.ps1` now runs this structural audit instead of a raw `Contains()` substring scan.
- The legacy module deny-list remains strict; the check was corrected, not weakened.
- Added regression coverage proving that an exclusion-list occurrence passes while an actual `('tkinter', ..., 'PYMODULE')` entry fails.

## Build state before this fix
The user's Windows build log confirmed:
- Python 3.14.7 x64;
- PySide6 6.11.2;
- PyInstaller 6.22.2;
- static Qt import boundary: OK;
- Qt Multimedia/tray: OK;
- `dist\\AudioKnigiDownloader_Qt.exe` built successfully;
- failure happened only in the old post-build raw-text TOC check.
