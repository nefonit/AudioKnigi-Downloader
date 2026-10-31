"""V36: production source hygiene and Windows release-candidate integrity checks."""

from __future__ import annotations

import hashlib
import json
import tomllib
import zipfile
from pathlib import Path

import pytest

from tools.package_source_release import build_source_zip
from tools.release_candidate_audit import AUTOMATED_GATES, audit_release_candidate


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("profile", ["developer", "production"])
def test_source_package_excludes_new_private_runtime_artifacts(tmp_path, profile):
    root = tmp_path / "checkout"
    pkg = root / "audioknigi" / "download"
    pkg.mkdir(parents=True)
    (pkg / "engine.py").write_text("print('clean source')\n", encoding="utf-8")
    (root / "README.md").write_text("Build instructions\n", encoding="utf-8")
    (root / "THIRD_PARTY_NOTICES.md").write_text("Notices\n", encoding="utf-8")

    # Every entry is a realistic local file that must not leak into a
    # developer or production release ZIP, including nested state files.
    user_data = {
        "settings.json": '{"api_key": "secret"}',
        "qt_queue.json": '{"private_title": "Book"}',
        "qt_queue.lastgood.json": '{"private_title": "Book"}',
        "history.lastgood.json": '{"private_title": "Book"}',
        "qt_queue.corrupt-012345abcdef.json": "damaged private queue",
        "history.corrupt-012345abcdef.json": "private history",
        "session_cookies.json": "secret cookie",
        "session_state.json": '{"running": true}',
        "player_positions.json": '{"file": "private title"}',
        "last_crash_report.txt": "private paths",
        "book.mp3.part.seg000": "partial audio",
        "book.mp3.part.segments.json": "private source URL",
        "book.mp3.part.segments.sha256.json": "private checksum",
        "book.mp3.part.assembling": "unfinished audio",
        ".env": "TOKEN=secret",
        ".env.local": "TOKEN=secret",
        "cache.tmp": "scratch",
    }
    for name, value in user_data.items():
        (pkg / name).write_text(value, encoding="utf-8")

    venv = root / ".venv-qt" / "Scripts"
    venv.mkdir(parents=True)
    (venv / "private-package.py").write_text("user-specific state", encoding="utf-8")
    source = root / "tools"
    source.mkdir()
    (source / "qt_import_audit.py").write_text("pass", encoding="utf-8")

    archive = tmp_path / f"{profile}.zip"
    build_source_zip(root, archive, profile=profile, root_name="release")
    with zipfile.ZipFile(archive) as result:
        names = set(result.namelist())
        assert "release/audioknigi/download/engine.py" in names
        assert "release/README.md" in names
        assert "release/THIRD_PARTY_NOTICES.md" in names
        assert not any(name.endswith("/" + private) for private in user_data for name in names)
        assert not any(".venv-qt/" in name for name in names)
        assert not any(b"secret" in result.read(name) for name in names)
        if profile == "production":
            assert "release/tools/qt_import_audit.py" in names


def test_source_packager_never_follows_symlink_outside_checkout(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "README.md").write_text("safe", encoding="utf-8")
    external = tmp_path / "private.txt"
    external.write_text("PRIVATE USER DATA", encoding="utf-8")
    link = root / "linked-private.txt"
    try:
        link.symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation disabled by Windows test environment")
    archive = tmp_path / "developer.zip"
    build_source_zip(root, archive, root_name="project")
    with zipfile.ZipFile(archive) as result:
        assert result.namelist() == ["project/README.md"]


def _candidate(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    executable = dist / "AudioKnigiDownloader_Qt.exe"
    executable.write_bytes(b"safe fake frozen executable")
    for name in ("THIRD_PARTY_NOTICES.md", "RELEASE_LICENSING.md"):
        (dist / name).write_text("Required notices and review checklist", encoding="utf-8")
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    manifest = {
        "schema": 1, "platform": "windows", "app_version": "4.12.42",
        "exe": executable.name, "size_bytes": executable.stat().st_size,
        "exe_sha256": digest,
        "automated": {name: "pass" for name in AUTOMATED_GATES},
        "manual_screen_reader_acceptance": "required",
        "licensing_review": "required",
    }
    (dist / "qt_release_candidate.json").write_text(json.dumps(manifest), encoding="utf-8")
    return dist, executable, manifest


def test_release_candidate_passes_only_with_matching_exe_and_legal_notices(tmp_path):
    dist, _, _ = _candidate(tmp_path)
    assert audit_release_candidate(dist, tag="v4.12.42") == []


@pytest.mark.parametrize("changed", ["exe", "size", "hash", "notices", "tag", "automated", "manual"])
def test_release_candidate_rejects_incomplete_or_mismatched_artifact(tmp_path, changed):
    dist, exe, manifest = _candidate(tmp_path)
    if changed == "exe":
        exe.write_bytes(b"tampered content")
    elif changed == "size":
        manifest["size_bytes"] += 1
    elif changed == "hash":
        manifest["exe_sha256"] = "0" * 64
    elif changed == "notices":
        (dist / "THIRD_PARTY_NOTICES.md").unlink()
    elif changed == "automated":
        manifest["automated"]["accessibility"] = "failed"
    elif changed == "manual":
        manifest["manual_screen_reader_acceptance"] = "pass"
    (dist / "qt_release_candidate.json").write_text(json.dumps(manifest), encoding="utf-8")
    problems = audit_release_candidate(dist, tag="v4.12.43" if changed == "tag" else "v4.12.42")
    assert problems, f"candidate auditor incorrectly passed {changed}"


def test_missing_or_nonobject_candidate_manifest_is_rejected(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    assert audit_release_candidate(dist)
    (dist / "qt_release_candidate.json").write_text("[]", encoding="utf-8")
    assert audit_release_candidate(dist)
    (dist / "qt_release_candidate.json").write_text("{invalid", encoding="utf-8")
    assert audit_release_candidate(dist)


def test_package_metadata_declares_every_normal_runtime_dependency():
    import re

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    declared = {
        re.split(r"[<>=!~\[; ]", package, maxsplit=1)[0].casefold().replace("_", "-")
        for package in project["dependencies"]
    }
    requirements = {
        re.split(r"[<>=!~\[; ]", line.strip(), maxsplit=1)[0].casefold().replace("_", "-")
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert requirements <= declared
    assert "beautifulsoup4" in declared


def test_tagged_release_workflow_never_uploads_exe_without_notices():
    yml = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "tools/release_candidate_audit.py" in yml
    assert "dist/THIRD_PARTY_NOTICES.md" in yml
    assert "dist/RELEASE_LICENSING.md" in yml
    assert "if-no-files-found: error" in yml
    assert "windows-x64-candidate" in yml
