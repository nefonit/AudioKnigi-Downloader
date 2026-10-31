"""Validate a frozen Windows *candidate* before release artifact upload.

This tool checks integrity and completeness, not licensing or NVDA/JAWS
acceptance. It never changes an acceptance status from 'required' to 'pass'.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


EXE_NAME = "AudioKnigiDownloader_Qt.exe"
REQUIRED_NOTICES = ("THIRD_PARTY_NOTICES.md", "RELEASE_LICENSING.md")
AUTOMATED_GATES = (
    "runtime", "accessibility", "playwright_edge", "import_boundary",
    "frozen_module_boundary",
)


def audit_release_candidate(dist: Path, *, tag: str | None = None) -> list[str]:
    dist = Path(dist)
    errors: list[str] = []
    manifest_path = dist / "qt_release_candidate.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"Cannot read release candidate manifest: {type(exc).__name__}"]
    if not isinstance(manifest, dict):
        return ["Release manifest must be a JSON object"]

    if manifest.get("schema") != 1:
        errors.append("Unsupported release manifest schema")
    if manifest.get("platform") != "windows":
        errors.append("Release manifest platform is not Windows")
    if manifest.get("exe") != EXE_NAME:
        errors.append("Unexpected executable name in manifest")
    version = manifest.get("app_version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:\.\d+)?", version):
        errors.append("Invalid application version in manifest")
    elif tag is not None and tag != f"v{version}":
        errors.append(f"Release tag {tag!r} does not match EXE version v{version}")

    expected_hash = manifest.get("exe_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch("[a-f0-9]{64}", expected_hash):
        errors.append("Invalid EXE SHA-256 in manifest")
    expected_size = manifest.get("size_bytes")
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size <= 0:
        errors.append("Invalid EXE size in manifest")

    exe = dist / EXE_NAME
    if not exe.is_file() or exe.is_symlink():
        errors.append("Windows EXE missing or not a regular file")
    else:
        count = 0
        digest = hashlib.sha256()
        try:
            with exe.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    count += len(chunk)
                    digest.update(chunk)
            if isinstance(expected_size, int) and count != expected_size:
                errors.append("EXE size disagrees with release manifest")
            if isinstance(expected_hash, str) and digest.hexdigest() != expected_hash:
                errors.append("EXE SHA-256 disagrees with release manifest")
        except OSError as exc:
            errors.append(f"Cannot read Windows EXE: {type(exc).__name__}")

    automated = manifest.get("automated")
    for gate in AUTOMATED_GATES:
        if not isinstance(automated, dict) or automated.get(gate) != "pass":
            errors.append(f"Frozen automated gate {gate} not passed")

    for gate in ("manual_screen_reader_acceptance", "licensing_review"):
        if manifest.get(gate) != "required":
            errors.append(f"Candidate manifest must explicitly leave {gate} required")

    for name in REQUIRED_NOTICES:
        notice = dist / name
        if not notice.is_file() or notice.is_symlink() or notice.stat().st_size == 0:
            errors.append(f"Missing or empty required release notice: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--tag", default=None)
    args = parser.parse_args()
    problems = audit_release_candidate(args.dist, tag=args.tag)
    if problems:
        for problem in problems:
            print("FAILED:", problem)
        return 1
    print("OK: EXE hash/size, version tag, automated gates and legal notices")
    print("Manual screen-reader acceptance and licensing review remain REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
