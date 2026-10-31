"""Behavior and compatibility contracts for the Help Center presentation split."""

import pytest

from audioknigi.qt.help_actions import resolve_help_topic
from audioknigi.qt.help_content import TOPICS, ROUND55_TOPIC_DETAILS
from audioknigi.qt.help_formatter import _format_help_body_html


def test_html_escapes_untrusted_help_text_and_keeps_markup():
    html = _format_help_body_html("A <B> & C", 'Text <script>alert("x")</script> & Ctrl+F')
    assert "<h2>A &lt;B&gt; &amp; C</h2>" in html
    assert "&lt;script&gt;" in html
    assert "<script>" not in html
    assert "<kbd>Ctrl+F</kbd>" in html
    assert "line-height: 1.42" in html


def test_multilingual_shortcuts_and_list_rendering():
    html = _format_help_body_html(
        "Keyboard",
        "1. Ctrl+F\n2. Strg+Umschalt+Tab\n\n• Leertaste\n• Пробіл\n\nNext\nline",
    )
    assert '<ol>' in html
    assert '<ul>' in html
    assert "<kbd>Ctrl+F</kbd>" in html
    assert "<kbd>Strg+Umschalt+Tab</kbd>" in html
    assert "<kbd>Leertaste</kbd>" in html
    assert "<kbd>Пробіл</kbd>" in html
    assert "<p>Next<br>line</p>" in html


@pytest.mark.parametrize("language", ["ru", "uk", "de", "en"])
def test_topic_selection_preserves_supplemental_details(language):
    topics = TOPICS[language]
    selected = resolve_help_topic(language, topics, 0)
    assert selected is not None
    title, body = selected
    _, original_title, original_body = topics[0]
    assert title == original_title
    assert body == original_body.rstrip() + "\n\n" + ROUND55_TOPIC_DETAILS[language]["start"]


def test_invalid_row_does_not_produce_or_change_topic():
    assert resolve_help_topic("ru", TOPICS["ru"], -1) is None
    assert resolve_help_topic("ru", TOPICS["ru"], len(TOPICS["ru"])) is None


def test_help_center_reexports_identical_formatter():
    from audioknigi.qt.help_center import _format_help_body_html as legacy
    assert legacy is _format_help_body_html


def test_qt_callbacks_retain_original_action_boundaries():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[2] / "audioknigi/qt/help_center.py").read_text(encoding="utf-8")
    assert "self.topics.currentRowChanged.connect(self._show_row)" in source
    assert "copy_btn.clicked.connect(self._copy_report)" in source
    assert "close_btn.clicked.connect(self.accept)" in source
    assert "self.topics.setFocus()" in source
    assert "if callable(self.copy_report_callback):" in source
    assert "self.copy_report_callback()" in source
