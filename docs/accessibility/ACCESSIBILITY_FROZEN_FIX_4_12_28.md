# AudioKnigi Downloader 4.12.28 — Frozen Prism/NVDA/JAWS fix

## What the Windows log proved

The 4.12.27 Windows log showed that NVDA was running and the application's own
Tab/focus router worked: focus moved through visible controls and generated
correct accessible descriptions.  The bridge itself remained inactive because
Prism could not be loaded from the frozen application.

The old runtime code then tried `import prismatoid` as a compatibility fallback.
That was incorrect: `prismatoid` is the distribution name on PyPI, while the
official Python import name is `prism`.  The fallback also hid the original
`prism` import exception, which could have been a missing native DLL/submodule.

## Changes in 4.12.28

- Runtime imports only the official `prism` package and logs the full original
  traceback when it fails.
- Added `hook-prism.py` using PyInstaller `collect_all("prism")` and copied
  `prismatoid` distribution metadata.
- Build arguments explicitly collect Prism binaries/data and hidden imports.
- Added `--accessibility-import-selftest` to the application.
- After PyInstaller creates the one-file EXE, `build_ci.ps1` launches that EXE
  in accessibility self-test mode.
- The self-test verifies the frozen `prism` import, `BackendId.NVDA`,
  `BackendId.JAWS`, `Context`, and Prism's native payload directory.
- The build is rejected if that frozen self-test fails.  A diagnostic report is
  written to `dist/accessibility_frozen_selftest.txt`.

This is deliberately stronger than checking Prism in the build virtualenv: the
check now proves that the final EXE contains the accessibility dependency.
