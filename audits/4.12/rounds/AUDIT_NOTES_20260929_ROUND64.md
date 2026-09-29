# Round 64 — Qt offscreen font-directory hardening

The Windows Qt build log showed `QFontDatabase: Cannot find font directory .../PySide6/lib/fonts` during the offscreen accessibility preflight. Qt 6/PySide6 no longer ships that legacy fonts directory.

Applied fix:

- `build_qt_exe.bat` seeds `QT_QPA_FONTDIR` from `%WINDIR%\Fonts` for manual builds when the caller has not already set it.
- `build_qt_ci.ps1` independently performs the same guarded initialization so direct CI-script invocations are covered too.
- an explicit caller-supplied `QT_QPA_FONTDIR` is preserved.
- no font binaries are copied or bundled into the repository/EXE; normal Windows runtime rendering continues to use the platform font stack.

This targets the offscreen self-test warning only; it does not change application UI fonts or packaging contents.
