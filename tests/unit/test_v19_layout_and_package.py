from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def test_search_row_index_column_is_fixed_and_font_scaled():
    advanced = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    easy = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert "search_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)" in advanced
    assert 'self.search_table.fontMetrics().horizontalAdvance("99999") + 28' in advanced
    assert "easy_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)" in easy
    assert 'self.easy_search_table.fontMetrics().horizontalAdvance("99999") + 28' in easy
    assert 'for column in (4, 5):' in advanced
    model = (ROOT / "audioknigi/qt/search_model.py").read_text(encoding="utf-8")
    assert "Qt.ItemDataRole.TextAlignmentRole and index.column() == 0" in model
    assert "Qt.AlignmentFlag.AlignCenter" in model


def test_release_documents_are_organized():
    assert not list(ROOT.glob("README_*.md"))
    assert (ROOT / "docs/releases/README_IZIB_TITLE_FIX_V18.md").is_file()
    assert (ROOT / "docs/architecture/REPOSITORY_GUIDE_V19.md").is_file()


def test_production_release_excludes_development_data(tmp_path):
    from tools.package_source_release import build_source_zip
    output = tmp_path / "production.zip"
    build_source_zip(ROOT, output, root_name="AudioKnigi", profile="production")
    with zipfile.ZipFile(output) as z:
        names = set(z.namelist())
        assert "AudioKnigi/audioknigi_qt.py" in names
        assert "AudioKnigi/build_qt_ci.ps1" in names
        assert "AudioKnigi/tools/qt_import_audit.py" in names
        assert "AudioKnigi/docs/development/RELEASE_LICENSING.md" in names
        assert any(x.startswith("AudioKnigi/assets/sounds/") for x in names)
        assert not any("/archive/" in x or "/audits/" in x or "/tests/" in x or "/.github/" in x for x in names)
        assert not any("/docs/releases/" in x for x in names)
