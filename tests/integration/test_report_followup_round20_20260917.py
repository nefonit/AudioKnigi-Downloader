from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


from audioknigi import knigavuhe, poleknig
from audioknigi.core import fmt_eta, parse_time_seconds
from audioknigi.download.probe import ProbeMixin
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, SearchResult
from audioknigi.providers import audioknigi_search as search_module
from audioknigi.services.queue_service import _parse_selected_indices_payload


ROOT = Path(__file__).resolve().parents[2]


def test_knigavuhe_call_argument_balances_parentheses_inside_object() -> None:
    source = 'BookController.enter({title: "Book", value: fn(1, nested(2)), rows: [x(3)]}, true);'
    argument = knigavuhe._extract_call_argument(source)
    assert argument.startswith('{title: "Book"')
    assert 'fn(1, nested(2))' in argument
    assert argument.endswith('}')


def test_eta_float_string_and_nonfinite_playlist_times_are_safe() -> None:
    assert fmt_eta("120.5") == "00:02:00"
    assert parse_time_seconds(float("inf")) is None
    assert parse_time_seconds("Infinity") is None
    assert parse_time_seconds("1e308:00") is None


def test_poleknig_symbol_only_titles_do_not_merge_by_author(monkeypatch) -> None:
    response = SimpleNamespace(text="", url="https://poleknig.com/search/")
    rows = [
        SearchResult(title="!!!", author="Толстой", narrator="A", url="https://poleknig.com/books/1", source="poleknig"),
        SearchResult(title="???", author="Толстой", narrator="B", url="https://poleknig.com/books/2", source="poleknig"),
    ]
    monkeypatch.setattr(poleknig, "_fetch_search_page", lambda *_a, **_k: response)
    monkeypatch.setattr(poleknig, "parse_search_results", lambda *_a, **_k: list(rows))
    monkeypatch.setattr(poleknig, "_search_last_page", lambda *_a, **_k: 1)
    monkeypatch.setattr(poleknig, "_hydrate_search_result_info", lambda item: (item, []))
    monkeypatch.setattr(poleknig, "_book_page_author_links", lambda *_a, **_k: [])
    monkeypatch.setattr(poleknig, "_expand_matching_author_catalogs", lambda *_a, **_k: [])
    results = poleknig.search("толстой")
    assert [item.url for item in results] == [rows[0].url, rows[1].url]


def test_poleknig_external_playlist_finds_variable_config_without_browser() -> None:
    html = '''<script>
    var player_cfg = {playlist: "/media/book-list.json"};
    var player = new Playerjs(player_cfg);
    </script>'''
    assert poleknig._external_playlist_url(html, "https://poleknig.com/books/123") == "https://poleknig.com/media/book-list.json"


def test_partial_download_sidecars_use_full_book_track_list_contract() -> None:
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert 'self._save_book_sidecars(book, folder, list(getattr(book, "tracks", None) or []))' in source
    assert 'self._save_book_sidecars(book, folder, chosen)' not in source


def test_probe_filename_accepts_mapping_track() -> None:
    class Dummy(ProbeMixin):
        runtime_use_templates = False
        runtime_naming_mode = "number_title"

    book = Book(url="https://example.invalid/book", title="Book", tracks=[])
    name = Dummy()._track_filename(book, {"index": "4", "title": "Chapter"})
    assert name == "04 - Chapter.mp3"


def test_dynamic_narration_label_is_runtime_localized() -> None:
    assert localize_runtime_text("en", "Озвучка 3") == "Recording 3"
    assert localize_runtime_text("de", "Озвучка 3") == "Sprecherfassung 3"
    assert localize_runtime_text("uk", "Озвучка 3") == "Озвучення 3"


def test_audioknigi_search_prefers_utf8_response_bytes(monkeypatch) -> None:
    captured = {}
    html = '<a href="/audio-1">Война и мир</a>'
    mojibake = html.encode("utf-8").decode("latin-1")

    class Response:
        url = "https://audioknigi.com.ua/search"
        content = html.encode("utf-8")
        text = mojibake
        def raise_for_status(self):
            return None

    class Session:
        def get(self, *_a, **_k):
            return Response()

    monkeypatch.setattr(search_module, "get_http_session", lambda: Session())

    def fake_parse(text, *_a, **_k):
        captured["text"] = text
        return []

    monkeypatch.setattr(search_module, "parse_audioknigi_results", fake_parse)
    search_module.search_audioknigi("война")
    assert captured["text"] == html


def test_queue_legacy_string_selected_indices_support_common_separators() -> None:
    assert _parse_selected_indices_payload("1, 2; 3  4") == [1, 2, 3, 4]
    assert _parse_selected_indices_payload("") is None
    assert _parse_selected_indices_payload([]) == []


def test_history_player_and_parallel_progress_contracts_are_stable() -> None:
    history = (ROOT / "audioknigi/qt/mixins/history.py").read_text(encoding="utf-8")
    listen = history.split("def history_listen", 1)[1].split("def history_open_folder", 1)[0]
    assert 'self.set_ui_mode("advanced", persist=False)' in listen

    flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert "self._suppress_source_transfer_ui = True" in flow
    assert "self.set_progress(pos * 100 / max(1, len(download_jobs)))" in flow

    network = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    assert network.count('_suppress_source_transfer_ui') >= 4
