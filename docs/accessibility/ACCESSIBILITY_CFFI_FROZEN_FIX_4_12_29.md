# AudioKnigi Downloader 4.12.29 — Prism CFFI frozen packaging fix

The Windows 4.12.28 self-test correctly exposed a real PyInstaller omission:
`ModuleNotFoundError: No module named prism._prism_cffi`.

Prismatoid uses out-of-line CFFI bindings. The runtime needs both:
- `prism._prism_cffi` (Prism's compiled binding extension);
- `_cffi_backend` (CFFI runtime extension).

4.12.29 makes both explicit at three levels:
1. PyInstaller hook hidden imports and binary collection.
2. `build_ci.ps1` resolves the exact `.pyd` files from the Python 3.14.7 build environment and adds them with `--add-binary`.
3. The finished EXE self-test imports both compiled modules and records their paths.

The Windows Prismatoid minimum is raised to 0.18.2.

The frozen self-test report also has a default path beside the EXE, so a windowed process cannot lose the diagnostic merely because an environment variable is unavailable.
