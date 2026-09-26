from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _parent_map(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _function_name(node, parents) -> str:
    cur = node
    while cur in parents:
        cur = parents[cur]
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur.name
    return "<module>"


def _broad_handler_kind(node: ast.ExceptHandler) -> str:
    if node.type is None:
        return "bare"
    types = node.type.elts if isinstance(node.type, ast.Tuple) else [node.type]
    names = {item.id for item in types if isinstance(item, ast.Name)}
    if "BaseException" in names:
        return "BaseException"
    return "Exception" if "Exception" in names else ""


def _empty_handler_body(body: list[ast.stmt]) -> bool:
    return bool(body) and all(
        isinstance(stmt, ast.Pass)
        or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            and stmt.value.value is Ellipsis)
        for stmt in body
    )


def scan(root: Path = ROOT) -> list[dict]:
    findings: list[dict] = []
    for path in sorted((root / "audioknigi").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = _parent_map(tree)
        rel = path.relative_to(root).as_posix()
        candidates = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            kind = _broad_handler_kind(node)
            if not kind or not _empty_handler_body(node.body):
                continue
            candidates.append((node.lineno, _function_name(node, parents), kind))
        counters: dict[tuple[str, str], int] = defaultdict(int)
        for line, fn, kind in sorted(candidates):
            counter_key = (fn, kind)
            counters[counter_key] += 1
            occurrence = counters[counter_key]
            key = f"{rel}:{fn}:{kind}#{occurrence}"
            findings.append({
                "key": key, "path": rel, "function": fn, "line": line,
                "handler": kind, "occurrence": occurrence,
            })
    return findings


def audit(root: Path = ROOT) -> tuple[list[dict], list[dict], list[str]]:
    root = Path(root)
    allow = json.loads((root / "tools" / "exception_allowlist.json").read_text(encoding="utf-8"))
    findings = scan(root)
    finding_keys = {item["key"] for item in findings}
    unknown = [item for item in findings if item["key"] not in allow]
    stale = sorted(set(allow) - finding_keys)
    return findings, unknown, stale


def main() -> int:
    findings, unknown, stale = audit()
    if unknown or stale:
        print("EXCEPTION AUDIT: FAIL")
        for item in unknown:
            print(
                f"unreviewed={item['path']}:{item['line']}:{item['function']}:"
                f"{item['handler']}#{item['occurrence']}"
            )
        for key in stale:
            print(f"stale_allowlist={key}")
        return 1
    print(f"EXCEPTION AUDIT: PASS reviewed_broad_exception_passes={len(findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
