from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HELP_CENTER = ROOT / "audioknigi" / "qt" / "help_center.py"
MESSAGES = ROOT / "audioknigi" / "locales" / "messages.json"
ACCESSIBILITY_UI = ROOT / "audioknigi" / "qt" / "mixins" / "accessibility_ui.py"


def _topics() -> dict[str, tuple[tuple[str, str, str], ...]]:
    tree = ast.parse(HELP_CENTER.read_text(encoding="utf-8"), filename=str(HELP_CENTER))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TOPICS" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("TOPICS not found")


def test_help_center_is_full_guide_in_all_languages() -> None:
    topics = _topics()
    assert set(topics) == {"ru", "uk", "de", "en"}
    expected_keys = [
        "start", "modes", "book", "search", "download", "quality", "queue", "history",
        "player", "settings", "files", "backup", "accessibility", "shortcuts", "diagnostics",
        "troubleshooting",
    ]
    for language, rows in topics.items():
        assert [key for key, _title, _body in rows] == expected_keys, language
        assert len(rows) == 16
        assert all(title.strip() for _key, title, _body in rows)
        assert all(len(body.strip()) >= 550 for _key, _title, body in rows), language
        assert all("\n\n" in body for _key, _title, body in rows), language


def test_russian_help_covers_complete_workflow() -> None:
    rows = {key: body for key, _title, body in _topics()["ru"]}
    assert "audioknigi.com.ua" in rows["start"]
    assert "Скачать одним MP3" in rows["book"]
    assert "Range" in rows["download"]
    assert "FFmpeg" in rows["quality"]
    assert "Повторить задачу" in rows["queue"]
    assert "CSV" in rows["history"]
    assert "player_positions.json" in rows["player"]
    assert "Audiobookshelf" in rows["settings"]
    assert "{Track_Number}" in rows["files"]
    assert "резерв" in rows["backup"].casefold()
    assert "NVDA/JAWS" in rows["accessibility"]
    assert "Ctrl+Shift+F12" in rows["shortcuts"]
    assert "диагностический пакет" in rows["diagnostics"].casefold()
    assert "Восстановить" in rows["troubleshooting"]


def test_help_header_no_longer_calls_it_short_instructions() -> None:
    messages = json.loads(MESSAGES.read_text(encoding="utf-8"))
    forbidden = {
        "ru": "коротк",
        "uk": "коротк",
        "en": "short instruction",
        "de": "kurze anleitung",
    }
    for language, needle in forbidden.items():
        intro = str(messages[language]["help_short_intro"])
        assert needle not in intro.casefold()
        assert len(intro) >= 60


def test_help_menu_opens_dedicated_shortcuts_topic_on_f1() -> None:
    source = ACCESSIBILITY_UI.read_text(encoding="utf-8")
    assert 'shortcuts_action.triggered.connect(lambda: self.show_context_help(topic="shortcuts"))' in source
    assert 'help_action.setShortcut(QKeySequence("Shift+F1"))' in source
    assert any(key == "shortcuts" for key, _title, _body in _topics()["ru"])
