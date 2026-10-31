"""Help Center content/UI split preserves accessibility and localization contracts."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "audioknigi/qt/help_content.py"
DIALOG = ROOT / "audioknigi/qt/help_center.py"

TOPIC_KEYS = (
    "start", "modes", "book", "search", "download", "quality",
    "queue", "history", "player", "settings", "files", "backup",
    "accessibility", "shortcuts", "diagnostics", "troubleshooting",
)


def _constants():
    tree = ast.parse(CONTENT.read_text(encoding="utf-8"))
    return {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
        and target.id in {
            "TOPICS", "ROUND55_TOPIC_DETAILS_RU", "ROUND55_TOPIC_DETAILS_EN",
            "ROUND55_TOPIC_DETAILS_DE", "ROUND55_TOPIC_DETAILS_UK",
        }
    }


def test_content_is_pure_python_and_each_language_has_same_topics():
    raw = CONTENT.read_text(encoding="utf-8")
    assert "PySide6" not in raw
    data = _constants()
    assert set(data["TOPICS"]) == {"ru", "de", "en", "uk"}
    for language, rows in data["TOPICS"].items():
        assert tuple(key for key, _, _ in rows) == TOPIC_KEYS
        assert set(data[f"ROUND55_TOPIC_DETAILS_{language.upper()}"]) == set(TOPIC_KEYS)


def test_dialog_preserves_accessible_controls_focus_and_copy_report():
    source = DIALOG.read_text(encoding="utf-8")
    for marker in (
        "class QtHelpCenter(QDialog)", "QSplitter", 'identifier="help_center"',
        'identifier="help_topics"', 'identifier="help_text"',
        'identifier="help_copy_crash_report"', 'identifier="help_close"',
        "self.topics.setFocus()", "self.copy_report_callback()",
        "self.text.setHtml(_format_help_body_html(title, body))",
    ):
        assert marker in source


def test_backwards_compatible_help_content_exports_are_identical():
    from audioknigi.qt import help_center, help_content

    assert help_center.TOPICS is help_content.TOPICS
    assert help_center.TOPICS_RU is help_content.TOPICS["ru"]
    assert help_center.ROUND55_TOPIC_DETAILS is help_content.ROUND55_TOPIC_DETAILS
