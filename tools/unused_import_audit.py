from __future__ import annotations

"""Fail when runtime implementation layers accumulate unused imports."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    *sorted((ROOT / "audioknigi" / "download").glob("*.py")),
    *sorted((ROOT / "audioknigi" / "qt" / "mixins").glob("*.py")),
    *sorted((ROOT / "audioknigi" / "services").glob("*.py")),
    ROOT / "audioknigi" / "qt" / "main_window.py",
    ROOT / "audioknigi" / "core.py",
    ROOT / "audioknigi" / "cover_fetch.py",
    ROOT / "audioknigi" / "i18n.py",
    ROOT / "audioknigi" / "knigavuhe.py",
    ROOT / "audioknigi" / "poleknig.py",
    ROOT / "audioknigi" / "network_dns.py",
    ROOT / "audioknigi" / "diagnostics" / "support_bundle.py",
]


def _bound_name(alias: ast.alias, *, plain_import: bool) -> str:
    if alias.asname:
        return alias.asname
    return alias.name.split(".", 1)[0] if plain_import else alias.name


def _annotation_loaded_names(tree: ast.AST) -> set[str]:
    loaded: set[str] = set()

    def collect(annotation: ast.AST | None) -> None:
        if annotation is None:
            return
        for child in ast.walk(annotation):
            if isinstance(child, ast.Name):
                loaded.add(child.id)
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                try:
                    parsed = ast.parse(child.value, mode="eval")
                except SyntaxError:
                    continue
                for subchild in ast.walk(parsed):
                    if isinstance(subchild, ast.Name):
                        loaded.add(subchild.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            collect(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            collect(node.returns)
        elif isinstance(node, ast.AnnAssign):
            collect(node.annotation)
    return loaded


def _module_scope_imports(statements: list[ast.stmt]):
    for node in statements:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        nested: list[list[ast.stmt]] = []
        if isinstance(node, ast.Try):
            nested.extend([node.body, node.orelse, node.finalbody])
            nested.extend(handler.body for handler in node.handlers)
        elif isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While)):
            nested.extend([node.body, node.orelse])
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            nested.append(node.body)
        elif isinstance(node, ast.Match):
            nested.extend(case.body for case in node.cases)
        for block in nested:
            yield from _module_scope_imports(block)


def unused_imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    loaded = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    loaded.update(_annotation_loaded_names(tree))

    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            continue
        value = node.value
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for item in value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    loaded.add(item.value)

    issues: list[tuple[int, str]] = []
    for node in _module_scope_imports(tree.body):
        if isinstance(node, ast.Import):
            pairs = [(_bound_name(alias, plain_import=True), alias) for alias in node.names]
        else:
            if node.module == "__future__":
                continue
            pairs = [(_bound_name(alias, plain_import=False), alias) for alias in node.names if alias.name != "*"]
        for name, _alias in pairs:
            if name not in loaded:
                issues.append((node.lineno, name))
    return issues


def main() -> int:
    failures = []
    for path in TARGETS:
        if path.name == "__init__.py":
            continue
        for line, name in unused_imports(path):
            failures.append((path.relative_to(ROOT), line, name))
    if failures:
        print("UNUSED IMPORT AUDIT: FAIL")
        for path, line, name in failures:
            print(f"  {path}:{line}: {name}")
        return 1
    print(f"UNUSED IMPORT AUDIT: OK ({len(TARGETS)} implementation modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
