from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "tools" / "pyinstaller_bootstrap.py"
BUILD_PS1 = ROOT / "build_qt_ci.ps1"
BUILD_BAT = ROOT / "build_qt_exe.bat"


def _load_bootstrap_module():
    spec = importlib.util.spec_from_file_location("round8_pyinstaller_bootstrap", BOOTSTRAP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_imports_without_pyinstaller_and_selftests():
    module = _load_bootstrap_module()
    assert callable(module.prepare_platform_for_pyinstaller)
    proc = subprocess.run(
        [sys.executable, str(BOOTSTRAP), "--bootstrap-selftest"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PYINSTALLER BOOTSTRAP SELFTEST: OK" in proc.stdout



def test_prepare_platform_for_pyinstaller_disables_wmi_on_simulated_py314_windows(monkeypatch):
    module = _load_bootstrap_module()
    sentinel = object()
    monkeypatch.setattr(module.sys, "platform", "win32")
    monkeypatch.setattr(module.sys, "version_info", (3, 14, 7))
    monkeypatch.setattr(module.platform, "_wmi", sentinel, raising=False)
    assert module.prepare_platform_for_pyinstaller() is True
    assert module.platform._wmi is None

def test_bootstrap_disables_only_platform_wmi_before_pyinstaller_import():
    text = BOOTSTRAP.read_text(encoding="utf-8")
    prepare_pos = text.index("prepare_platform_for_pyinstaller()", text.index("def main"))
    import_pos = text.index("from PyInstaller.__main__ import run")
    assert prepare_pos < import_pos
    assert 'sys.platform != "win32"' in text
    assert "sys.version_info < (3, 14)" in text
    assert "platform._wmi = None" in text
    assert "platform.win32_ver =" not in text


def test_powershell_build_uses_bootstrap_instead_of_python_m_pyinstaller():
    text = BUILD_PS1.read_text(encoding="utf-8-sig")
    assert 'tools\\pyinstaller_bootstrap.py' in text
    assert '& $PythonExe $pyinstallerBootstrap "--bootstrap-selftest"' in text
    assert "& $PythonExe $pyinstallerBootstrap @arguments" in text
    assert '"-m", "PyInstaller"' not in text


def test_batch_requires_bootstrap_file_before_build():
    text = BUILD_BAT.read_text(encoding="utf-8-sig")
    assert 'if not exist "tools\\pyinstaller_bootstrap.py" (' in text
