from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QSplitter, QTextBrowser, QVBoxLayout,
)

from ..i18n import tr, ui_text
from .accessibility import configure_accessible


from .help_content import (
    TOPICS,
    ROUND55_TOPIC_DETAILS_RU,
    ROUND55_TOPIC_DETAILS_EN,
    ROUND55_TOPIC_DETAILS_DE,
    ROUND55_TOPIC_DETAILS_UK,
    ROUND55_TOPIC_DETAILS,
)

# Stable private import for callers using the original Help Center module.
from .help_formatter import _format_help_body_html
from .help_actions import resolve_help_topic


class QtHelpCenter(QDialog):
    def __init__(self, parent=None, *, language="ru", topic="start", copy_report_callback=None):
        super().__init__(parent)
        self.language = str(language or "ru")
        if self.language not in TOPICS:
            self.language = "ru"
        self.copy_report_callback = copy_report_callback
        self.setWindowTitle(tr(self.language, "help_center"))
        self.resize(1020, 700)
        self.setMinimumSize(760, 520)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        configure_accessible(self, name=tr(self.language, "help_center"), identifier="help_center")
        outer = QVBoxLayout(self)
        intro = QLabel(tr(self.language, "help_short_intro"))
        outer.addWidget(intro)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        self.topics = QListWidget()
        self.topics.setWordWrap(True)
        self.topics.setSpacing(4)
        self.topics.setMinimumWidth(240)
        self.topics.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        configure_accessible(self.topics, name=ui_text(self.language, "Темы справки"), identifier="help_topics")
        self.text = QTextBrowser()
        self.text.setOpenExternalLinks(True)
        self.text.setStyleSheet("QTextBrowser { padding: 12px; }")
        configure_accessible(self.text, name=tr(self.language, "help_text_accessible"), identifier="help_text")
        self._topic_data = list(TOPICS[self.language])
        topic_row_height = max(42, self.topics.fontMetrics().height() * 2 + 12)
        for key, title, _body in self._topic_data:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setSizeHint(QSize(0, topic_row_height))
            self.topics.addItem(item)
        self.topics.currentRowChanged.connect(self._show_row)
        splitter.addWidget(self.topics)
        splitter.addWidget(self.text)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 700])
        outer.addWidget(splitter, 1)
        row = QHBoxLayout()
        copy_btn = QPushButton(tr(self.language, "copy_error_report"))
        configure_accessible(copy_btn, name=tr(self.language, "copy_error_report"), identifier="help_copy_crash_report")
        copy_btn.clicked.connect(self._copy_report)
        close_btn = QPushButton(tr(self.language, "close"))
        configure_accessible(close_btn, name=tr(self.language, "close"), identifier="help_close")
        close_btn.clicked.connect(self.accept)
        row.addWidget(copy_btn)
        row.addStretch(1)
        row.addWidget(close_btn)
        outer.addLayout(row)
        target = next((i for i, x in enumerate(self._topic_data) if x[0] == topic), 0)
        self.topics.setCurrentRow(target)
        self.topics.setFocus()

    def _show_row(self, row: int):
        selected = resolve_help_topic(self.language, self._topic_data, row)
        if selected is None:
            return
        title, body = selected
        self.text.setHtml(_format_help_body_html(title, body))

    def _copy_report(self):
        if callable(self.copy_report_callback):
            self.copy_report_callback()


# Backward-compatible export used by older audit/tests.
TOPICS_RU = TOPICS["ru"]
__all__ = ["QtHelpCenter", "TOPICS", "TOPICS_RU"]
