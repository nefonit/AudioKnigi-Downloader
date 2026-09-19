from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_secondary_text_has_stronger_dark_theme_contrast() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert 'secondary = "#9ba3af"' in theme
    assert 'QLabel#secondaryText {{ color: {secondary}; }}' in theme
    assert 'QLabel#emptyState {{\n    color: {secondary};' in theme


def test_focus_rings_are_refined_to_two_pixels_with_matched_radius() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert 'focus = "#e5a93c"' in theme
    assert 'QPushButton:focus {{ border: 2px solid {focus};' in theme
    assert 'QListWidget:focus, QTreeView:focus {{ border: 2px solid {focus}; border-radius: 6px; }}' in theme
    assert 'QLineEdit:focus, QComboBox:focus' in theme
    assert 'border: 2px solid {focus}; border-radius: 8px;' in theme


def test_mode_switch_is_a_real_segmented_control_holder() -> None:
    theme = src("audioknigi/qt/theme.py")
    window = src("audioknigi/qt/main_window.py")
    assert 'QWidget#modeSegmentHolder' in theme
    assert 'mode_segment_holder.setObjectName("modeSegmentHolder")' in window
    assert 'mode_segment_layout.setContentsMargins(2, 2, 2, 2)' in window
    assert 'mode_segment_layout.setSpacing(0)' in window


def test_advanced_workspace_is_centered_and_bounded_on_ultrawide_monitors() -> None:
    window = src("audioknigi/qt/main_window.py")
    assert 'self.advanced_page = QWidget(central)' in window
    assert 'advanced_layout.addStretch(1)' in window
    assert 'self.tabs.setMaximumWidth(1500)' in window
    assert 'advanced_layout.addWidget(self.tabs, 1)' in window


def test_search_and_track_tables_keep_descriptive_columns_near_each_other() -> None:
    search = src("audioknigi/qt/mixins/search.py")
    book = src("audioknigi/qt/main_window_pages.py")
    for column in (1, 2, 3):
        assert f'search_header.setSectionResizeMode({column}, QHeaderView.ResizeMode.Stretch)' in search
    assert 'search_header.setStretchLastSection(False)' in search
    assert 'track_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)' in book
    assert 'track_header.setStretchLastSection(False)' in book


def test_help_center_uses_rich_text_headings_lists_and_keyboard_badges() -> None:
    help_source = src("audioknigi/qt/help_center.py")
    assert 'def _format_help_body_html' in help_source
    assert '<h2>{escaped_title}</h2>' in help_source
    assert '<kbd>' in help_source
    assert 'line-height: 1.42' in help_source
    assert 'self.text.setHtml(_format_help_body_html(title, body))' in help_source
    assert 'self.text.setPlainText(' not in help_source


def test_menu_bar_has_more_vertical_air_without_touching_search_progress_dialog() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert 'padding: 4px 6px 3px 6px;' in theme
    search_progress = src("audioknigi/qt/operation_dialog.py")
    assert 'BlockingOperationDialog' in search_progress
