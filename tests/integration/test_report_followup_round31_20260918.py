from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_manual_empty_easy_input_uses_same_reset_path_as_next_book_button() -> None:
    source = _source("audioknigi/qt/main_window.py")
    assert "self.easy_input.textEdited.connect(self._easy_user_input_edited)" in source
    assert "def _easy_reset_to_initial_state" in source
    assert "def _easy_user_input_edited" in source
    assert "if self._easy_operation_active():" in source
    assert "self._easy_reset_to_initial_state(clear_input=False, focus=False)" in source
    easy_start = source.index("def easy_add_another_book")
    easy_end = source.index("def _play_event_sound", easy_start)
    easy_block = source[easy_start:easy_end]
    assert "self.book_url_edit.clear()" in easy_block
    assert "self._easy_reset_to_initial_state(clear_input=True, focus=True)" in easy_block


def test_easy_reset_clears_book_search_variant_and_description_state() -> None:
    source = _source("audioknigi/qt/main_window.py")
    start = source.index("def _easy_reset_to_initial_state")
    end = source.index("def _easy_user_input_edited", start)
    block = source[start:end]
    for expected in (
        "self.current_book = None",
        "self._pending_search_result = None",
        "self._known_narration_variants = None",
        "self.search_model.set_results([])",
        "self.easy_description.clear()",
        "self.easy_book_card.setVisible(False)",
        "self.easy_download_button.setEnabled(False)",
        "self.book_url_edit.clear()",
    ):
        assert expected in block


def test_easy_mode_has_accessible_annotation_block() -> None:
    source = _source("audioknigi/qt/main_window.py")
    assert 'self.easy_description_title = QLabel(self._l("Аннотация"))' in source
    assert "self.easy_description = QPlainTextEdit()" in source
    assert "self.easy_description.setReadOnly(True)" in source
    assert "self.easy_description.setMaximumHeight(120)" in source
    assert 'identifier="easy_book_description"' in source
    assert "self.easy_description_title.setVisible(False)" in source
    assert "self.easy_description.setVisible(False)" in source


def test_analysis_populates_easy_annotation_only_when_description_exists() -> None:
    source = _source("audioknigi/qt/mixins/analysis_download.py")
    assert 'easy_description = str(book.description or "").strip()' in source
    assert "self.easy_description.setPlainText(easy_description)" in source
    assert "self.easy_description_title.setVisible(bool(easy_description))" in source
    assert "self.easy_description.setVisible(bool(easy_description))" in source
    assert "self.easy_description.setAccessibleDescription(easy_description)" in source
