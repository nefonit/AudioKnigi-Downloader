from __future__ import annotations

"""Launch PyInstaller without Python 3.14's Windows WMI version probe.

CPython 3.14's platform.win32_ver() prefers a WMI query. On some Windows
machines that query can block indefinitely before PyInstaller's CLI has even
started.  CPython already contains a normal non-WMI fallback based on
sys.getwindowsversion()/the `ver` command.  Setting platform._wmi to None makes
platform.win32_ver() take that built-in fallback immediately; no OS version is
forged and PyInstaller itself is otherwise left untouched.
"""

import platform
import sys


def prepare_platform_for_pyinstaller() -> bool:
    """Disable only the blocking CPython WMI probe used by win32_ver()."""
    if sys.platform != "win32" or sys.version_info < (3, 14):
        return False
    if not hasattr(platform, "_wmi"):
        return False
    platform._wmi = None  # type: ignore[attr-defined]
    return True


def _bootstrap_selftest() -> int:
    # The mapping/fallback itself belongs to CPython; this helper merely makes
    # sure our bootstrap is side-effect free on non-Windows and importable in
    # build/test environments that do not have PyInstaller installed.
    changed = prepare_platform_for_pyinstaller()
    expected = sys.platform == "win32" and sys.version_info >= (3, 14) and hasattr(platform, "_wmi")
    if changed != expected:
        print(f"PYINSTALLER BOOTSTRAP SELFTEST: FAILED changed={changed} expected={expected}")
        return 1
    print(f"PYINSTALLER BOOTSTRAP SELFTEST: OK (wmi_bypass={changed})")
    return 0


def main() -> int:
    if "--bootstrap-selftest" in sys.argv[1:]:
        return _bootstrap_selftest()

    prepare_platform_for_pyinstaller()
    # Import only after the WMI probe has been disabled; importing PyInstaller
    # imports PyInstaller.compat, which calls platform.win32_ver() immediately.
    from PyInstaller.__main__ import run

    run(sys.argv[1:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
