from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi import cover_fetch
from audioknigi.config.settings import AppSettings
from audioknigi.core import SiteStructureChanged
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import parse_book_html
from audioknigi.models import Book, Track
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.services.book_analysis_service import BookAnalysisService

ROOT = Path(__file__).resolve().parents[2]


def test_process_book_accepts_primitive_string_indices():
    class Harness(BookFlowMixin):
        def _process_book_once(self, book, active_selected, status_callback=None):
            return book, set(active_selected)
        def log(self, _text):
            pass

    book = Book(
        url="https://example.invalid/book",
        title="Demo",
        tracks=[
            Track(index=0, title="Prologue", file="x"),
            Track(index=1, title="Chapter", file="y"),
        ],
    )
    _book, selected = Harness()._process_book(book, ["0", "1"])
    assert selected == {0, 1}


def test_process_book_once_accepts_mapping_tracks_and_string_selection(monkeypatch):
    class Harness(BookFlowMixin):
        def _check_cancel(self):
            pass
        def _scan_book_files(self, *_args, **_kwargs):
            pass
        def _estimate_required_space(self, *_args, **_kwargs):
            return 0
        def _disk_free_for_path(self, *_args, **_kwargs):
            return 10**9
        def _book_folder(self, *_args, **_kwargs):
            return ROOT
        def set_status(self, *_args, **_kwargs):
            pass
        def set_progress(self, *_args, **_kwargs):
            pass
        def set_stage(self, *_args, **_kwargs):
            pass
        def log(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr("audioknigi.download.book_flow.resolve_executable", lambda _name: "/ffmpeg")
    # Stop immediately after selection normalization, before any real I/O.
    harness = Harness()
    harness._scan_book_files = lambda book, create_folder=False: (_ for _ in ()).throw(RuntimeError("selection-ok"))
    book = SimpleNamespace(tracks=[{"index": "0", "title": "P", "file": "x"}])
    with pytest.raises(RuntimeError, match="selection-ok"):
        harness._process_book_once(book, ["0"])


def test_expired_media_indices_accept_mapping_tracks():
    exc = MissingMediaSourceError("gone", source_url="https://cdn.invalid/a.mp3")
    book = SimpleNamespace(tracks=[
        {"index": "0", "file": "https://cdn.invalid/a.mp3", "fallback_file": ""},
        {"index": "1", "file": "https://cdn.invalid/b.mp3", "fallback_file": ""},
    ])
    assert BookFlowMixin._expired_media_track_indices(exc, book, {0, 1}) == [0]


def test_optional_metadata_does_not_erase_existing_title(monkeypatch):
    service = BookAnalysisService()
    monkeypatch.setattr(analysis_module, "extract_metadata_from_html", lambda _html, _title: ("", "", ""))
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/demo",
        html_text='<script>new Playerjs({title:"Recovered Title"})</script>',
        page_title="Fallback Title",
        playlist_url="https://audioknigi.com.ua/list.pl.txt",
        playlist_text='[{"file":"track.mp3","title":"One"}]',
    )
    assert book.title == "Recovered Title"


def test_playlist_object_wrapper_is_supported_and_wrong_object_shape_is_explicit(monkeypatch):
    service = BookAnalysisService()
    monkeypatch.setattr(analysis_module, "extract_metadata_from_html", lambda _html, title: (title, "", ""))
    kwargs = dict(
        url="https://audioknigi.com.ua/demo",
        html_text='<script>new Playerjs({title:"Demo"})</script>',
        page_title="Demo",
        playlist_url="https://audioknigi.com.ua/list.pl.txt",
    )
    book = service._parse_playlist_data(
        **kwargs,
        playlist_text='{"playlist":[{"file":"track.mp3","title":"One"}]}',
    )
    assert len(book.tracks) == 1
    with pytest.raises(SiteStructureChanged, match="ожидался список треков"):
        service._parse_playlist_data(**kwargs, playlist_text='{"error":"forbidden"}')


def test_knigavuhe_controller_uses_page_author_fallback():
    payload = {
        "book": {"name": "Demo", "authors": [], "readers": []},
        "playlist": [{"url": "https://cdn.invalid/1.mp3", "title": "One"}],
    }
    html = (
        '<html><head><title>Demo — автор Иван Автор</title></head><body>'
        '<script>BookController.enter(' + json.dumps(payload, ensure_ascii=False) + ');</script>'
        '</body></html>'
    )
    book = parse_book_html(html, "https://knigavuhe.org/book/demo/")
    assert book.author == "Иван Автор"


def test_download_engine_uses_retrying_unlink_for_manifest_and_full_source():
    source = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    manifest = source[source.index("def _remove_resume_manifest"):source.index("@staticmethod", source.index("def _remove_resume_manifest"))]
    assert "unlink_with_retry(path, missing_ok=True)" in manifest
    full = source[source.index("def run_full_mp3"):source.index("def run(self)")]
    assert "unlink_with_retry(source_target, missing_ok=True)" in full
    assert "source_target.unlink(missing_ok=True)" not in full


def test_cover_fetch_rejects_oversized_declared_length_before_streaming(monkeypatch):
    class Response:
        headers = {"content-length": str(cover_fetch._MAX_COVER_BYTES + 1), "content-type": "image/jpeg"}
        iterated = False
        def raise_for_status(self):
            pass
        def iter_content(self, chunk_size=0):
            self.iterated = True
            yield b"should-not-read"
        def close(self):
            pass

    response = Response()
    class Session:
        def get(self, *args, **kwargs):
            return response
    monkeypatch.setattr(cover_fetch, "get_http_session", lambda: Session())
    assert cover_fetch.fetch_cover_bytes("https://example.invalid/huge.jpg") is None
    assert response.iterated is False


def test_posix_file_redaction_avoids_arithmetic_false_positive_but_keeps_real_paths_private():
    assert _privacy_path("math: 10 / 2 / calc.py", collapse_whole_path=False) == "math: 10 / 2 / calc.py"
    assert _privacy_path("date: 2024 / 01 / file.mp3", collapse_whole_path=False) == "date: 2024 / 01 / file.mp3"
    assert _privacy_path("file /home/user/My Book/file.mp3 done", collapse_whole_path=False) == "file <configured-path> done"
    assert _privacy_path("path /secret", collapse_whole_path=False) == "path <configured-path>"


def test_search_accessibility_descriptions_are_localized():
    assert localize_runtime_text("en", "Введите название аудиокниги или автора, минимум три символа").startswith("Enter the audiobook")
    assert localize_runtime_text("de", "Поиск одновременно на трёх поддерживаемых сайтах").startswith("Gleichzeitige Suche")
    assert "варіантів озвучення" in localize_runtime_text(
        "uk", "Таблица с названием, автором, чтецом, количеством озвучек и источником"
    )


def test_reported_runtime_templates_and_settings_membership_are_intentional_contracts():
    assert ui_text("en", "Озвучка {index}", index=3) == "Narration 3"
    assert ui_text("en", "Найдено вариантов озвучки: {count}. Выберите чтеца.", count=2) == (
        "Narration options found: 2. Choose a narrator."
    )
    settings = AppSettings({"normalization_mode": "single", "auto_chunk_min_kbytes_per_sec": 512})
    assert settings["normalize_audio"] is True
    assert settings.get("auto_chunk_min_kbps") == 512
    assert "normalize_audio" not in settings
    assert "auto_chunk_min_kbps" not in settings


def test_reported_already_fixed_round78_items_remain_fixed():
    source = (ROOT / "audioknigi/knigavuhe.py").read_text(encoding="utf-8")
    grouping = source[source.index("grouped: dict"):source.index("unique: list", source.index("grouped: dict"))]
    assert "groups[key]" not in grouping
    assert "grouped[key]" in grouping
    speed = (ROOT / "audioknigi/qt/speed_graph.py").read_text(encoding="utf-8")
    assert "fontMetrics()" in speed and "label_baseline" in speed
