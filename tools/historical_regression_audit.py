from __future__ import annotations

"""Run the archived pre-refactor regressions as a compatibility safety net.

The archived files intentionally retain their original path assumptions and
source-shape assertions.  They are copied to a temporary directory directly
under the repository root before execution so their historical ``ROOT`` logic
still resolves the current checkout.  Failures caused by the retired monolith
shape are explicitly allow-listed; any *new* failure turns this gate red.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive" / "tests" / "phase_regressions"
ALLOWLIST = ROOT / "tools" / "historical_regression_incompatibilities.json"
FAILED_LINE_RE = re.compile(r"^FAILED\s+(.+)$", re.MULTILINE)
SUMMARY_RE = re.compile(r"(?:(\d+) failed,\s*)?(\d+) passed")


def _failed_nodeid_from_line(raw: str) -> str:
    """Strip pytest failure detail without truncating spaces inside parameters."""
    text = str(raw or "").strip()
    bracket_depth = 0
    for index in range(len(text) - 2):
        char = text[index]
        if char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth:
            bracket_depth -= 1
        if bracket_depth == 0 and text.startswith(" - ", index):
            return text[:index].rstrip()
    return text


def _normalize_nodeid(raw: str, temp_name: str) -> str:
    raw = raw.replace("\\", "/")
    temp_name = temp_name.replace("\\", "/")
    prefix = temp_name.rstrip("/") + "/"
    return raw[len(prefix):] if raw.startswith(prefix) else raw


def main() -> int:
    if not ARCHIVE.is_dir():
        print("HISTORICAL REGRESSION: FAIL archive missing")
        return 2
    allowed = set(json.loads(ALLOWLIST.read_text(encoding="utf-8")))
    with tempfile.TemporaryDirectory(prefix=".historical-regression-", dir=ROOT) as tmp:
        tmp_path = Path(tmp)
        # TemporaryDirectory itself must be the test directory.  Copy files,
        # not the parent directory, so Path(__file__).parents[1] remains ROOT.
        for source in ARCHIVE.iterdir():
            destination = tmp_path / source.name
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", tmp_path.name, "--disable-warnings", "--tb=no"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=240,
        )
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        actual = {
            _normalize_nodeid(_failed_nodeid_from_line(match.group(1)), tmp_path.name)
            for match in FAILED_LINE_RE.finditer(combined)
        }
        unexpected = sorted(actual - allowed)
        resolved = sorted(allowed - actual)
        if re.search(r"^ERROR\s+", combined, re.MULTILINE) or "errors during collection" in combined.lower():
            print(combined)
            print("HISTORICAL REGRESSION: FAIL collection/runtime error")
            return 1
        if unexpected:
            print("HISTORICAL REGRESSION: FAIL unexpected regressions")
            for nodeid in unexpected:
                print("  +", nodeid)
            return 1
        summary = SUMMARY_RE.findall(combined)
        passed = int(summary[-1][1]) if summary else 0
        if passed < 250:
            print(combined)
            print(f"HISTORICAL REGRESSION: FAIL only {passed} archived tests passed")
            return 1
        print(
            "HISTORICAL REGRESSION: PASS "
            f"passed={passed} known_shape_incompatibilities={len(actual)} resolved={len(resolved)}"
        )
        if resolved:
            print("Resolved historical incompatibilities (remove from allowlist when convenient):")
            for nodeid in resolved:
                print("  -", nodeid)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
