from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_easy_search_table_uses_available_width_without_horizontal_scroll() -> None:
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert "card.setMaximumWidth(1180)" in source
    assert "easy_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)" in source
    assert 'if key in {"index", "availability", "variants", "source"}:' in source
    assert "easy_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)" in source
    assert "self.easy_search_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)" in source
    assert "self.easy_search_table.setTextElideMode(Qt.TextElideMode.ElideRight)" in source
    assert "self.easy_search_table.setWordWrap(True)" in source
    assert "self.easy_search_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)" in source
    assert "easy_header.setStretchLastSection(False)" in source


def test_easy_search_keeps_all_search_model_columns_visible() -> None:
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    block = source[source.index("self.easy_search_table = QTableView()"):source.index("easy_search_actions = QHBoxLayout()") ]
    assert ".setColumnHidden(" not in block
    assert "SearchResultsModel.COLUMNS" in block
