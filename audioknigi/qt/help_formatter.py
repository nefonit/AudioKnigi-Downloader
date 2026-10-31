from __future__ import annotations

"""Qt-independent rendering for Help Center topics.

The rendered markup and keyboard-shortcut highlighting must remain stable
for existing users and screen readers. No QWidget or GUI code belongs here.
"""

import html as html_lib
import re


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

