from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[2]


def lines(rel):
    return len((ROOT / rel).read_text(encoding="utf-8").splitlines())


def test_large_monoliths_are_split():
    assert lines("audioknigi/qt/main_window.py") < 1200
    assert lines("audioknigi/downloader.py") < 200
    assert lines("audioknigi/i18n.py") < 250


def test_new_subsystems_have_clear_packages():
    for rel in ("audioknigi/config", "audioknigi/download", "audioknigi/providers", "audioknigi/diagnostics", "audioknigi/locales", "audioknigi/qt/mixins"):
        assert (ROOT / rel).is_dir()


def test_active_tests_are_organized_by_behavior_not_phase_number():
    active = list((ROOT / "tests").rglob("test_*.py"))
    assert active
    assert not any("phase" in p.name or "audit" in p.name for p in active)
    assert (ROOT / "archive/tests/phase_regressions").is_dir()
    assert (ROOT / "archive/tests/pre_qt_retirement").is_dir()


def test_historical_sources_are_outside_runtime_root():
    assert (ROOT / "archive/history/variants").is_dir()
    assert not (ROOT / "history").exists()


def test_release_dependency_lock_exists_and_is_exact():
    lines_ = [line.strip() for line in (ROOT / "requirements-release.txt").read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    assert lines_
    assert all("==" in line for line in lines_)


def test_pytest_points_to_active_tests_only():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_locale_catalogs_are_packaged_and_frozen_build_includes_them():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "locales/*.json" in data["tool"]["setuptools"]["package-data"]["audioknigi"]
    build = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8-sig")
    assert "audioknigi\\locales;audioknigi\\locales" in build


def test_active_tools_do_not_contain_one_off_phase13_source_builder():
    assert not (ROOT / "tools/build_qt_only_source.py").exists()
    assert (ROOT / "archive/tools/phase13/build_qt_only_source.py").is_file()


def test_windows_build_uses_exact_release_dependency_baseline():
    build_requirements = (ROOT / "requirements-qt-build.txt").read_text(encoding="utf-8")
    assert "-r requirements-release.txt" in build_requirements


def test_repository_root_has_no_audit_notes_and_rounds_are_catalogued():
    assert not list(ROOT.glob("AUDIT_NOTES_*.md"))
    assert (ROOT / ".gitignore").is_file()
    assert (ROOT / "audits/4.12/rounds/INDEX.md").is_file()
    assert list((ROOT / "audits/4.12/rounds").glob("AUDIT_NOTES_*.md"))


def test_source_release_packager_exists_and_knows_generated_exclusions():
    source = (ROOT / "tools/package_source_release.py").read_text(encoding="utf-8")
    for marker in ("__pycache__", ".pytest_cache", ".historical-regression-", "build", "dist"):
        assert marker in source
