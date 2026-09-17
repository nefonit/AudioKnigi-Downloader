from __future__ import annotations

"""Build the Phase 13 Qt-only source tree after strict 1:1 parity is proven.

The working migration tree deliberately retains the legacy Tk UI until the
pre-retirement regression is complete.  This tool creates a *new* source tree,
preserves the old test suite under audits/reference_tests_pre_retirement, and
then removes all retired Tk runtime/launcher/build surfaces.
"""

import argparse
import json
import shutil
from pathlib import Path

from full_parity_audit import LEGACY_UI_PATHS, audit

CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
OBSOLETE_TOP_LEVEL = {
    "audioknigi_gui.py",
    "build_exe.bat",
    "build_exe_fixed.bat",
    "build_ci.ps1",
    "hook-prism.py",
    "hook-tkinterdnd2.py",
    "rollback_to_legacy.bat",
    "promote_qt_launcher.bat",
    "check_default_launcher.bat",
    "PHASE11_NEXT_STEPS.txt",
    "PHASE12_NEXT_STEPS.txt",
    "make_source_release.py",
}
OBSOLETE_INTERNAL = {
    "audioknigi/qt/promotion_contract.py",
    "tools/qt_launcher_promotion.py",
}
LEGACY_DEPENDENCY_TOKENS = (
    "pygame-ce", "ttkbootstrap", "pystray", "plyer", "tkinterdnd2", "prismatoid", "tk-uia"
)


def _ignore(_dir: str, names: list[str]) -> set[str]:
    ignored = {name for name in names if name in CACHE_NAMES or name.endswith(".pyc")}
    ignored.update(name for name in names if name in {".venv", ".venv-qt", "build", "dist"})
    return ignored


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _write_run_bat(root: Path) -> None:
    (root / "run.bat").write_text(
        r'''@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

rem Phase 13 Qt-only launcher.  The legacy Tk UI has been retired from this tree.
set "QT_EXE=%CD%\dist\AudioKnigiDownloader_Qt.exe"
if exist "%QT_EXE%" (
  start "" "%QT_EXE%" %*
  endlocal
  exit /b 0
)

set "QT_PYTHON=%CD%\.venv-qt\Scripts\python.exe"
if exist "%QT_PYTHON%" (
  "%QT_PYTHON%" audioknigi_qt.py %*
  set "RC=%ERRORLEVEL%"
  endlocal & exit /b %RC%
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3.14 audioknigi_qt.py %*
  set "RC=%ERRORLEVEL%"
  endlocal & exit /b %RC%
)
python audioknigi_qt.py %*
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
''',
        encoding="utf-8",
    )


def _write_pyproject(root: Path) -> None:
    (root / "pyproject.toml").write_text(
        '''[build-system]\nrequires = ["setuptools>=68"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "audioknigi-downloader"\ndynamic = ["version"]\ndescription = "Accessible Qt audiobook downloader and library manager for Windows"\nreadme = "README.md"\nrequires-python = ">=3.11"\ndependencies = [\n  "PySide6>=6.8,<7",\n  "requests",\n  "playwright",\n  "Pillow",\n  "mutagen",\n]\n\n[project.optional-dependencies]\nbuild = ["pyinstaller>=6.10"]\n\n[tool.setuptools.dynamic]\nversion = {attr = "audioknigi.version.__version__"}\n\n[tool.setuptools.packages.find]\ninclude = ["audioknigi*"]\n''',
        encoding="utf-8",
    )
    runtime = "# Phase 13 Qt-only runtime dependencies.\nPySide6>=6.8,<7\nrequests\nplaywright\nPillow\nmutagen\n"
    (root / "requirements.txt").write_text(runtime, encoding="utf-8")
    (root / "requirements-qt.txt").write_text(runtime, encoding="utf-8")


def _patch_build_script(root: Path) -> None:
    path = root / "build_qt_ci.ps1"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for name in (
        "audioknigi.app", "audioknigi.actions", "audioknigi.accessibility", "audioknigi.player",
        "audioknigi.queue_manager", "audioknigi.search", "audioknigi.storage", "audioknigi.tray",
        "audioknigi.ui", "audioknigi.ui_kit",
    ):
        text = text.replace(f'    "--exclude-module", "{name}",\n', "")
    text = text.replace(
        'Write-Host "Promotion remains blocked until run_qt_acceptance.bat passes NVDA and JAWS for this exact EXE hash."',
        'Write-Host "Run run_qt_acceptance.bat with NVDA and JAWS for this exact EXE hash before release sign-off."',
    )
    path.write_text(text, encoding="utf-8-sig")


def _write_workflows(root: Path) -> None:
    wf = root / ".github" / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    (wf / "ci.yml").write_text('''name: Qt-only CI\n\non:\n  push:\n  pull_request:\n  workflow_dispatch:\n\npermissions:\n  contents: read\n\njobs:\n  qt-smoke:\n    runs-on: windows-latest\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: "3.14.7"\n          cache: pip\n      - shell: pwsh\n        run: |\n          python -m pip install --upgrade pip\n          python -m pip install -r requirements-qt-build.txt\n      - shell: pwsh\n        run: python -m compileall -q audioknigi audioknigi_qt.py tools\n      - shell: pwsh\n        run: python tools/full_parity_audit.py --root . --require-legacy-retired\n      - shell: pwsh\n        run: python tools/qt_import_audit.py --verbose\n      - shell: pwsh\n        run: python -m pytest -q tests\n''', encoding="utf-8")
    (wf / "release.yml").write_text('''name: Build Qt-only Windows EXE\n\non:\n  push:\n    tags: ["v*"]\n\npermissions:\n  contents: write\n\njobs:\n  windows-release:\n    runs-on: windows-latest\n    timeout-minutes: 90\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-python@v7\n        with:\n          python-version: "3.14.7"\n          cache: pip\n      - shell: pwsh\n        run: |\n          python -m pip install --upgrade pip\n          python -m pip install -r requirements-qt-build.txt\n          choco install ffmpeg -y --no-progress\n      - shell: pwsh\n        run: |\n          python tools/full_parity_audit.py --root . --require-legacy-retired\n          python tools/qt_import_audit.py --verbose\n      - shell: pwsh\n        run: .\\build_qt_ci.ps1\n      - uses: actions/upload-artifact@v7\n        with:\n          name: AudioKnigiDownloader-Qt-${{ github.ref_name }}-windows-x64\n          path: |\n            dist/AudioKnigiDownloader_Qt.exe\n            dist/qt_release_candidate.json\n''', encoding="utf-8")


def _write_active_tests(root: Path) -> None:
    tests = root / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_qt_only_release_41231.py").write_text(
        '''from pathlib import Path\nimport os\nimport subprocess\nimport sys\n\nROOT = Path(__file__).resolve().parents[1]\nLEGACY = [\n    "audioknigi_gui.py", "audioknigi/app.py", "audioknigi/actions.py", "audioknigi/accessibility.py",\n    "audioknigi/dnd.py", "audioknigi/help_center.py", "audioknigi/onboarding.py", "audioknigi/player.py",\n    "audioknigi/queue_manager.py", "audioknigi/search.py", "audioknigi/storage.py", "audioknigi/tray.py",\n    "audioknigi/ui_kit.py", "audioknigi/event_sounds.py", "audioknigi/event_bus.py", "audioknigi/library_visuals.py",\n    "audioknigi/notifications.py", "audioknigi/ui_state.py", "audioknigi/visuals.py", "audioknigi/ui",\n]\n\ndef test_legacy_runtime_is_absent():\n    assert not [p for p in LEGACY if (ROOT / p).exists()]\n\ndef test_strict_full_parity_gate_passes_after_retirement():\n    env = dict(os.environ, PYTHONPATH=str(ROOT))
    proc = subprocess.run([sys.executable, str(ROOT / "tools/full_parity_audit.py"), "--root", str(ROOT), "--require-legacy-retired"], cwd=ROOT, env=env, text=True, capture_output=True)\n    assert proc.returncode == 0, proc.stdout + proc.stderr\n    assert "PASS 61/61" in proc.stdout\n\ndef test_qt_import_boundary_is_clean():\n    proc = subprocess.run([sys.executable, str(ROOT / "tools/qt_import_audit.py")], cwd=ROOT, text=True, capture_output=True)\n    assert proc.returncode == 0, proc.stdout + proc.stderr\n    assert "no legacy frontend path" in proc.stdout.lower()\n\ndef test_standard_install_is_qt_only():\n    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()\n    assert "pyside6" in text\n    for token in ("ttkbootstrap", "pygame-ce", "pystray", "tkinterdnd2", "prismatoid", "tk-uia"):\n        assert token not in text\n\ndef test_default_launcher_has_no_legacy_fallback():\n    text = (ROOT / "run.bat").read_text(encoding="utf-8").lower()\n    assert "audioknigi_qt.py" in text\n    assert "audioknigi_gui.py" not in text\n    assert "audioknigidownloader.exe" not in text\n''',
        encoding="utf-8",
    )


def build(source: Path, dest: Path) -> dict:
    source = source.resolve()
    dest = dest.resolve()
    pre = audit(source, require_legacy_retired=False)
    if not pre["ok"] or pre["passed"] != pre["total"]:
        raise RuntimeError(f"strict parity is not complete: {pre['passed']}/{pre['total']} issues={pre['issues']}")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, ignore=_ignore)

    # Preserve the exact pre-retirement test suite as audit evidence, not as an
    # active Qt-only test suite that would import removed Tk modules.
    tests = dest / "tests"
    if tests.exists():
        archive_tests = dest / "audits" / "reference_tests_pre_retirement_phase13"
        archive_tests.parent.mkdir(parents=True, exist_ok=True)
        if archive_tests.exists():
            shutil.rmtree(archive_tests)
        shutil.move(str(tests), str(archive_tests))

    for rel in LEGACY_UI_PATHS:
        _remove(dest / rel)
    for rel in OBSOLETE_TOP_LEVEL:
        _remove(dest / rel)
    for rel in OBSOLETE_INTERNAL:
        _remove(dest / rel)

    _write_run_bat(dest)
    _write_pyproject(dest)
    _patch_build_script(dest)
    _write_workflows(dest)
    _write_active_tests(dest)

    (dest / "PHASE13_QT_ONLY.txt").write_text(
        "Phase 13 Qt-only release. Strict legacy-to-Qt capability audit: 61/61.\n"
        "The retired Tk runtime is intentionally absent from this source tree.\n"
        "The pre-retirement regression suite is preserved under audits/reference_tests_pre_retirement_phase13/.\n",
        encoding="utf-8",
    )
    post = audit(dest, require_legacy_retired=True)
    if not post["ok"]:
        raise RuntimeError("Qt-only retirement audit failed: " + "; ".join(post["issues"]))

    requirements = (dest / "requirements.txt").read_text(encoding="utf-8").lower()
    leaked_deps = [x for x in LEGACY_DEPENDENCY_TOKENS if x in requirements]
    if leaked_deps:
        raise RuntimeError("legacy dependencies remain in Qt-only requirements: " + ", ".join(leaked_deps))

    result = {
        "strict_parity_before_retirement": f"{pre['passed']}/{pre['total']}",
        "strict_parity_after_retirement": f"{post['passed']}/{post['total']}",
        "legacy_ui_present_after_retirement": post["legacy_ui_present"],
        "archived_pre_retirement_tests": "audits/reference_tests_pre_retirement_phase13",
    }
    verification = dest / "audits" / "4.12" / "phase13_qt_only_release.json"
    verification.parent.mkdir(parents=True, exist_ok=True)
    verification.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=".")
    parser.add_argument("--dest", required=True)
    args = parser.parse_args(argv)
    result = build(Path(args.source), Path(args.dest))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
