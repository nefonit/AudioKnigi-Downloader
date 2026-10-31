"""V37: read-only, privacy-conscious Windows upgrade acceptance evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.qt_upgrade_acceptance import (
    STATE_FILES, capture, compare, inspect_state_file, main, validate_baseline,
    write_evidence,
)


ROOT = Path(__file__).resolve().parents[2]


def setup_pair(tmp_path):
    app = tmp_path / "isolated" / "AudioKnigiDownloader"
    app.mkdir(parents=True)
    old_exe = tmp_path / "old.exe"
    new_exe = tmp_path / "new.exe"
    old_exe.write_bytes(b"old frozen executable")
    new_exe.write_bytes(b"new frozen executable")
    (app / "settings.json").write_text('{"language":"ru","theme":"dark"}', encoding="utf-8")
    (app / "qt_queue.json").write_text(
        '[{"id":"private-1","status_code":"interrupted"},{"id":"private-2","status_code":"completed"}]',
        encoding="utf-8",
    )
    (app / "history.json").write_text('[{"title":"Private Book"}]', encoding="utf-8")
    (app / "player_positions.json").write_text('{"private.mp3":12345}', encoding="utf-8")
    return app, old_exe, new_exe


def test_unchanged_profile_is_compatible_but_not_manual_release_signoff(tmp_path):
    app, old_exe, new_exe = setup_pair(tmp_path)
    before = capture(app, old_exe)
    after = capture(app, new_exe)
    report = compare(before, after)
    assert report["status"] == "pass"
    assert report["manual_nvda_jaws_acceptance"] == "required"
    assert report["manual_upgrade_signoff"] == "required"
    assert all(v["result"] == "unchanged" for v in report["files"].values())
    assert before["exe_sha256"] != after["exe_sha256"]


def test_changed_valid_settings_and_queue_are_review_not_automatic_pass(tmp_path):
    app, old, new = setup_pair(tmp_path)
    before = capture(app, old)
    (app / "settings.json").write_text(
        '{"language":"ru","theme":"dark","settings_version":3}', encoding="utf-8"
    )
    (app / "qt_queue.json").write_text(
        '[{"id":"private-1","status_code":"pending"},{"id":"private-2","status_code":"completed"}]',
        encoding="utf-8",
    )
    report = compare(before, capture(app, new))
    assert report["status"] == "review"
    assert report["files"]["settings.json"]["result"] == "modified"
    assert report["files"]["qt_queue.json"]["result"] == "modified"
    assert report["files"]["qt_queue.json"]["before_count"] == 2
    assert report["files"]["qt_queue.json"]["after_count"] == 2


@pytest.mark.parametrize("name", ["settings.json", "qt_queue.json", "history.json", "player_positions.json"])
def test_missing_previously_present_file_is_a_failure(tmp_path, name):
    app, old, new = setup_pair(tmp_path)
    before = capture(app, old)
    (app / name).unlink()
    result = compare(before, capture(app, new))
    assert result["status"] == "fail"
    assert result["files"][name]["result"] == "missing"


def test_corrupted_queue_fails_with_report_instead_of_leaking_json(tmp_path):
    app, old, new = setup_pair(tmp_path)
    baseline = capture(app, old)
    (app / "qt_queue.json").write_bytes(b'{"SECRET_PASSWORD": \xff')
    result = compare(baseline, capture(app, new))
    assert result["status"] == "fail"
    assert result["files"]["qt_queue.json"]["result"] == "corrupt"
    path = tmp_path / "upgrade_after.json"
    write_evidence(path, result, app)
    evidence = path.read_text(encoding="utf-8")
    assert "SECRET_PASSWORD" not in evidence
    assert "Private Book" not in evidence
    assert "private.mp3" not in evidence


def test_lost_queue_or_history_records_is_failure(tmp_path):
    app, old, new = setup_pair(tmp_path)
    before = capture(app, old)
    (app / "qt_queue.json").write_text("[]", encoding="utf-8")
    (app / "history.json").write_text("[]", encoding="utf-8")
    r = compare(before, capture(app, new))
    assert r["status"] == "fail"
    assert r["files"]["qt_queue.json"]["result"] == "fewer-records"
    assert r["files"]["history.json"]["result"] == "fewer-records"


def test_no_old_data_is_not_resurrected_or_modified_by_tool(tmp_path):
    app, old, new = setup_pair(tmp_path)
    (app / "history.json").unlink()
    original_settings = (app / "settings.json").read_bytes()
    before = capture(app, old)
    assert not before["files"]["history.json"]["present"]
    (app / "history.json").write_text("[]", encoding="utf-8")
    result = compare(before, capture(app, new))
    assert result["status"] == "review"
    assert result["files"]["history.json"]["result"] == "new"
    assert (app / "settings.json").read_bytes() == original_settings


def test_identical_exe_is_not_misrepresented_as_upgrade(tmp_path):
    app, old, _ = setup_pair(tmp_path)
    before = capture(app, old)
    r = compare(before, capture(app, old))
    assert r["status"] == "fail"
    assert r["exe_issue"] == "same-executable"


def test_baseline_must_be_well_formed_and_old_profile_valid(tmp_path):
    app, old, _ = setup_pair(tmp_path)
    baseline = capture(app, old)
    baseline["files"]["history.json"]["sha256"] = "broken"
    with pytest.raises(ValueError, match="checksum/count"):
        validate_baseline(baseline)
    (app / "history.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError, match="damaged"):
        validate_baseline(capture(app, old))


def test_reports_cannot_be_written_inside_real_test_profile(tmp_path):
    app, old, _ = setup_pair(tmp_path)
    before = capture(app, old)
    with pytest.raises(ValueError, match="outside"):
        write_evidence(app / "state.json", before, app)
    assert not (app / "state.json").exists()
    outside = tmp_path / "evidence" / "before.json"
    write_evidence(outside, before, app)
    data = json.loads(outside.read_text(encoding="utf-8"))
    assert data["files"]["qt_queue.json"]["count"] == 2


def test_cli_capture_then_compare_returns_review_status_and_evidence(tmp_path):
    app, old, new = setup_pair(tmp_path)
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    assert main([
        "capture", "--app-dir", str(app), "--exe", str(old), "--output", str(before),
    ]) == 0
    (app / "settings.json").write_text(
        '{"language":"ru","theme":"dark","settings_version":3}', encoding="utf-8"
    )
    assert main([
        "compare", "--app-dir", str(app), "--exe", str(new),
        "--baseline", str(before), "--output", str(after),
    ]) == 2
    assert json.loads(after.read_text(encoding="utf-8"))["status"] == "review"


def test_symlinked_profile_file_is_rejected(tmp_path):
    app, old, _ = setup_pair(tmp_path)
    external = tmp_path / "secret-history.json"
    external.write_text('[{"title":"private"}]', encoding="utf-8")
    (app / "history.json").unlink()
    try:
        (app / "history.json").symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("Windows symlink creation not permitted")
    assert inspect_state_file(app / "history.json", list)["reason"] == "symlink"
    with pytest.raises(ValueError):
        validate_baseline(capture(app, old))


def test_production_source_zip_contains_upgrade_tool_and_guide():
    src = (ROOT / "tools/package_source_release.py").read_text(encoding="utf-8")
    assert '"qt_upgrade_acceptance.py"' in src
    assert '"docs/qa/UPGRADE_ACCEPTANCE_V37.md"' in src
    assert '"run_qt_upgrade_acceptance.bat"' in src
    assert (ROOT / "run_qt_upgrade_acceptance.bat").exists()
    assert set(STATE_FILES) >= {"settings.json", "history.json", "qt_queue.json", "player_positions.json"}


def test_production_zip_really_contains_upgrade_docs_and_runner(tmp_path):
    from tools.package_source_release import build_source_zip
    import zipfile

    root = tmp_path / "source"
    for name in (
        "run_qt_upgrade_acceptance.bat",
        "tools/qt_upgrade_acceptance.py",
        "docs/qa/UPGRADE_ACCEPTANCE_V37.md",
    ):
        entry = root / name
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("safe test content", encoding="utf-8")
    output = tmp_path / "production.zip"
    build_source_zip(root, output, profile="production", root_name="package")
    with zipfile.ZipFile(output) as archive:
        assert {
            "package/run_qt_upgrade_acceptance.bat",
            "package/tools/qt_upgrade_acceptance.py",
            "package/docs/qa/UPGRADE_ACCEPTANCE_V37.md",
        } <= set(archive.namelist())


def test_evidence_file_symlink_outside_profile_cannot_be_overwritten(tmp_path):
    app, old, _ = setup_pair(tmp_path)
    external = tmp_path / "personal.json"
    external.write_text("NEVER OVERWRITE", encoding="utf-8")
    output = tmp_path / "evidence.json"
    try:
        output.symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("Windows symlink creation not permitted")
    with pytest.raises(ValueError, match="symlinked"):
        write_evidence(output, capture(app, old), app)
    assert external.read_text(encoding="utf-8") == "NEVER OVERWRITE"
