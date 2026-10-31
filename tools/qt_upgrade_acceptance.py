"""Read-only Windows upgrade evidence for a throwaway AudioKnigi profile.

Capture the *old* EXE/profile, then compare after testing the *new* EXE.
Reports contain only content hashes, JSON types and row counts, not user data.
This tool never launches an executable or writes into the application profile.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SCHEMA = 1
STATE_FILES: dict[str, type | None] = {
    "settings.json": dict,
    "qt_queue.json": list,
    "history.json": list,
    "player_positions.json": dict,
    "session_profile.json": None,
    "session_state.json": None,
    "session_cookies.json": None,
}
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_state_file(path: Path, expected_type: type | None) -> dict:
    """Read metadata only; do not put any JSON values in the report."""
    if path.is_symlink():
        return {"present": True, "valid": False, "reason": "symlink"}
    if not path.exists():
        return {"present": False}
    try:
        raw = path.read_bytes()
        checksum = hashlib.sha256(raw).hexdigest()
        payload = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, ValueError, TypeError):
        return {"present": True, "valid": False, "reason": "unreadable"}
    if expected_type is not None and not isinstance(payload, expected_type):
        return {"present": True, "valid": False, "reason": "shape"}
    if not isinstance(payload, (dict, list)):
        return {"present": True, "valid": False, "reason": "shape"}
    return {
        "present": True,
        "valid": True,
        "kind": "list" if isinstance(payload, list) else "object",
        "count": len(payload),
        "sha256": checksum,
    }


def capture(app_dir: Path, exe: Path) -> dict:
    """Snapshot only an explicitly selected test profile and EXE."""
    app_dir, exe = Path(app_dir), Path(exe)
    if not app_dir.is_dir() or app_dir.is_symlink():
        raise ValueError("The isolated application profile must be an existing real directory")
    if not exe.is_file() or exe.is_symlink():
        raise ValueError("The executable must be an existing regular file")
    return {
        "schema": SCHEMA,
        "exe_sha256": sha256_file(exe),
        "files": {
            name: inspect_state_file(app_dir / name, expected)
            for name, expected in STATE_FILES.items()
        },
    }


def validate_baseline(baseline: dict) -> None:
    if not isinstance(baseline, dict) or baseline.get("schema") != SCHEMA:
        raise ValueError("Unsupported upgrade baseline schema")
    if not isinstance(baseline.get("exe_sha256"), str) or not HEX_SHA256.fullmatch(baseline["exe_sha256"]):
        raise ValueError("Invalid old executable hash")
    files = baseline.get("files")
    if not isinstance(files, dict) or set(files) != set(STATE_FILES):
        raise ValueError("Missing fields in upgrade baseline")
    for name, value in files.items():
        if not isinstance(value, dict) or not isinstance(value.get("present"), bool):
            raise ValueError(f"Invalid baseline entry for {name}")
        if value["present"]:
            if value.get("valid") is not True:
                raise ValueError(f"Previous profile already contains damaged {name}")
            if value.get("kind") not in ("list", "object"):
                raise ValueError(f"Missing baseline JSON shape for {name}")
            if (
                isinstance(value.get("count"), bool)
                or not isinstance(value.get("count"), int)
                or value["count"] < 0
                or not isinstance(value.get("sha256"), str)
                or not HEX_SHA256.fullmatch(value["sha256"])
            ):
                raise ValueError(f"Invalid baseline checksum/count for {name}")


def compare(baseline: dict, current: dict) -> dict:
    """FAIL on data loss/corruption, REVIEW on valid rewrites, PASS if equal."""
    validate_baseline(baseline)
    if (
        not isinstance(current, dict)
        or current.get("schema") != SCHEMA
        or not isinstance(current.get("exe_sha256"), str)
        or not HEX_SHA256.fullmatch(current["exe_sha256"])
        or not isinstance(current.get("files"), dict)
        or set(current["files"]) != set(STATE_FILES)
    ):
        raise ValueError("Invalid new upgrade snapshot")
    outcomes = {}
    for name in STATE_FILES:
        before = baseline["files"][name]
        after = current["files"][name]
        if not isinstance(after, dict) or not isinstance(after.get("present"), bool):
            result, status = "invalid-snapshot", "fail"
        elif after["present"] and after.get("valid") is not True:
            result, status = "corrupt", "fail"
        elif not before["present"]:
            result = "new" if after["present"] else "unchanged"
            status = "review" if after["present"] else "pass"
        elif not after["present"]:
            result, status = "missing", "fail"
        elif before["kind"] != after["kind"]:
            result, status = "changed-shape", "fail"
        elif (
            before["kind"] == "list"
            and after["count"] < before["count"]
        ):
            result, status = "fewer-records", "fail"
        elif before["sha256"] != after["sha256"]:
            result, status = "modified", "review"
        else:
            result, status = "unchanged", "pass"
        outcomes[name] = {
            "status": status, "result": result,
            "before_count": before.get("count"), "after_count": after.get("count"),
        }

    if baseline["exe_sha256"] == current["exe_sha256"]:
        overall = "fail"
        exe_issue = "same-executable"
    else:
        overall = "fail" if any(v["status"] == "fail" for v in outcomes.values()) else (
            "review" if any(v["status"] == "review" for v in outcomes.values()) else "pass"
        )
        exe_issue = None

    return {
        "schema": SCHEMA,
        "status": overall,
        "old_exe_sha256": baseline["exe_sha256"],
        "new_exe_sha256": current["exe_sha256"],
        "exe_issue": exe_issue,
        "files": outcomes,
        "manual_nvda_jaws_acceptance": "required",
        "manual_upgrade_signoff": "required",
    }


def write_evidence(output: Path, data: dict, app_dir: Path) -> None:
    """Evidence goes outside the app's directory; no profile files modified."""
    output = Path(output)
    if output.is_symlink():
        raise ValueError("Refusing to overwrite a symlinked evidence file")
    output = output.resolve()
    app_dir = Path(app_dir).resolve()
    if output == app_dir or app_dir in output.parents:
        raise ValueError("Write upgrade evidence outside the application profile")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    try:
        temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("capture", "compare"):
        command = commands.add_parser(name)
        command.add_argument("--app-dir", type=Path, required=True, help="Isolated APPDATA/AudioKnigiDownloader")
        command.add_argument("--exe", type=Path, required=True, help="Exact old/new EXE being tested")
        command.add_argument("--output", type=Path, required=True, help="Evidence JSON outside app-dir")
        if name == "compare":
            command.add_argument("--baseline", type=Path, required=True, help="Earlier capture JSON")
    args = parser.parse_args(argv)
    try:
        current = capture(args.app_dir, args.exe)
        if args.command == "capture":
            validate_baseline(current)
            write_evidence(args.output, current, args.app_dir)
            print("CAPTURED: baseline recorded; no profile data was changed")
            return 0
        baseline = json.loads(args.baseline.read_text(encoding="utf-8-sig"))
        report = compare(baseline, current)
        write_evidence(args.output, report, args.app_dir)
    except (OSError, ValueError, TypeError) as exc:
        print(f"UPGRADE CHECK FAILED: {exc}")
        return 1

    print(f"UPGRADE CHECK: {report['status'].upper()}")
    for name, result in report["files"].items():
        print(f"  {name}: {result['result']}")
    print("NVDA/JAWS and manual upgrade sign-off remain required")
    return {"pass": 0, "review": 2, "fail": 1}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
