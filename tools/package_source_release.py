from __future__ import annotations

"""Create either a complete developer ZIP or a lean buildable production-source ZIP."""

import argparse
import zipfile
from pathlib import Path

EXCLUDED_DIR_NAMES = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "build", "dist", ".venv", "venv", "env",
}
EXCLUDED_FILE_NAMES = {
    "settings.json", "history.json", "qt_queue.json", "cookies.json", "session_profile.json",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".part", ".pyd", ".so", ".dll", ".orig"}


def _excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_DIR_NAMES or part.startswith(".historical-regression-") for part in relative.parts[:-1]):
        return True
    name = relative.name
    if len(relative.parts) == 1 and name.startswith("AUDIT_NOTES_") and name.endswith(".md"):
        return True
    # Keep intentional test fixtures; still exclude private runtime state from
    # arbitrary nested folders (not only the repository root).
    is_fixture = relative.parts[:2] == ("tests", "fixtures")
    if (name in EXCLUDED_FILE_NAMES and not is_fixture) or name.startswith(".historical-regression-"):
        return True
    return relative.suffix.lower() in EXCLUDED_SUFFIXES


# Keep the build and acceptance tooling required by existing Windows launchers.
# Unit tests and development-only static audits do not belong in a production
# *source* ZIP, but the user can still build an EXE from that source.
PRODUCTION_TOOLS = frozenset({
    "qt_import_audit.py", "pyinstaller_bootstrap.py", "windows_version_info.py",
    "qt_frozen_module_audit.py", "qt_windows_acceptance.py",
})
PRODUCTION_ROOT_FILES = frozenset({
    "README.md", "THIRD_PARTY_NOTICES.md", "audioknigi_qt.py",
    "run.bat", "run_qt.bat", "run_qt_acceptance.bat",
    "check_qt_acceptance.bat", "build_qt_exe.bat", "build_qt_ci.ps1",
    "pyproject.toml", "requirements.txt", "requirements-qt.txt",
    "requirements-qt-build.txt", "requirements-release.txt",
})


def _excluded_from_production(relative: Path) -> bool:
    head = relative.parts[0]
    if head == "tools":
        return len(relative.parts) != 2 or relative.name not in PRODUCTION_TOOLS
    if head == "docs":
        return relative.as_posix() not in {
            "docs/development/RELEASE_LICENSING.md",
            "docs/user/DIAGNOSTICS.md",
            "docs/architecture/REPOSITORY_GUIDE_V19.md",
            "docs/architecture/PROJECT_STRUCTURE.md",
        }
    if head in {"tests", "archive", "audits", ".github"}:
        return True
    if head in {"audioknigi", "assets"}:
        return False
    return len(relative.parts) != 1 or relative.name not in PRODUCTION_ROOT_FILES


def build_source_zip(
    root: Path, output: Path, *, root_name: str | None = None,
    profile: str = "developer",
) -> Path:
    if profile not in {"developer", "production"}:
        raise ValueError(f"Unknown source package profile: {profile}")
    root = Path(root).resolve()
    output = Path(output).resolve()
    root_name = root_name or root.name
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if (_excluded(relative) or path.resolve() == output
                    or (profile == "production" and _excluded_from_production(relative))):
                continue
            archive.write(path, Path(root_name) / relative)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root-name", default=None)
    parser.add_argument("--profile", choices=("developer", "production"), default="developer")
    args = parser.parse_args()
    result = build_source_zip(args.root, args.output, root_name=args.root_name, profile=args.profile)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
