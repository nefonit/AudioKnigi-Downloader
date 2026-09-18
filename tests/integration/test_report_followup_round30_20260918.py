from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_easy_mode_exposes_narration_picker_for_multi_variant_results() -> None:
    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    search = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    assert "self.easy_narration_combo = QComboBox()" in main
    assert 'identifier="easy_narration_variant"' in main
    assert "easy_selection_model.selectionChanged.connect(self._easy_search_selection_changed)" in main
    assert "def _refresh_easy_narration_variants" in search
    assert 'self.easy_narration_combo.addItem(self._l("Выберите озвучку…"), "")' in search
    assert "for idx, item in enumerate(variants, start=1):" in search


def test_easy_mode_does_not_auto_choose_first_of_multiple_narrations() -> None:
    search = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    assert "self.easy_narration_combo.setCurrentIndex(0)" in search
    assert "narration_ready = len(variants) <= 1 or self._easy_selected_narration(easy_result) is not None" in search
    assert 'self.set_status(self._l("Выберите озвучку перед анализом книги."), assertive=True)' in search
    assert "self.easy_narration_combo.setFocus(Qt.FocusReason.OtherFocusReason)" in search


def test_selected_easy_narration_url_is_used_for_analysis_and_preserves_variants() -> None:
    search = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    block = search[search.index("def use_selected_result"):search.index("def copy_selected_url")]
    assert "selected_variant = self._easy_selected_narration(result)" in block
    assert "selected_result = replace(" in block
    assert "url=selected_url" in block
    assert "narrator=selected_narrator or result.narrator" in block
    assert "self._pending_search_result = selected_result" in block
    assert "self.book_url_edit.setText(selected_result.url)" in block


def test_single_narration_keeps_one_click_flow() -> None:
    search = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    assert "multiple = len(variants) > 1" in search
    assert 'self.easy_narration_label.setVisible(multiple and self.current_ui_mode() == "easy")' in search
    assert 'self.easy_narration_combo.setVisible(multiple and self.current_ui_mode() == "easy")' in search
