# Compact Windows EXE build audit — 4.12.31

## Goal

Reduce the Windows PyInstaller one-file size without removing accessibility, FFmpeg/FFprobe, drag-and-drop, Cloudflare DNS routing or the Playwright fallback.

## Root cause of the oversized EXE

The previous build explicitly set `PLAYWRIGHT_BROWSERS_PATH=0`, installed Playwright Chromium into the Python package and then used `--collect-all playwright`. This made PyInstaller embed the full browser distribution together with Playwright's Python/Node driver.

## Changes

- Removed `playwright install chromium` from both BAT entry points and `build_ci.ps1`.
- Removed any stale `playwright/driver/package/.local-browsers` directory before PyInstaller runs, so reusing an old `.venv` cannot silently re-embed Chromium.
- Playwright runtime now launches the installed stable Microsoft Edge with `channel="msedge"`.
- The Cloudflare-resolving localhost proxy and `--disable-quic` remain active for Playwright.
- Kept `--collect-all playwright` for Playwright's Python modules, JavaScript driver and Node executable; only the browser payload is omitted.
- Removed broad `--collect-all` calls for Pillow, Mutagen, pygame, tkinterdnd2, ttkbootstrap and pystray. Standard PyInstaller hooks/static imports are used; ttkbootstrap data is collected explicitly and `pystray._win32` is an explicit hidden import.
- Prism and `tk_uia` remain fully collected; the exact Prism CFFI extensions are still explicitly bundled.
- FFmpeg and FFprobe remain embedded, so media processing stays portable.
- Added a pre-build Edge launch check and a **frozen EXE** `--playwright-edge-selftest`. The build fails if the final EXE cannot control installed Edge.
- Build output now prints the final EXE size in MB.

## Compatibility trade-off

The compact build now requires Microsoft Edge to be installed on the Windows machine. It no longer carries its own Chromium copy. This is an intentional size/reliability trade-off.

## Regression validation

Added `tests/test_compact_exe_build_41231.py`. The complete active pytest suite is **499/499 passed**. `test_visual_ui.py` is a module-level smoke test with no pytest test functions; its import/assertion pass was verified separately under Xvfb.

## Expected effect

The exact Windows size must be measured on the user's Windows build machine because this Linux environment cannot produce the target EXE. The several-hundred-megabyte embedded Chromium payload is no longer eligible for collection, so the Windows one-file output should be substantially smaller. FFmpeg/FFprobe plus the Playwright Node driver remain significant contributors.
