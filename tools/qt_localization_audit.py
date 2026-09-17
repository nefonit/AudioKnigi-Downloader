from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audioknigi.i18n import _PHASE29_LITERAL_TRANSLATIONS, _PHASE29_RUNTIME_EXACT, localize_runtime_text  # noqa: E402

CYRILLIC = re.compile(r"[А-Яа-яЁё]")


def _strict_json_catalog_issues() -> list[str]:
    """Reject duplicate JSON object keys before Python silently overwrites them."""
    issues: list[str] = []
    locale_dir = ROOT / "audioknigi" / "locales"

    def strict_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    for path in sorted(locale_dir.glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)
        except (OSError, ValueError, TypeError) as exc:
            issues.append(f"locale catalog {path.name}: {exc}")
    return issues


def _assignment_value(node: ast.AST, name: str):
    if isinstance(node, ast.Assign):
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return node.value
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id == name and node.value is not None:
            return node.value
    return None


def _load_help_topics():
    path = ROOT / "audioknigi" / "qt" / "help_center.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        value = _assignment_value(node, "TOPICS")
        if value is not None:
            return ast.literal_eval(value)
    raise RuntimeError("TOPICS not found")


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        value = _assignment_value(node, name)
        if value is not None:
            return ast.literal_eval(value)
    raise RuntimeError(f"{name} not found in {path}")


def _accessible_name_literals(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "configure_accessible"):
            continue
        for kw in node.keywords:
            if kw.arg != "name":
                continue
            value = kw.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str) and CYRILLIC.search(value.value):
                values.add(value.value)
    return values


def _literal_l_calls(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        func = node.func
        is_localizer = (
            isinstance(func, ast.Attribute) and func.attr == "_l"
        ) or (isinstance(func, ast.Name) and func.id == "_l")
        if is_localizer:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and CYRILLIC.search(arg.value):
                values.add(arg.value)
    return values


def _ui_text_literals(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_ui_text = (
            isinstance(func, ast.Name) and func.id == "ui_text"
        ) or (isinstance(func, ast.Attribute) and func.attr == "ui_text")
        if not is_ui_text:
            continue
        arg = node.args[1] if len(node.args) >= 2 else None
        if arg is None:
            for keyword in node.keywords:
                if keyword.arg in {"russian_text", "default"}:
                    arg = keyword.value
                    break
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and CYRILLIC.search(arg.value):
            values.add(arg.value)
    return values


def _direct_visible_russian(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    issues: list[str] = []
    constructors = {"QLabel", "QPushButton", "QCheckBox", "QGroupBox", "QAction"}
    methods = {"setText", "setWindowTitle", "setPlaceholderText", "addAction", "addMenu", "addItem", "setToolTip", "setWhatsThis", "setAccessibleName", "setAccessibleDescription"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        arg = node.args[0]
        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str) or not CYRILLIC.search(arg.value):
            continue
        called = ""
        if isinstance(node.func, ast.Name):
            called = node.func.id
        elif isinstance(node.func, ast.Attribute):
            called = node.func.attr
        if called in constructors or called in methods:
            issues.append(f"{path.relative_to(ROOT)}:{getattr(node, 'lineno', '?')}: raw visible literal {arg.value!r}")
    return issues


def _leading_constant_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _leading_constant_text(node.left)
    return None

def _runtime_visible_literals(path: Path, *, include_log: bool = False) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: set[str] = set()
    methods = {"set_status", "_show_message", "_ask_yes_no"}
    if include_log:
        methods.add("log")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func.attr if isinstance(node.func, ast.Attribute) else ""
        if called not in methods:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if CYRILLIC.search(arg.value):
                    values.add(arg.value)
                continue
            # A concatenated visible status such as
            # ``"Поиск не выполнен: " + details`` needs its translatable
            # leading prefix audited. Technical log composition is intentionally
            # excluded because full log lines are covered by runtime regexes.
            if called != "log" and isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                value = _leading_constant_text(arg)
                if value and CYRILLIC.search(value):
                    values.add(value)
    return values


def _unwrapped_dynamic_visible_russian(path: Path) -> list[str]:
    """Reject raw Russian f-strings sent directly to visible/accessibility setters."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    issues: list[str] = []
    methods = {
        "setText", "setToolTip", "setWhatsThis", "setPlaceholderText",
        "setAccessibleName", "setAccessibleDescription", "setWindowTitle",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        called = node.func.attr if isinstance(node.func, ast.Attribute) else ""
        if called not in methods:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.JoinedStr):
            rendered = ast.unparse(arg)
            if CYRILLIC.search(rendered):
                issues.append(
                    f"{path.relative_to(ROOT)}:{getattr(node, 'lineno', '?')}: "
                    f"unlocalized dynamic visible text {rendered!r}"
                )
    return issues


def audit() -> list[str]:
    issues: list[str] = []
    issues.extend(_strict_json_catalog_issues())

    # Catalogs intentionally overlap at a few compatibility boundaries. Keep
    # those duplicates byte-for-byte consistent so future edits cannot make
    # ui_text() and localize_runtime_text() disagree for the same source text.
    locale_dir = ROOT / "audioknigi" / "locales"
    runtime_exact = json.loads((locale_dir / "runtime_exact.json").read_text(encoding="utf-8"))
    legacy_literals = json.loads((locale_dir / "legacy_literals.json").read_text(encoding="utf-8"))
    for language in ("uk", "de", "en"):
        literal_map = legacy_literals.get(language, {})
        for source, variants in runtime_exact.items():
            if source not in literal_map or language not in variants:
                continue
            if literal_map[source] != variants[language]:
                issues.append(
                    f"catalog mismatch {language}: {source!r}: "
                    f"literal={literal_map[source]!r} runtime_exact={variants[language]!r}"
                )
        keys = list(literal_map)
        if keys != sorted(keys):
            issues.append(f"legacy_literals {language} keys are not sorted")
    qt_dir = ROOT / "audioknigi" / "qt"
    main = qt_dir / "main_window.py"
    literals: set[str] = set()
    qt_paths = sorted(qt_dir.rglob("*.py"))
    for path in qt_paths:
        literals |= _literal_l_calls(path)
        literals |= _ui_text_literals(path)
        literals |= _accessible_name_literals(path)
    for language in ("uk", "de", "en"):
        translated = _PHASE29_LITERAL_TRANSLATIONS.get(language, {})
        for literal in sorted(literals):
            exact_entry = _PHASE29_RUNTIME_EXACT.get(literal)
            has_exact = isinstance(exact_entry, dict) and language in exact_entry
            if literal not in translated and not has_exact:
                issues.append(f"missing {language} translation: {literal}")

    # Scan every Qt module, not only the main window.  This catches a future raw
    # Russian button/label, tooltip or accessibility string accidentally added
    # to a dialog, player, tray, etc.
    for path in qt_paths:
        issues.extend(_direct_visible_russian(path))
        issues.extend(_unwrapped_dynamic_visible_russian(path))

    # Status bars, modal helpers and the user-visible technical session log
    # translate at the runtime boundary. Verify literal Russian messages used
    # there are covered, including downloader/engine log lines forwarded into
    # the Qt technical-log panel.
    same_language_ok = {"Одним MP3", "Пауза…", "недоступно", "Незавершено"}
    runtime_literals = set(_runtime_visible_literals(main))
    runtime_paths = [
        ROOT / "audioknigi/downloader.py",
        ROOT / "audioknigi/download_engine.py",
        ROOT / "audioknigi/services/book_analysis_service.py",
        ROOT / "audioknigi/qt/main_window_pages.py",
        ROOT / "audioknigi/qt/player_mixin.py",
        *sorted((ROOT / "audioknigi/download").glob("*.py")),
        *sorted((ROOT / "audioknigi/qt/mixins").glob("*.py")),
    ]
    for path in runtime_paths:
        runtime_literals |= _runtime_visible_literals(path, include_log=True)
    for literal in sorted(runtime_literals):
        for language in ("uk", "de", "en"):
            translated = localize_runtime_text(language, literal)
            if language in ("de", "en") and CYRILLIC.search(translated):
                issues.append(f"runtime {language} translation still Cyrillic: {literal}")
            if translated == literal and literal not in same_language_ok:
                issues.append(f"missing runtime {language} translation: {literal}")

    onboarding = qt_dir / "onboarding.py"
    onboarding_text = _literal_assignment(onboarding, "_ONBOARDING_TEXT")
    onboarding_hints = _literal_assignment(onboarding, "_ONBOARDING_HINTS")
    expected_onboarding_keys = set(onboarding_text["ru"])
    expected_hint_keys = set(onboarding_hints["ru"])
    for language in ("uk", "de", "en"):
        if set(onboarding_text.get(language, {})) != expected_onboarding_keys:
            issues.append(f"onboarding text key mismatch for {language}")
        if set(onboarding_hints.get(language, {})) != expected_hint_keys:
            issues.append(f"onboarding hint key mismatch for {language}")
    for language in ("de", "en"):
        for value in onboarding_text.get(language, {}).values():
            if CYRILLIC.search(str(value)):
                issues.append(f"Cyrillic leaked into {language} onboarding text: {value}")
        for value in onboarding_hints.get(language, {}).values():
            if CYRILLIC.search(str(value)):
                issues.append(f"Cyrillic leaked into {language} onboarding hint: {value}")

    topics = _load_help_topics()
    expected_keys = [key for key, _title, _body in topics["ru"]]
    for language in ("uk", "de", "en"):
        actual_keys = [key for key, _title, _body in topics[language]]
        if actual_keys != expected_keys:
            issues.append(f"help topic mismatch for {language}: {actual_keys!r}")
    for language in ("de", "en"):
        for key, title, body in topics[language]:
            if CYRILLIC.search(title) or CYRILLIC.search(body):
                issues.append(f"Cyrillic leaked into {language} help topic {key}")
    return issues


def main() -> int:
    issues = audit()
    if issues:
        print("FAILED")
        for issue in issues:
            print(f"issue={issue}")
        return 1
    print("OK")
    print("languages=ru,uk,de,en")
    print("static_ui_literals=translated")
    print("help_topics=complete")
    print("onboarding=complete")
    print("accessible_names=translated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
