from __future__ import annotations

import threading
from pathlib import Path

import pytest

from audioknigi import downloader
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _hydrate_search_result_titles, parse_book_html
from audioknigi.models import Book, SearchResult, Track
from audioknigi.poleknig import _canonical_book_url, _query_matches_metadata as pole_query_matches
from audioknigi.services.download_request import DownloadRequest


ROOT = Path(__file__).resolve().parents[1]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class _Limiter:
    def consume(self, *_args, **_kwargs):
        return None


class _Response416:
    status_code = 416
    headers = {"content-range": "bytes */4"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        raise AssertionError("a complete .part must not call raise_for_status for 416")

    def iter_content(self, **_kwargs):
        raise AssertionError("a complete .part must not read the body")


class _Session416:
    def get(self, *_args, **_kwargs):
        return _Response416()


class _SingleDownloadHarness(downloader.DownloaderMixin):
    def __init__(self):
        self.cancel_event = threading.Event()
        self.progress = []

    def _check_cancel(self):
        return None

    def _get_bandwidth_limiter(self):
        return _Limiter()

    def _register_active_network_response(self, _response):
        return None

    def _unregister_active_network_response(self, _response):
        return None

    def set_progress(self, value):
        self.progress.append(value)

    def set_status(self, _text):
        return None

    def record_transfer_metrics(self, *_args):
        return None


def _request(tmp_path: Path, *, preset="copy", normalization="off") -> DownloadRequest:
    book = Book(
        url="https://example.test/book",
        title="Book",
        tracks=[Track(index=1, title="Chapter", file="https://example.test/audio.mp3")],
    )
    return DownloadRequest(
        book=book,
        selected_indices=[1],
        output_dir=tmp_path,
        audio_preset=preset,
        normalization_mode=normalization,
    )


def test_single_download_promotes_complete_part_after_http_416(monkeypatch, tmp_path):
    target = tmp_path / "book.mp3"
    part = target.with_suffix(".mp3.part")
    part.write_bytes(b"done")
    monkeypatch.setattr(downloader, "get_http_session", lambda: _Session416())

    harness = _SingleDownloadHarness()
    result = harness._download_single("https://example.test/audio.mp3", target, "https://example.test/book")

    assert result == target
    assert target.read_bytes() == b"done"
    assert not part.exists()
    assert 100 in harness.progress


def test_full_mp3_honors_audio_preset_and_normalization(monkeypatch, tmp_path):
    import audioknigi.download_engine as engine_module

    engine = _DownloadEngine(
        _request(tmp_path, preset="64k_mono", normalization="single"),
        {"embed_tags": False, "save_sidecars": False},
        threading.Event(),
        DownloadCallbacks(),
    )
    commands = []

    def fake_download(_url, target, _referer):
        Path(target).write_bytes(b"x" * 100_000)
        return Path(target)

    def fake_ffmpeg(cmd):
        commands.append(list(cmd))
        Path(cmd[-1]).write_bytes(b"mp3")

    monkeypatch.setattr(engine, "_download_with_resume", fake_download)
    monkeypatch.setattr(engine, "_cached_probe_audio_info", lambda _path: {"codec": "mp3", "bit_rate": 128_000, "channels": 2})
    monkeypatch.setattr(engine, "_run_ffmpeg", fake_ffmpeg)
    monkeypatch.setattr(engine, "_disk_free_for_path", lambda _path: 10**9)
    monkeypatch.setattr(engine, "_save_book_sidecars", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(engine, "_scan_audiobookshelf_after_book", lambda: None)
    monkeypatch.setattr(engine, "_add_history", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(engine_module, "resolve_executable", lambda name: "/fake/ffmpeg" if name == "ffmpeg" else None)

    result = engine.run_full_mp3()
    assert result.target_file is not None and result.target_file.exists()
    assert len(commands) == 1
    cmd = commands[0]
    assert "-af" in cmd and any("loudnorm=" in value for value in cmd)
    assert cmd[cmd.index("-b:a") + 1] == "64k"
    assert cmd[cmd.index("-ac") + 1] == "1"


def test_remove_resume_manifest_does_not_create_book_folder(tmp_path):
    output = tmp_path / "not-created"
    engine = _DownloadEngine(_request(output), {}, threading.Event(), DownloadCallbacks())
    expected_folder = output / "Book"
    assert not expected_folder.exists()
    engine._remove_resume_manifest(engine.request.book)
    assert not expected_folder.exists()


def test_proxy_uses_system_resolver_for_local_single_label(monkeypatch):
    import audioknigi.network_dns as dns

    marker = object()
    calls = []

    def fake_create_connection(address, timeout=None, **_kwargs):
        calls.append((address, timeout))
        return marker

    monkeypatch.setattr(dns, "_ORIGINAL_CREATE_CONNECTION", fake_create_connection)
    monkeypatch.setattr(dns, "_resolve", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("DoH must be bypassed")))
    assert dns._connect_target("nas", 13378, timeout=3.0) is marker
    assert calls == [(('nas', 13378), 3.0)]


def test_knigavuhe_playlist_uses_embedded_duration_without_probe():
    html = '''<script>BookController.enter({"book":{"name":"Demo"},"playlist":[{"title":"Глава 1","url":"https://u.example/1.mp3","duration":"01:02.5"}]});</script>'''
    book = parse_book_html(html, "https://knigavuhe.org/book/demo/")
    assert len(book.tracks) == 1
    assert book.tracks[0].duration == pytest.approx(62.5)


def test_knigavuhe_hydration_preserves_site_matches_from_description_or_genre():
    item = SearchResult(
        title="Совсем другое название",
        url="https://knigavuhe.org/book/demo/",
        source="knigavuhe.org",
        author="Автор",
        narrator="Чтец",
    )
    assert _hydrate_search_result_titles([item], query="фантастика") == [item]


def test_poleknig_query_matching_includes_narrator_and_read_urls():
    assert pole_query_matches("Клюквин", "Книга", "Автор", "Александр Клюквин")
    assert _canonical_book_url("https://poleknig.com/", "/books/12345-demo/read") == "https://poleknig.com/books/12345"


def test_contextual_missing_file_status_does_not_collide_with_logical_no():
    assert ui_text("uk", "нет (файл)") == "немає"
    assert ui_text("de", "нет (файл)") == "fehlt"
    assert ui_text("en", "нет (файл)") == "missing"
    assert ui_text("uk", "нет") == "ні"
    assert ui_text("de", "нет") == "nein"
    assert ui_text("en", "нет") == "no"


def test_player_loaded_message_is_runtime_localized():
    assert localize_runtime_text("uk", "Файл загружен: 01.mp3") == "Файл завантажено: 01.mp3"
    assert localize_runtime_text("de", "Файл загружен: 01.mp3") == "Datei geladen: 01.mp3"
    assert localize_runtime_text("en", "Файл загружен: 01.mp3") == "File loaded: 01.mp3"


def test_drag_drop_deduplicates_url_and_text_mime_flavors():
    source = text("audioknigi/qt/workers.py")
    body = source[source.index("def dropEvent"):source.index("__all__")]
    assert "if not values and mime.hasText():" in body
    assert "list(dict.fromkeys" in body


def test_player_chapter_switch_uses_normalized_path_identity():
    source = text("audioknigi/qt/player_mixin.py")
    body = source[source.index("def _player_path_identity"):source.index("def media_play_pause")]
    assert "value.replace" in body
    assert 'value.casefold() if os.name == "nt" else value' in body
    assert "files.index(self.player_controller.current_path)" not in body


def test_external_playlists_are_decoded_as_utf8_bytes():
    downloader_source = text("audioknigi/downloader.py")
    pole_source = text("audioknigi/poleknig.py")
    assert downloader_source.count('content.decode("utf-8", errors="replace")') >= 2
    assert 'playlist_response.content.decode("utf-8", errors="replace")' in pole_source
