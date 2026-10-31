from __future__ import annotations

import html as html_lib
import re

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

def _format_help_body_html(title: str, body: str) -> str:
    """Render plain help topics as readable rich text without changing content."""
    escaped_title = html_lib.escape(str(title or ""))
    raw_lines = str(body or "").splitlines()

    def inline(value: str) -> str:
        text = html_lib.escape(value)
        shortcut = re.compile(
            r"(?<![\w+])(?:(?:Ctrl|Strg)(?:\+(?:Shift|Umschalt)|\+Alt)?\+[A-Za-z0-9…]+|"
            r"(?:Ctrl|Strg)\+(?:Shift|Umschalt)\+Tab|(?:Ctrl|Strg)\+Tab|"
            r"(?:Shift|Umschalt)\+F\d+|Alt\+↓|F\d+|Enter|Space|Leertaste|Пробел|Пробіл|Esc)(?![\w+])",
            re.I,
        )
        return shortcut.sub(lambda match: f"<kbd>{match.group(0)}</kbd>", text)

    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_kind = "ul"
    list_start = 1

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append("<p>" + "<br>".join(inline(line) for line in paragraph) + "</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            start_attr = f' start="{list_start}"' if list_kind == "ol" and list_start != 1 else ""
            blocks.append(f"<{list_kind}{start_attr}>" + "".join(f"<li>{inline(item)}</li>" for item in list_items) + f"</{list_kind}>")
            list_items = []

    for raw in raw_lines:
        line = raw.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        bullet = re.match(r"^[•▪-]\s*(.+)$", line)
        numbered = re.match(r"^\d+[.)]\s*(.+)$", line)
        if bullet or numbered:
            flush_paragraph()
            new_kind = "ol" if numbered else "ul"
            if list_items and new_kind != list_kind:
                flush_list()
            if not list_items:
                list_kind = new_kind
                list_start = int(re.match(r"^(\d+)", line).group(1)) if numbered else 1
            list_items.append((bullet or numbered).group(1))
        else:
            flush_list()
            paragraph.append(line)
    flush_paragraph()
    flush_list()

    return f"""
    <html><head><style>
      body {{ font-family: 'Segoe UI'; font-size: 10.5pt; line-height: 1.42; }}
      h2 {{ color: #4fa3ff; font-size: 15pt; margin: 0 0 12px 0; }}
      p {{ margin: 0 0 12px 0; }}
      ul, ol {{ margin-top: 4px; margin-bottom: 12px; padding-left: 22px; }}
      li {{ margin: 4px 0; }}
      kbd {{ background: #303640; border: 1px solid #596273; border-radius: 4px;
             padding: 1px 5px; color: #f3f6fa; font-family: 'Segoe UI'; font-weight: 600; }}
    </style></head><body><h2>{escaped_title}</h2>{''.join(blocks)}</body></html>
    """


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
        if not 0 <= row < len(self._topic_data):
            return
        key, title, body = self._topic_data[row]
        detail = ROUND55_TOPIC_DETAILS.get(self.language, {}).get(key, "")
        if detail:
            body = body.rstrip() + "\n\n" + detail
        self.text.setHtml(_format_help_body_html(title, body))

    def _copy_report(self):
        if callable(self.copy_report_callback):
            self.copy_report_callback()


# Backward-compatible export used by older audit/tests.
TOPICS_RU = TOPICS["ru"]
__all__ = ["QtHelpCenter", "TOPICS", "TOPICS_RU"]
