from __future__ import annotations

"""Fail when refactored modules reference unresolved module globals.

``compileall`` catches syntax errors but not names that were left behind when a
method moved into another module.  This audit uses Python's symbol table to
catch that class of split-module regression before a Qt action reaches it.
"""

import builtins
from pathlib import Path
import symtable

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "audioknigi"
_SPECIAL_GLOBALS = {
    "__annotations__",
    "__builtins__",
    # Python 3.14+ compiler/symtable implementation detail for conditional
    # annotation evaluation. It can appear as a referenced synthetic module
    # global even though user code never defines or reads it directly.
    "__conditional_annotations__",
    "__doc__",
    "__file__",
    "__loader__",
    "__name__",
    "__package__",
    "__path__",
    "__spec__",
    # Present as a built-in alias on Windows but absent on POSIX.
    "WindowsError",
}
_BUILTINS = set(dir(builtins))


def _module_definitions(table: symtable.SymbolTable) -> set[str]:
    return {
        symbol.get_name()
        for symbol in table.get_symbols()
        if symbol.is_imported() or symbol.is_assigned() or symbol.is_namespace() or symbol.is_parameter()
    }


def _missing_globals(table: symtable.SymbolTable, module_definitions: set[str]) -> set[tuple[str, str]]:
    missing: set[tuple[str, str]] = set()

    def visit(scope: symtable.SymbolTable) -> None:
        for symbol in scope.get_symbols():
            name = symbol.get_name()
            if not symbol.is_referenced() or not symbol.is_global():
                continue
            if name in module_definitions or name in _BUILTINS or name in _SPECIAL_GLOBALS:
                continue
            missing.add((scope.get_name(), name))
        for child in scope.get_children():
            visit(child)

    visit(table)
    return missing


def main() -> int:
    failures: list[str] = []
    modules = [ROOT / "audioknigi_qt.py", *sorted(PACKAGE_ROOT.rglob("*.py"))]
    for path in modules:
        source = path.read_text(encoding="utf-8")
        try:
            table = symtable.symtable(source, str(path), "exec")
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)}: syntax error: {exc}")
            continue
        module_definitions = _module_definitions(table)
        for scope_name, name in sorted(_missing_globals(table, module_definitions)):
            failures.append(f"{path.relative_to(ROOT)}:{scope_name}: unresolved global {name}")

    if failures:
        print("UNDEFINED GLOBAL AUDIT: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"UNDEFINED GLOBAL AUDIT: OK ({len(modules)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
