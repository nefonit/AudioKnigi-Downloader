from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_search_results_have_one_shared_active_state_for_both_modes() -> None:
    search = src("audioknigi/qt/mixins/search.py")
    assert "def _set_search_results_active(self, active: bool) -> None:" in search
    assert "self._search_results_active = active" in search
    assert "self.search_results_stack.setCurrentIndex(1 if active else 0)" in search
    assert "self.easy_search_table.setVisible(active)" in search
    assert "self.easy_use_result_button.setVisible(active)" in search
    assert "self.easy_copy_url_button.setVisible(active)" in search
    assert "self._set_search_results_active(True)" in search


def test_switching_to_advanced_with_pending_results_opens_search_tab() -> None:
    main = src("audioknigi/qt/main_window.py")
    search = src("audioknigi/qt/mixins/search.py")
    assert "search_owns_view = self._sync_search_presentation_for_mode(mode)" in main
    assert "elif search_owns_view:" in main
    assert "target = self.search_table" in main
    assert "def _sync_search_presentation_for_mode(self, mode: str) -> bool:" in search
    assert 'if mode == "advanced":' in search
    assert "self.tabs.setCurrentIndex(self.TAB_SEARCH)" in search


def test_search_selection_is_mirrored_between_easy_and_advanced_tables() -> None:
    search = src("audioknigi/qt/mixins/search.py")
    assert "selection_model.selectionChanged.connect(self._advanced_search_selection_changed)" in search
    assert "def _sync_search_selection(self, source_table, target_table) -> None:" in search
    assert "focus_table_row(target_table, row, column=1, focus=False)" in search
    assert "self._sync_search_selection(self.search_table, self.easy_search_table)" in search
    assert "self._sync_search_selection(self.easy_search_table, self.search_table)" in search


def test_all_query_fields_are_synchronized_across_modes() -> None:
    settings = src("audioknigi/qt/mixins/settings.py")
    assert 'for name in ("book_url_edit", "easy_input", "search_edit")' in settings


def test_selecting_a_result_ends_shared_search_selection_stage() -> None:
    search = src("audioknigi/qt/mixins/search.py")
    marker = "self._pending_search_result = selected_result\n        self._set_search_results_active(False)"
    assert marker in search
