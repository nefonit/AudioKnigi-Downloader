from pathlib import Path
import ast
import importlib.util
import subprocess
import sys

from audioknigi.qt import QT_MIGRATION_STAGE
from audioknigi.qt.full_parity import FULL_PARITY_ITEMS, full_parity_complete, parity_keys

ROOT = Path(__file__).resolve().parents[1]


def _load_audit_module():
    path = ROOT / "tools" / "full_parity_audit.py"
    spec = importlib.util.spec_from_file_location("full_parity_audit_phase13", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_phase13_stage_and_complete_manifest():
    assert QT_MIGRATION_STAGE == "phase-13"
    assert len(FULL_PARITY_ITEMS) == 61
    assert len(parity_keys()) == 61
    assert full_parity_complete()


def test_strict_pre_retirement_parity_is_61_of_61():
    mod = _load_audit_module()
    result = mod.audit(ROOT, require_legacy_retired=False)
    assert result["ok"], result["issues"]
    assert result["passed"] == result["total"] == 61


def test_qt_runtime_import_graph_stays_out_of_legacy_frontend():
    proc = subprocess.run([sys.executable, str(ROOT / "tools/qt_import_audit.py")], cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "no legacy frontend path" in proc.stdout.lower()


def test_phase13_has_no_deferred_parity_items():
    assert all(item.complete for item in FULL_PARITY_ITEMS)
    labels = "\n".join(item.label for item in FULL_PARITY_ITEMS)
    for required in ("Мастер первого запуска", "Простой режим", "Drag-and-drop", "Голосовые/системные звуки", "Пауза очереди"):
        assert required in labels


def test_phase13_new_qt_surfaces_exist():
    for rel in (
        "audioknigi/qt/full_parity.py",
        "audioknigi/qt/event_sounds.py",
        "audioknigi/qt/speed_graph.py",
        "audioknigi/qt/onboarding.py",
        "tools/full_parity_audit.py",
        "tools/build_qt_only_source.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_event_sounds_are_qt_multimedia_not_legacy_audio():
    text = (ROOT / "audioknigi/qt/event_sounds.py").read_text(encoding="utf-8")
    assert "QMediaPlayer" in text
    tree = ast.parse(text)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0].lower())
    assert "pygame" not in roots


def test_extended_columns_and_easy_mode_are_real_qt_code():
    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    tracks = (ROOT / "audioknigi/qt/track_model.py").read_text(encoding="utf-8")
    assert "_build_easy_page" in main and "easy_universal_action" in main
    assert "def dropEvent" in main and "_queue_drag_reordered" in main
    for value in ('"Начало"', '"Конец"', '"Источник"'):
        assert value in tracks


def test_accessibility_contracts_survive_phase13_expansion():
    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    for marker in (
        'focus_table_row(self.search_table, 0, column=1, focus=True)',
        'QShortcut(QKeySequence("Return"), self.search_table',
        'QAction("Доступность и горячие клавиши…", self)',
        'accessibility_help.setShortcut(QKeySequence("F1"))',
    ):
        assert marker in main


def test_qt_only_builder_declares_all_retired_runtime_paths():
    audit = _load_audit_module()
    builder = (ROOT / "tools/build_qt_only_source.py").read_text(encoding="utf-8")
    for rel in audit.LEGACY_UI_PATHS:
        assert rel in builder or "LEGACY_UI_PATHS" in builder
