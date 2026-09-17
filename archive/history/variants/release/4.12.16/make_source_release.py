from __future__ import annotations

import re
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".venv", "venv", "build", "dist"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def _version(root: Path) -> str:
    text = (root / "audioknigi" / "version.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise RuntimeError("Cannot determine application version")
    return match.group(1)


def _excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    if relative.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return False


def build_source_zip(root: Path | None = None) -> Path:
    root = (root or Path(__file__).resolve().parent).resolve()
    version = _version(root)
    package_name = f"AudioKnigi_Downloader_v{version.replace('.', '_')}_Source_Python_3_14_7"
    output = root.parent / f"{package_name}.zip"

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if _excluded(relative):
                continue
            archive.write(path, f"{package_name}/{relative.as_posix()}")

    with zipfile.ZipFile(output, "r") as archive:
        bad = [
            name for name in archive.namelist()
            if "/__pycache__/" in name
            or "/.pytest_cache/" in name
            or name.endswith((".pyc", ".pyo"))
            or "/.venv/" in name
            or "/build/" in name
            or "/dist/" in name
        ]
    if bad:
        output.unlink(missing_ok=True)
        raise RuntimeError(f"Release hygiene validation failed: {bad[:5]}")
    return output


if __name__ == "__main__":
    print(build_source_zip())
