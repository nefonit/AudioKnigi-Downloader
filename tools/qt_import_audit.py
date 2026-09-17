from __future__ import annotations

"""Static import-graph preflight for the Qt entry point.

Exit 0 means the project import graph reachable from ``audioknigi_qt.py`` does
not cross into retired legacy frontend modules and the dedicated Qt requirements
manifest contains the declared runtime distributions.
"""

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audioknigi.qt_runtime_audit import (  # noqa: E402
    FORBIDDEN_EXTERNAL_PREFIXES,
    FORBIDDEN_PROJECT_PREFIXES,
    QT_RUNTIME_DISTRIBUTIONS,
)


@dataclass(frozen=True, slots=True)
class ImportPath:
    modules: tuple[str, ...]

    def format(self) -> str:
        return " -> ".join(self.modules)


def _module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def discover_project_modules() -> dict[str, Path]:
    modules: dict[str, Path] = {"audioknigi_qt": ROOT / "audioknigi_qt.py"}
    for path in (ROOT / "audioknigi").rglob("*.py"):
        modules[_module_name(path)] = path
    return modules


def _package_parts(module: str, path: Path) -> list[str]:
    if path.name == "__init__.py":
        return module.split(".") if module else []
    return module.split(".")[:-1]


def _resolve_from(module: str, path: Path, node: ast.ImportFrom) -> str:
    target = node.module or ""
    if not node.level:
        return target
    package = _package_parts(module, path)
    # level=1 means current package; level=2 means one package upward.
    keep = max(0, len(package) - (node.level - 1))
    prefix = package[:keep]
    if target:
        prefix.extend(target.split("."))
    return ".".join(prefix)


def parse_imports(module: str, path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_from(module, path, node)
            if base:
                found.append(base)
            # ``from . import foo`` needs the imported name to find project modules.
            if node.module is None and base:
                found.extend(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
    return tuple(found)


def _matches(name: str, prefixes: Iterable[str]) -> bool:
    return any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)


def build_graph(modules: dict[str, Path]) -> dict[str, tuple[str, ...]]:
    return {name: parse_imports(name, path) for name, path in modules.items()}


def walk_reachable(
    graph: dict[str, tuple[str, ...]],
    modules: dict[str, Path],
    start: str = "audioknigi_qt",
) -> tuple[set[str], list[ImportPath], set[str]]:
    seen: set[str] = set()
    forbidden_paths: list[ImportPath] = []
    direct_external: set[str] = set()
    stack: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]

    while stack:
        current, path = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        for imported in graph.get(current, ()):
            if _matches(imported, FORBIDDEN_PROJECT_PREFIXES) or _matches(imported, FORBIDDEN_EXTERNAL_PREFIXES):
                forbidden_paths.append(ImportPath(path + (imported,)))
            if imported in modules and imported not in seen:
                stack.append((imported, path + (imported,)))
            elif imported and not imported.startswith("audioknigi"):
                direct_external.add(imported.split(".", 1)[0])

    return seen, forbidden_paths, direct_external


def _normalize_requirement_name(line: str) -> str:
    value = line.split("#", 1)[0].strip()
    if not value or value.startswith("-"):
        return ""
    value = value.split(";", 1)[0].strip()
    match = re.match(r"([A-Za-z0-9_.-]+)", value)
    return (match.group(1) if match else "").lower().replace("_", "-")


def _declared_requirements(path: Path, seen: set[Path] | None = None) -> set[str]:
    seen = set() if seen is None else seen
    resolved = path.resolve()
    if resolved in seen:
        return set()
    seen.add(resolved)
    declared: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement ")):
            target = line.split(maxsplit=1)[1].strip()
            declared.update(_declared_requirements(path.parent / target, seen))
            continue
        name = _normalize_requirement_name(line)
        if name:
            declared.add(name)
    return declared


def validate_requirements(path: Path) -> list[str]:
    declared = _declared_requirements(path)
    missing: list[str] = []
    for distribution in QT_RUNTIME_DISTRIBUTIONS:
        canonical = distribution.lower().replace("_", "-")
        if canonical not in declared:
            missing.append(distribution)
    return missing


def run_audit(*, verbose: bool = False) -> int:
    modules = discover_project_modules()
    graph = build_graph(modules)
    reachable, forbidden_paths, external = walk_reachable(graph, modules)
    missing_requirements = validate_requirements(ROOT / "requirements-qt.txt")

    if verbose:
        print(f"Qt entry reachable project modules: {len(reachable)}")
        for name in sorted(reachable):
            print(f"  {name}")
        print("Direct external import roots:", ", ".join(sorted(external)) or "none")

    if forbidden_paths:
        print("QT IMPORT AUDIT: FAILED - legacy runtime boundary crossed", file=sys.stderr)
        for path in forbidden_paths:
            print(f"  {path.format()}", file=sys.stderr)
    if missing_requirements:
        print(
            "QT IMPORT AUDIT: FAILED - requirements-qt.txt misses: "
            + ", ".join(missing_requirements),
            file=sys.stderr,
        )
    if forbidden_paths or missing_requirements:
        return 31

    print(
        f"QT IMPORT AUDIT: OK ({len(reachable)} project modules reachable, "
        f"no legacy frontend path)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    return run_audit(verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
