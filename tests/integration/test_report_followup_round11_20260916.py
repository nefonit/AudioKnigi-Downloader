from __future__ import annotations

import json
from pathlib import Path

from audioknigi.core import _first_json_ld
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.library_service import scan_unfinished

ROOT = Path(__file__).resolve().parents[2]


def test_scan_unfinished_accepts_scalar_selected_index_without_crashing(tmp_path):
    folder = tmp_path / "Book"
    folder.mkdir()
    (folder / "resume.json").write_text(
        json.dumps(
            {
                "url": "https://knigavuhe.org/book/1",
                "title": "Book",
                "selected_indices": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rows = scan_unfinished(tmp_path)
    assert len(rows) == 1
    assert rows[0].selected_indices == [1]


def test_scan_unfinished_ignores_boolean_selected_payload(tmp_path):
    folder = tmp_path / "Book"
    folder.mkdir()
    (folder / "resume.json").write_text(
        json.dumps(
            {
                "url": "https://knigavuhe.org/book/1",
                "title": "Book",
                "selected_indices": False,
            }
        ),
        encoding="utf-8",
    )
    assert scan_unfinished(tmp_path) == []


def test_playlist_track_title_decodes_html_entities():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/demo",
        html_text="<title>Demo</title>",
        page_title="Demo",
        playlist_url="https://audioknigi.com.ua/demo.pl.txt",
        playlist_text=json.dumps(
            [{"file": "1.mp3", "title": "&quot;Глава 1&quot; &amp; 2"}],
            ensure_ascii=False,
        ),
    )
    assert book.tracks[0].title == '"Глава 1" & 2'


def test_json_ld_parses_before_unescaping_entities():
    html = (
        '<script type="application/ld+json">'
        '{"@type":"Book","name":"A &quot;quoted&quot; &amp; safe"}'
        "</script>"
    )
    items = _first_json_ld(html)
    assert items == [{"@type": "Book", "name": 'A "quoted" & safe'}]


def test_round11_network_peer_abort_contract_present():
    source = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    assert "peer_abort_event=None" in source
    assert "peer_abort_event = threading.Event()" in source
    assert "peer_abort_event=peer_abort_event" in source
    assert "peer_abort_event.set()" in source
    assert "if peer_aborted():" in source


def test_round11_skip_preserves_completed_sources_and_split_cancels_pending():
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    marker = 'if action == "skip" and available_after_skip:'
    first = source.index(marker)
    window = source[first : first + 900]
    assert "_clear_stale_source_downloads(book)" not in window
    assert "Keep already completed fresh source downloads" in window
    assert source.count("pending.cancel()") >= 4


def test_round11_clipboard_guards_is_file_inside_try():
    source = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    block = source[source.index('if path.suffix.lower() == ".url":') : source.index("if value and value not in out:")]
    assert "try:" in block
    assert "if not path.is_file():" in block
    assert "except (OSError, ValueError):" in block


def test_help_text_uses_same_labels_as_visible_actions():
    messages = json.loads((ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8"))
    assert "Fürs Smartphone" in messages["de"]["help_quality_body"]
    assert "Buch suchen oder Link öffnen" in messages["de"]["help_search_body"]
    assert "Find a book or open a link" in messages["en"]["help_search_body"]
    assert "Найти книгу или открыть ссылку" in messages["ru"]["help_search_body"]
    assert "Знайти книгу або відкрити посилання" in messages["uk"]["help_search_body"]
