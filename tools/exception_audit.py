from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "tools" / "exception_allowlist.json"


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
    if isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}:
        return node.type.id
    return ""


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
            if not kind or len(node.body) != 1 or not isinstance(node.body[0], ast.Pass):
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
    allow = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
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
