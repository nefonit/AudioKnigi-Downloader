from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_advanced_data_tabs_use_full_workspace_width() -> None:
    window = src("audioknigi/qt/main_window.py")
    assert "layout.setContentsMargins(16, 10, 16, 12)" in window
    assert "layout.setSpacing(8)" in window
    assert "self.tabs.setMaximumWidth(16777215)" in window
    assert "self.mode_stack.addWidget(self.tabs)" in window
    assert "self.tabs.setMaximumWidth(1500)" not in window


def test_settings_and_player_remain_centered_form_cards() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    player = src("audioknigi/qt/player_mixin.py")
    theme = src("audioknigi/qt/theme.py")
    assert 'settings_card.setObjectName("settingsCard")' in pages
    assert "settings_card.setMaximumWidth(1180)" in pages
    assert "center.addStretch(1)" in pages
    assert 'card.setObjectName("playerCard")' in player
    assert "card.setMaximumWidth(1180)" in player
    assert "QWidget#easyCard, QWidget#playerCard, QWidget#settingsCard" in theme


def test_search_columns_prioritize_full_author_and_narrator_names() -> None:
    search = src("audioknigi/qt/mixins/search.py")
    assert "for column in (0, 4, 5, 6):" in search
    assert "search_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)" in search
    assert "search_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)" in search
    assert "search_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)" in search
    assert "self.search_table.setColumnWidth(2, 260)" in search
    assert "self.search_table.setColumnWidth(3, 280)" in search


def test_history_folder_path_gets_remaining_width() -> None:
    history = src("audioknigi/qt/mixins/history.py")
    assert "for column in (0, 1, 5):" in history
    assert "history_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)" in history
    assert "history_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)" in history
    assert "history_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)" in history
    assert "history_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)" in history
    assert "self.history_table.setColumnWidth(2, 320)" in history
    assert "self.history_table.setColumnWidth(3, 220)" in history
    assert "self.history_table.setColumnWidth(4, 220)" in history


def test_book_chapter_title_stretches_and_source_remains_readable() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    assert "for column in (0, 1, 2, 3, 4, 5):" in pages
    assert "track_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)" in pages
    assert "track_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)" in pages
    assert "self.track_table.setColumnWidth(7, 280)" in pages


def test_wide_tables_have_stronger_zebra_striping() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert 'table_bg = "#181a1f"' in theme
    assert 'table_alt = "#20242c"' in theme
    assert 'table_grid = "#2d333f"' in theme
    assert "QTableView, QTableWidget {{" in theme
    assert "background: {table_bg};" in theme
    assert "alternate-background-color: {table_alt};" in theme
    assert "QTableView::item, QTableWidget::item {{ padding: 6px 10px;" in theme


def test_menu_is_shifted_away_from_top_left_overlay() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert "spacing: 6px;" in theme
    assert "padding: 3px 6px 3px 10px;" in theme
