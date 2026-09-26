from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle
from audioknigi.core import safe_int
from audioknigi.models import Book, SearchResult, Track
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.library_service import scan_unfinished


def test_support_log_multiline_path_does_not_collapse_whole_log(monkeypatch):
    monkeypatch.setattr(support_bundle.os, "name", "nt", raising=False)
    monkeypatch.setattr(support_bundle.Path, "home", classmethod(lambda cls: Path(r"C:\\Users\\Alice")))
    raw = b"D:\\Books\\broken.mp3\r\nsecond diagnostic line\r\n"
    cleaned = support_bundle._sanitize_log_bytes(raw).decode("utf-8")
    assert cleaned != "<configured-path>"
    assert "second diagnostic line" in cleaned
    assert "D:\\" not in cleaned


def test_privacy_path_keeps_sanitizing_when_home_lookup_fails(monkeypatch):
    monkeypatch.setattr(support_bundle.Path, "home", classmethod(lambda cls: (_ for _ in ()).throw(RuntimeError("no home"))))
    cleaned = support_bundle._privacy_path(r"error at D:\\Private\\book.mp3", collapse_whole_path=False)
    assert "D:\\Private" not in cleaned
    assert "<configured-path>" in cleaned


def test_privacy_path_masks_drive_root_and_trailing_slash():
    root_only = support_bundle._privacy_path(r"free on D:\\ 20 GB", collapse_whole_path=False)
    trailing = support_bundle._privacy_path(r"folder D:\\Downloads\\", collapse_whole_path=False)
    assert "D:\\" not in root_only
    assert "D:\\Downloads" not in trailing


def test_appsettings_partial_mapping_has_consistent_keys_length_and_delete():
    settings = settings_module.AppSettings({"scale": 120, "plugin_key": "x"})
    assert settings["language"] == settings_module.DEFAULT_SETTINGS["language"]
    assert "language" in settings.keys()
    assert len(settings) == len(settings.to_dict())
    assert settings.to_dict()["plugin_key"] == "x"
    del settings["language"]
    assert "language" not in settings
    try:
        settings["language"]
    except KeyError:
        pass
    else:
        raise AssertionError("deleted mapping key unexpectedly resurrected from defaults")


def test_legacy_only_settings_mark_profile_as_first_run_complete():
    data, _changed = settings_module.migrate_settings({"auto_chunk_min_kbps": 512})
    assert data["first_run_complete"] is True
    data2, _changed2 = settings_module.migrate_settings({"normalize_audio": True})
    assert data2["first_run_complete"] is True


def test_probe_space_estimator_accepts_string_track_indices(tmp_path):
    from audioknigi.download.probe import ProbeMixin

    class Probe(ProbeMixin):
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"
        runtime_delete_source = True
        def _book_folder(self, _book, create=False):
            return tmp_path
        def _source_target_assignments(self, _book, source_urls, folder):
            return [(index, url, Path(folder) / f"source-{index}.mp3") for index, url in enumerate(source_urls)]

    track = Track(index=1, title="x", file="https://example/x.mp3", local_status="missing", duration=10)
    track.index = "1"  # simulate a legacy/external parser payload
    book = Book(url="https://example/book", title="book", tracks=[track], remote_size=1_000_000)
    assert Probe()._estimate_required_space(book, [1]) > 0


def test_audioknigi_inferred_card_author_yields_to_structured_page_author():
    html = "<html><title>Гарри Поттер и Философский камень</title></html>"
    source = SearchResult(
        title="Философский камень",
        author="Гарри Поттер",
        author_inferred=True,
        url="https://audioknigi.com.ua/audio-1",
        source="audioknigi.com.ua",
    )

    class Response:
        content = html.encode("utf-8")
        text = html
        def raise_for_status(self):
            return None
    class Session:
        def get(self, *args, **kwargs):
            return Response()

    result = audioknigi_search._audioknigi_page_metadata(
        source,
        session_factory=Session,
        metadata_extractor=lambda _html, _fallback: ("Гарри Поттер и Философский камень", "Джоан Роулинг", ""),
        extended_metadata_extractor=lambda _html: ("", "", "", ""),
    )
    assert result.author == "Джоан Роулинг"
    assert result.title == "Гарри Поттер и Философский камень"


def test_audioknigi_plain_narrator_is_reused_by_direct_analysis():
    html = "<div>Описание: текст книги. Читает: Иван Иванов Жанр: Фантастика</div>"
    assert audioknigi_search._audioknigi_plain_narrator(html) == "Иван Иванов"


def test_direct_analysis_strips_all_coauthor_prefixes_and_plain_narrator():
    service = BookAnalysisService()
    html = "<html><body>Читает: Иван Иванов Жанр: Фантастика</body></html>"
    playlist = json.dumps([{"file": "https://example.test/1.mp3", "title": "1"}])
    # Exercise the parser with controlled generic metadata so only the Round 47
    # fallback/cleanup logic is under test.
    import audioknigi.services.book_analysis_service as module
    old_meta = module.extract_metadata_from_html
    old_ext = module.extract_extended_metadata_from_html
    try:
        module.extract_metadata_from_html = lambda _html, _title: (
            "Андрей Уланов, Владимир Серебряков - Название",
            "Андрей Уланов, Владимир Серебряков",
            "",
        )
        module.extract_extended_metadata_from_html = lambda _html: ("", "", "", "")
        book = service._parse_playlist_data(
            url="https://audioknigi.com.ua/audio-1",
            html_text=html,
            page_title="Название",
            playlist_url="https://example.test/list.json",
            playlist_text=playlist,
        )
    finally:
        module.extract_metadata_from_html = old_meta
        module.extract_extended_metadata_from_html = old_ext
    assert book.title == "Название"
    assert book.narrator == "Иван Иванов"


def test_scan_unfinished_accepts_string_all_selection(tmp_path):
    folder = tmp_path / "book"
    folder.mkdir()
    (folder / "resume.json").write_text(json.dumps({
        "url": "https://audioknigi.com.ua/audio-1",
        "title": "Book",
        "selected_indices": "all",
    }), encoding="utf-8")
    rows = scan_unfinished(tmp_path)
    assert len(rows) == 1
    assert rows[0].selected_indices is None


def test_safe_int_accepts_integer_like_decimal_but_not_fractional():
    assert safe_int("12.0", 7) == 12
    assert safe_int("12.5", 7) == 7


def test_localized_context_menu_delete_slot_accepts_triggered_bool():
    source = (Path(__file__).resolve().parents[2] / "audioknigi/qt/localized_context_menu.py").read_text(encoding="utf-8")
    assert "delete_action.triggered.connect(lambda *_: _delete_selection(widget))" in source
