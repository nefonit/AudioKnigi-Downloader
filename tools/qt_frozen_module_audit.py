from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Iterable

MODULE_TYPECODES = {
    "PYMODULE",
    "PYMODULE-1",
    "PYMODULE-2",
    "EXTENSION",
    "PYSOURCE",
}

FORBIDDEN_ROOTS = (
    "tkinter",
    "_tkinter",
    "ttkbootstrap",
    "tkinterdnd2",
    "pygame",
    "pystray",
    "plyer",
    "prism",
    "tk_uia",
    "audioknigi.app",
    "audioknigi.actions",
    "audioknigi.accessibility",
    "audioknigi.ui_kit",
    "audioknigi.player",
    "audioknigi.queue_manager",
    "audioknigi.tray",
)


def _iter_toc_entries(value: object) -> Iterable[tuple[str, str, str]]:
    """Yield real PyInstaller TOC entries and ignore metadata such as excludes.

    Analysis-00.toc is a serialized tuple of Analysis._GUTS.  It includes both
    inputs (including the `excludes` list) and calculated TOC lists.  Looking
    for a forbidden module name in the raw file therefore produces false
    positives.  Actual collected entries are 3-tuples whose third item is a
    PyInstaller module typecode.
    """

    if isinstance(value, (tuple, list)):
        if (
            len(value) == 3
            and isinstance(value[0], str)
            and isinstance(value[1], (str, type(None)))
            and isinstance(value[2], str)
            and value[2] in MODULE_TYPECODES
        ):
            yield (value[0], "" if value[1] is None else value[1], value[2])
            return
        for item in value:
            yield from _iter_toc_entries(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_toc_entries(item)


def _normalise_entry_name(name: str, typecode: str) -> str:
    value = name.replace("\\", "/")
    if typecode == "EXTENSION":
        parts = value.split("/")
        filename = parts[-1]
        lower = filename.lower()
        for suffix in (".pyd", ".dll", ".so", ".dylib"):
            if lower.endswith(suffix):
                filename = filename[: -len(suffix)]
                break
        # Extension filenames may carry an ABI tag, e.g. _camera.cp314-win_amd64.
        filename = filename.split(".", 1)[0]
        parts[-1] = filename
        value = "/".join(parts)
    return value


def _matches_root(name: str, root: str) -> bool:
    if name == root or name.startswith(root + "."):
        return True
    path_name = name.replace("\\", "/")
    path_root = root.replace(".", "/")
    return path_name == path_root or path_name.startswith(path_root + "/")


def find_forbidden_modules(toc_data: object) -> list[tuple[str, str, str]]:
    leaks: list[tuple[str, str, str]] = []
    for name, source, typecode in _iter_toc_entries(toc_data):
        normalised = _normalise_entry_name(name, typecode)
        if any(_matches_root(normalised, root) for root in FORBIDDEN_ROOTS):
            leaks.append((name, source, typecode))
    return leaks


def load_analysis_toc(path: Path) -> object:
    try:
        return ast.literal_eval(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        raise ValueError(f"Could not parse PyInstaller Analysis TOC {path}: {exc}") from exc


def audit_analysis_toc(path: Path) -> list[tuple[str, str, str]]:
    return find_forbidden_modules(load_analysis_toc(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail only when legacy frontend modules are actually collected by PyInstaller."
    )
    parser.add_argument("toc", type=Path, help="Path to Analysis-00.toc")
    args = parser.parse_args(argv)

    try:
        leaks = audit_analysis_toc(args.toc)
    except ValueError as exc:
        print(f"QT FROZEN MODULE AUDIT: ERROR: {exc}")
        return 2

    if leaks:
        print("QT FROZEN MODULE AUDIT: FAILED")
        for name, source, typecode in leaks:
            print(f"  {name} [{typecode}] <- {source}")
        return 1

    print("QT FROZEN MODULE AUDIT: OK (no collected legacy frontend modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
