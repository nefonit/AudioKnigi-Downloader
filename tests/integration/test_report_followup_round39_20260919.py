from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_production_theme_has_cohesive_app_chrome() -> None:
    theme = src("audioknigi/qt/theme.py")
    for selector in (
        "QWidget#appHeader", "QLabel#appBrand", "QLabel#appSubtitle",
        "QMenuBar", "QMenu", "QStatusBar", "QToolTip",
    ):
        assert selector in theme
    assert 'accent = "#0a6ed1"' in theme
    assert 'focus = "#e5a93c"' in theme


def test_production_theme_polishes_buttons_inputs_and_focus_without_weakening_focus_ring() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert 'QPushButton[role="primary"]' in theme
    assert 'QPushButton[role="segment"]' in theme
    assert "QLineEdit:hover" in theme
    assert "QComboBox::drop-down" in theme
    assert "QFocusFrame#keyboardFocusFrame" in theme
    assert "border: 2px solid {focus}" in theme


def test_tables_lists_headers_tabs_and_scrollbars_have_production_styling() -> None:
    theme = src("audioknigi/qt/theme.py")
    for selector in (
        "QTableView, QTableWidget, QListWidget, QTreeView",
        "QHeaderView::section",
        "QTabWidget::pane",
        "QTabBar::tab",
        "QScrollBar:vertical",
        "QScrollBar:horizontal",
    ):
        assert selector in theme
    assert "gridline-color: transparent" in theme
    assert "selection-background-color" in theme


def test_main_window_uses_named_production_header_and_roomier_easy_card() -> None:
    source = src("audioknigi/qt/main_window.py")
    assert 'header.setObjectName("appHeader")' in source
    assert 'title.setObjectName("appBrand")' in source
    assert 'self.subtitle_label.setObjectName("appSubtitle")' in source
    assert "layout.setContentsMargins(30, 28, 30, 28)" in source
    assert "self.easy_input.setMinimumHeight(42)" in source
    assert "self.easy_download_button.setMinimumHeight(48)" in source


def test_easy_search_and_book_card_are_visually_clean_but_accessible() -> None:
    source = src("audioknigi/qt/main_window.py")
    assert "self.easy_search_table.setShowGrid(False)" in source
    assert "self.easy_search_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)" in source
    assert "easy_book_layout.setContentsMargins(18, 18, 18, 18)" in source
    assert "easy_book_layout.setSpacing(18)" in source
    assert "self.easy_cover_label.setFixedSize(168, 168)" in source
    assert "self.easy_description.setMaximumHeight(150)" in source
    assert "self.easy_description.setTabChangesFocus(True)" in source


def test_advanced_tables_use_clean_gridless_per_pixel_scrolling() -> None:
    expectations = {
        "audioknigi/qt/main_window_pages.py": "self.track_table",
        "audioknigi/qt/mixins/search.py": "self.search_table",
        "audioknigi/qt/mixins/history.py": "self.history_table",
        "audioknigi/qt/mixins/queue.py": "self.queue_table",
    }
    for relative, widget in expectations.items():
        source = src(relative)
        assert f"{widget}.setShowGrid(False)" in source
        assert f"{widget}.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)" in source


def test_player_card_is_wider_and_more_comfortable_for_production_layout() -> None:
    source = src("audioknigi/qt/player_mixin.py")
    assert "card.setMaximumWidth(1180)" in source
    assert "card_layout.setContentsMargins(24, 24, 24, 24)" in source
    assert "self.player_chapter_list.setMinimumHeight(150)" in source
