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


def test_focus_rings_are_refined_to_external_two_pixel_frame() -> None:
    theme = src("audioknigi/qt/theme.py")
    accessibility = src("audioknigi/qt/accessibility.py")
    assert 'focus = "#e5a93c"' in theme
    assert "QFocusFrame#keyboardFocusFrame" in theme
    assert "border: 2px solid {focus};" in theme
    assert "border-radius: 9px;" in theme
    assert "QFocusFrame" in accessibility
    assert "WA_TransparentForMouseEvents" in accessibility


def test_mode_switch_is_a_real_segmented_control_holder() -> None:
    theme = src("audioknigi/qt/theme.py")
    window = src("audioknigi/qt/main_window.py")
    assert 'QWidget#modeSegmentHolder' in theme
    assert 'mode_segment_holder.setObjectName("modeSegmentHolder")' in window
    assert 'mode_segment_layout.setContentsMargins(2, 2, 2, 2)' in window
    assert 'mode_segment_layout.setSpacing(0)' in window


def test_advanced_workspace_width_policy_is_explicit() -> None:
    window = src("audioknigi/qt/main_window.py")
    # Round 41 supersedes the Round 40 whole-tab 1500px cap: data tabs are
    # full width while Settings/Player center themselves internally.
    assert 'self.tabs.setMaximumWidth(16777215)' in window
    assert 'self.mode_stack.addWidget(self.tabs)' in window
    assert 'self.tabs.setMaximumWidth(1500)' not in window


def test_search_and_track_tables_keep_descriptive_columns_near_each_other() -> None:
    search = src("audioknigi/qt/mixins/search.py")
    book = src("audioknigi/qt/main_window_pages.py")
    assert 'search_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)' in search
    assert 'search_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)' in search
    assert 'search_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)' in search
    assert 'search_header.setStretchLastSection(False)' in search
    assert 'track_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)' in book
    assert 'track_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)' in book
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
    assert 'padding: 3px 6px 3px 10px;' in theme
    # Search progress dialog is intentionally outside this refinement round.
    search_progress = src("audioknigi/qt/operation_dialog.py")
    assert 'BlockingOperationDialog' in search_progress
