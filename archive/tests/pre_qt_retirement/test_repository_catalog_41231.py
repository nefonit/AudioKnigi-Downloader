from __future__ import annotations

from pathlib import Path

from make_source_release import _excluded


ROOT = Path(__file__).resolve().parents[1]


def test_audit_markdown_is_catalogued_outside_project_root():
    root_audits = [p.name for p in ROOT.glob("*.md") if "AUDIT" in p.name.upper()]
    assert root_audits == []
    assert (ROOT / "audits" / "INDEX.md").exists()
    assert (ROOT / "audits" / "4.12" / "AUDIT_CONSOLIDATED_FIXES_4_12_31.md").exists()


def test_documentation_catalog_and_release_setup_location():
    assert (ROOT / "docs" / "INDEX.md").exists()
    assert (ROOT / "docs" / "PROJECT_STRUCTURE.md").exists()
    assert (ROOT / "docs" / "build" / "RELEASE_SETUP.md").exists()


def test_source_release_keeps_docs_build_but_excludes_generated_root_build():
    assert _excluded(Path("build/temporary.bin")) is True
    assert _excluded(Path("dist/AudioKnigiDownloader.exe")) is True
    assert _excluded(Path("docs/build/RELEASE_SETUP.md")) is False
    assert _excluded(Path("docs/build/BUILD_PYTHON_3_14_7.md")) is False
    assert _excluded(Path("audioknigi/__pycache__/x.pyc")) is True
