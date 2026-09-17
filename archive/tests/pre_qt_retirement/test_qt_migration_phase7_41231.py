from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tomllib

from audioknigi.qt_runtime_audit import audit_loaded_runtime, find_forbidden_loaded


ROOT = Path(__file__).resolve().parents[1]
QT_DIR = ROOT / "audioknigi" / "qt"


def test_runtime_audit_detects_legacy_frontend_and_external_modules():
    names = {
        "audioknigi.core",
        "audioknigi.qt.main_window",
        "tkinter.ttk",
        "pygame.mixer",
        "audioknigi.ui_kit",
    }
    found = find_forbidden_loaded(names)
    assert "tkinter.ttk" in found
    assert "pygame.mixer" in found
    assert "audioknigi.ui_kit" in found
    assert not audit_loaded_runtime({"audioknigi.core", "PySide6.QtWidgets"}).forbidden_loaded


def test_static_qt_import_graph_audit_passes_without_pyside6_installed():
    proc = subprocess.run(
        [sys.executable, "tools/qt_import_audit.py", "--verbose"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "QT IMPORT AUDIT: OK" in proc.stdout
    assert "audioknigi.download_engine" in proc.stdout
    assert "audioknigi.downloader" in proc.stdout


def test_qt_runtime_requirements_and_build_requirements_are_separated():
    runtime = (ROOT / "requirements-qt.txt").read_text(encoding="utf-8").lower()
    build = (ROOT / "requirements-qt-build.txt").read_text(encoding="utf-8").lower()
    assert "pyside6>=6.8,<7" in runtime
    assert "requests" in runtime
    assert "playwright" in runtime
    assert "pillow" in runtime
    assert "mutagen" in runtime
    assert "pyinstaller" not in runtime
    for forbidden in ("pygame", "ttkbootstrap", "pystray", "plyer", "tkinterdnd2", "prismatoid", "tk-uia"):
        assert forbidden not in runtime
    assert "-r requirements-qt.txt" in build
    assert "pyinstaller" in build


def test_pyproject_qt_extra_no_longer_inherits_legacy_ui_dependencies():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    common = "\n".join(project["dependencies"]).lower()
    extras = project["optional-dependencies"]
    qt = "\n".join(extras["qt"]).lower()
    legacy = "\n".join(extras["legacy"]).lower()
    assert "pyside6>=6.8,<7" in qt
    for forbidden in ("pygame", "ttkbootstrap", "pystray", "plyer", "tkinterdnd2", "prismatoid", "tk-uia"):
        assert forbidden not in common
        assert forbidden not in qt
        assert forbidden in legacy


def test_qt_entry_has_frozen_runtime_and_edge_selftests_with_reports():
    text = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    for needle in (
        '"--qt-runtime-selftest"',
        '"--playwright-edge-selftest"',
        "AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT",
        "qt_runtime_frozen_selftest.txt",
        "AUDIOKNIGI_PLAYWRIGHT_SELFTEST_REPORT",
        "playwright_edge_qt_frozen_selftest.txt",
        "assert_qt_runtime_clean()",
        "QMediaPlayer",
        "QSystemTrayIcon",
        'channel="msedge"',
    ):
        assert needle in text


def test_qt_build_uses_isolated_venv_onefile_and_frozen_boundary_checks():
    bat = (ROOT / "build_qt_exe.bat").read_text(encoding="utf-8")
    ps = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    assert ".venv-qt" in bat
    assert "requirements-qt-build.txt" in bat
    assert "tools\\qt_import_audit.py --verbose" in bat
    for needle in (
        '"--onefile"',
        '"--windowed"',
        '"--collect-all", "playwright"',
        '"--copy-metadata", "PySide6"',
        '"--add-binary", "$ffmpeg;."',
        '"--add-binary", "$ffprobe;."',
        '"--exclude-module", "tkinter"',
        '"--exclude-module", "pygame"',
        '"--exclude-module", "pystray"',
        '"--exclude-module", "prism"',
        '"--exclude-module", "audioknigi.ui_kit"',
        "Analysis-00.toc",
        "--qt-runtime-selftest",
        "--playwright-edge-selftest",
    ):
        assert needle in ps


def test_qt_source_launcher_prefers_isolated_environment_and_runs_audit():
    text = (ROOT / "run_qt.bat").read_text(encoding="utf-8")
    assert ".venv-qt\\Scripts\\python.exe" in text
    assert "tools\\qt_import_audit.py" in text
    assert "requirements-qt.txt" in text


def test_migration_stage_is_phase7_or_later():
    text = (QT_DIR / "__init__.py").read_text(encoding="utf-8")
    import re
    match = re.search(r'QT_MIGRATION_STAGE = "phase-(\d+)"', text)
    assert match and int(match.group(1)) >= 7
