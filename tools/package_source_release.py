from __future__ import annotations

"""Create a clean source ZIP from the repository tree."""

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
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".part"}


def _excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_DIR_NAMES or part.startswith(".historical-regression-") for part in relative.parts[:-1]):
        return True
    name = relative.name
    if len(relative.parts) == 1 and name.startswith("AUDIT_NOTES_") and name.endswith(".md"):
        return True
    if name in EXCLUDED_FILE_NAMES or name.startswith(".historical-regression-"):
        return True
    return relative.suffix.lower() in EXCLUDED_SUFFIXES


def build_source_zip(root: Path, output: Path, *, root_name: str | None = None) -> Path:
    root = Path(root).resolve()
    output = Path(output).resolve()
    root_name = root_name or root.name
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if _excluded(relative) or path.resolve() == output:
                continue
            archive.write(path, Path(root_name) / relative)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root-name", default=None)
    args = parser.parse_args()
    result = build_source_zip(args.root, args.output, root_name=args.root_name)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
