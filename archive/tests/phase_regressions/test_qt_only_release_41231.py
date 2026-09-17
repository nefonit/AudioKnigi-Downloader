from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LEGACY = [
    "audioknigi_gui.py", "audioknigi/app.py", "audioknigi/actions.py", "audioknigi/accessibility.py",
    "audioknigi/dnd.py", "audioknigi/help_center.py", "audioknigi/onboarding.py", "audioknigi/player.py",
    "audioknigi/queue_manager.py", "audioknigi/search.py", "audioknigi/storage.py", "audioknigi/tray.py",
    "audioknigi/ui_kit.py", "audioknigi/event_sounds.py", "audioknigi/event_bus.py", "audioknigi/library_visuals.py",
    "audioknigi/notifications.py", "audioknigi/ui_state.py", "audioknigi/visuals.py", "audioknigi/ui",
]

def test_legacy_runtime_is_absent():
    assert not [p for p in LEGACY if (ROOT / p).exists()]

def test_strict_full_parity_gate_passes_after_retirement():
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    proc = subprocess.run([sys.executable, str(ROOT / "tools/full_parity_audit.py"), "--root", str(ROOT), "--require-legacy-retired"], cwd=ROOT, env=env, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS 61/61" in proc.stdout

def test_qt_import_boundary_is_clean():
    proc = subprocess.run([sys.executable, str(ROOT / "tools/qt_import_audit.py")], cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "no legacy frontend path" in proc.stdout.lower()

def test_standard_install_is_qt_only():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    assert "pyside6" in text
    for token in ("ttkbootstrap", "pygame-ce", "pystray", "tkinterdnd2", "prismatoid", "tk-uia"):
        assert token not in text

def test_default_launcher_has_no_legacy_fallback():
    text = (ROOT / "run.bat").read_text(encoding="utf-8").lower()
    assert "audioknigi_qt.py" in text
    assert "audioknigi_gui.py" not in text
    assert "audioknigidownloader.exe" not in text
