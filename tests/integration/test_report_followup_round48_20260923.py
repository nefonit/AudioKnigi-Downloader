from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_advanced_book_table_keeps_stable_column_policy_after_analysis() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    assert "track_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)" in pages
    assert "track_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)" in pages
    assert "self.track_table.setColumnWidth(7, 280)" in pages
    assert "self.track_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)" in pages
    assert "self.track_table.setMinimumWidth(0)" in pages
    assert "self.track_table.resizeColumnsToContents()" not in analysis


def test_advanced_book_description_is_bounded_scrollable_text() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    assert "self.book_description = QTextEdit()" in pages
    assert "self.book_description.setReadOnly(True)" in pages
    assert "self.book_description.setTabChangesFocus(True)" in pages
    assert "self.book_description.setMaximumHeight(86)" in pages
    assert "self.book_summary.setMaximumHeight(58)" in pages


def test_advanced_book_details_are_a_compact_stateful_card() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    window = src("audioknigi/qt/main_window.py")
    assert 'self.book_details_panel.setObjectName("bookCard")' in pages
    assert "self.book_details_panel.setVisible(False)" in pages
    assert "self.book_details_panel.setVisible(True)" in analysis
    assert "self.book_details_panel.setVisible(False)" in window
    assert "self.book_cover_label.setFixedSize(108, 108)" in pages


def test_advanced_narration_combo_does_not_grow_window_from_long_reader_names() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    assert "QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon" in pages
    assert "self.narration_combo.setMinimumContentsLength(22)" in pages
    assert "self.narration_row_widget.setVisible(False)" in pages
    assert "self.narration_row_widget.setVisible(visible)" in analysis


def test_advanced_result_controls_and_table_only_consume_space_for_real_book() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    window = src("audioknigi/qt/main_window.py")
    assert "self.track_controls_panel.setVisible(False)" in pages
    assert "self.track_table.setVisible(False)" in pages
    assert "self.track_controls_panel.setVisible(enabled)" in analysis
    assert "self.track_table.setVisible(enabled)" in analysis
    assert "self.track_controls_panel.setVisible(False)" in window
    assert "self.track_table.setVisible(False)" in window


def test_advanced_progress_panels_only_take_layout_space_while_active() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    assert "self.analysis_progress.setVisible(False)" in pages
    assert "self.analysis_progress.setVisible(True)" in analysis
    assert "self.download_activity_panel.setVisible(False)" in pages
    assert "self.download_activity_panel.setVisible(True)" in analysis
    assert "self.download_activity_panel.setVisible(False)" in analysis
