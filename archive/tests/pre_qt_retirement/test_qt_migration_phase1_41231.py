from __future__ import annotations

import ast
from pathlib import Path

from audioknigi.services.search_service import parse_audioknigi_results


ROOT = Path(__file__).resolve().parents[1]
QT_DIR = ROOT / "audioknigi" / "qt"
SERVICE = ROOT / "audioknigi" / "services" / "search_service.py"


FIXTURE = r'''
<div class="search-results">
  <a href="/audio-49051-sanderson-brendon-davshiy-klyatvu">
    <img alt="Слушать онлайн аудиокниги Сандерсон Брендон - Давший клятву">
  </a>
  <a href="https://audioknigi.com.ua/audio-48456-sanderson-brendon-slova-siyaniya">
    Сандерсон Брендон - Слова сияния
  </a>
</div>
<aside>
  <a href="/audio-90422-other">Филатов Валерий - Другая книга</a>
</aside>
'''


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_qt_entrypoint_coexists_with_stable_tk_entrypoint():
    assert (ROOT / "audioknigi_gui.py").exists()
    assert (ROOT / "audioknigi_qt.py").exists()
    assert (ROOT / "run_qt.bat").exists()
    assert (ROOT / "build_qt_exe.bat").exists()


def test_qt_and_new_service_layers_do_not_import_tkinter():
    paths = [*QT_DIR.rglob("*.py"), SERVICE]
    assert paths
    for path in paths:
        imports = _imports(path)
        assert not any(name == "tkinter" or name.startswith("tkinter.") for name in imports), path
        assert not any(name == "ttkbootstrap" or name.startswith("ttkbootstrap.") for name in imports), path
        text = path.read_text(encoding="utf-8")
        assert "ui_kit" not in text, path


def test_pyside6_dependency_is_declared():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements-qt.txt").read_text(encoding="utf-8")
    stable_requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "[project.optional-dependencies]" in pyproject
    assert "PySide6>=6.8,<7" in pyproject
    assert "PySide6>=6.8,<7" in requirements
    assert "PySide6" not in stable_requirements


def test_qt_accessibility_uses_native_metadata_and_announcement_event():
    text = (QT_DIR / "accessibility.py").read_text(encoding="utf-8")
    assert "setAccessibleName" in text
    assert "setAccessibleDescription" in text
    assert "setAccessibleIdentifier" in text
    assert "QAccessibleAnnouncementEvent" in text
    assert "QAccessible.updateAccessibility" in text
    assert "focus_force" not in text
    assert "grab_set" not in text


def test_qt_search_uses_qtableview_and_background_qthread():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert "QTableView" in text
    assert "QThread" in text
    assert "search_all_sources" in text
    assert "QMessageBox" in text


def test_gui_independent_search_parser_keeps_current_search_accuracy():
    parsed = parse_audioknigi_results(
        FIXTURE,
        "https://audioknigi.com.ua/search",
        query="Сандерсон",
    )
    assert [(item.title, item.author) for item in parsed] == [
        ("Слова сияния", "Сандерсон Брендон"),
        ("Давший клятву", "Сандерсон Брендон"),
    ]
    assert all("Филатов" not in item.title for item in parsed)
