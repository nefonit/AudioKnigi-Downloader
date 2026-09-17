from __future__ import annotations

import threading
from pathlib import Path

import pytest

import audioknigi.downloader as downloader_module
import audioknigi.integrations as integrations
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.downloader import DownloaderMixin
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _BookCardParser, _extract_narration_variants, _fallback_script_book
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import _variant_from_dict

ROOT = Path(__file__).resolve().parents[1]


def source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _book() -> Book:
    return Book(
        url="https://knigavuhe.org/book/demo/",
        title="Demo Book",
        author="Author",
        tracks=[Track(index=1, title="Part 1", file="https://cdn.example/demo.mp3")],
    )


def test_full_mp3_default_track_template_uses_book_title(tmp_path):
    request = DownloadRequest(
        book=_book(), selected_indices=[1], output_dir=tmp_path,
        use_templates=True, folder_template="{Book_Title}", track_template="{Track_Number}.mp3",
    )
    engine = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())
    assert engine._full_mp3_target(request.book, tmp_path).name == "Demo Book.mp3"


def test_full_mp3_kept_source_is_visible_and_playable(monkeypatch, tmp_path):
    book = _book()
    request = DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path)
    engine = _DownloadEngine(
        request,
        {"delete_source": False, "embed_tags": False, "save_sidecars": False, "audio_preset": "64k_mono"},
        threading.Event(),
        DownloadCallbacks(),
    )
    engine._write_resume_manifest = lambda *_a, **_k: None
    engine._remove_resume_manifest = lambda *_a, **_k: None
    engine._add_history = lambda *_a, **_k: None
    engine._scan_audiobookshelf_after_book = lambda: None
    engine._save_book_sidecars = lambda *_a, **_k: None
    engine._disk_free_for_path = lambda *_a, **_k: 10**9
    engine._cached_probe_audio_info = lambda *_a, **_k: {"codec": "mp3", "bit_rate": 128000}
    engine._effective_mp3_profile = lambda *_a, **_k: (False, "64k", 1)
    engine._normalization_filter_for_track = lambda *_a, **_k: ""

    def fake_download(_url, _fallback, target, _referer):
        Path(target).write_bytes(b"source")

    def fake_ffmpeg(cmd):
        Path(cmd[-1]).write_bytes(b"encoded")

    engine._download_source_with_fallback = fake_download
    engine._run_ffmpeg = fake_ffmpeg
    monkeypatch.setattr("audioknigi.download_engine.resolve_executable", lambda _name: "ffmpeg")

    result = engine.run_full_mp3()
    retained = result.folder / "Demo Book (исходник).mp3"
    assert result.target_file and result.target_file.exists()
    assert retained.exists()
    assert not (result.folder / ".Demo Book.full-source").exists()


class _Limiter:
    def consume(self, *_args, **_kwargs):
        return None


class _Response:
    def __init__(self, status_code, headers, chunks=()):
        self.status_code = status_code
        self.headers = headers
        self._chunks = list(chunks)

    def __enter__(self): return self
    def __exit__(self, *_a): return False
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)
    def iter_content(self, **_kwargs):
        yield from self._chunks
    def close(self): return None


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class _SingleHost(DownloaderMixin):
    def __init__(self):
        self.cancel_event = threading.Event()
    def _get_bandwidth_limiter(self): return _Limiter()
    def _register_active_network_response(self, _response): return None
    def _unregister_active_network_response(self, _response): return None
    def set_progress(self, _value): return None
    def set_status(self, _value): return None
    def record_transfer_metrics(self, *_args): return None


@pytest.mark.parametrize("header", ["bytes 0-3/4", "/4", "bytes */4"])
def test_http_416_accepts_common_content_range_total_forms(monkeypatch, tmp_path, header):
    target = tmp_path / "chapter.mp3"
    part = tmp_path / "chapter.mp3.part"
    part.write_bytes(b"abcd")
    session = _Session([_Response(416, {"content-range": header})])
    monkeypatch.setattr(downloader_module, "get_http_session", lambda: session)
    result = _SingleHost()._download_single("https://example.invalid/a.mp3", target, "")
    assert result == target
    assert target.read_bytes() == b"abcd"
    assert len(session.calls) == 1


def test_loudnorm_normalizes_unbracketed_map_label():
    class Host(DownloaderMixin):
        def __init__(self): self.command = None
        def _run_ffmpeg_capture(self, cmd, timeout=None):
            self.command = list(cmd)
            return '{"input_i":"-20","input_lra":"2","input_tp":"-1","input_thresh":"-30","target_offset":"0"}'
    host = Host()
    host._measure_loudnorm(Path("source.mp3"), filter_complex="[0:a]anull[a0]", map_label="a0")
    graph = host.command[host.command.index("-filter_complex") + 1]
    assert ";[a0]loudnorm=" in graph


def test_knigavuhe_card_reads_author_and_reader_from_links_after_icons():
    parser = _BookCardParser()
    parser.feed(
        '<div class="bookitem">'
        '<div class="bookitem_name"><a class="is_black" href="/book/demo/">Название</a></div>'
        '<span class="icon_author"></span><a href="/author/ivan/">Иван Автор</a>'
        '<span class="icon_reader"></span><a href="/reader/petr/">Пётр Чтец</a>'
        '</div>'
    )
    assert len(parser.results) == 1
    assert parser.results[0].author == "Иван Автор"
    assert parser.results[0].narrator == "Пётр Чтец"


def test_knigavuhe_nested_heading_activates_narration_variants():
    variants = _extract_narration_variants(
        '<h2><span>Другие озвучки</span></h2><a href="/book/other/">Другой чтец</a>',
        "https://knigavuhe.org/book/main/", title="Книга", current_narrator="Первый",
    )
    assert any(item.url.endswith("/book/other/") for item in variants)


def test_knigavuhe_fallback_script_accepts_en_dash_author():
    book = _fallback_script_book(
        '<title>Книга – автор Иван Иванов</title><script>"https://cdn.example/1.mp3"</script>',
        "https://knigavuhe.org/book/demo/",
    )
    assert book is not None
    assert book.title == "Книга"
    assert book.author == "Иван Иванов"


def test_audiobookshelf_non_json_response_is_explained(monkeypatch):
    class Response:
        def raise_for_status(self): return None
        def json(self): raise ValueError("html instead of json")
    class Session:
        def get(self, *_a, **_k): return Response()
    monkeypatch.setattr(integrations, "get_http_session", lambda: Session())
    with pytest.raises(RuntimeError, match="не в формате JSON"):
        integrations.audiobookshelf_get_libraries("http://localhost:13378", "key")


def test_corrupt_queue_variant_without_url_is_tolerated():
    variant = _variant_from_dict({"title": "Broken row", "narrator": "Reader"})
    assert variant.url == ""


def test_runtime_messages_and_player_labels_are_localized():
    msg = (
        "Источник audioknigi.com.ua короче таймкодов плейлиста "
        "(01:20:00 вместо 02:00:00). Ищу исправную копию этой же озвучки на knigavuhe.org."
    )
    assert localize_runtime_text("en", msg).startswith("The audioknigi.com.ua source")
    assert localize_runtime_text("de", "Скачивание завершено. Пропущены недоступные части: 2, 5").startswith("Download abgeschlossen")
    assert localize_runtime_text("en", "Скачивание аудиокниги завершено.") == "Audiobook download completed."
    assert ui_text("en", "Аудиокнига") == "Audiobook"
    assert ui_text("de", "{count} глав(ы) • {folder}", count=3, folder="Buch") == "3 Kapitel • Buch"


def test_qt_and_pool_hardening_is_present_without_importing_qt():
    accessibility = source("audioknigi/qt/accessibility.py")
    assert "except ImportError" in accessibility
    assert "QAccessibleAnnouncementEvent is None" in accessibility
    player = source("audioknigi/qt/player_mixin.py")
    assert 'self._l("Автор: {value}", value=chosen.author)' in player
    analysis = source("audioknigi/services/book_analysis_service.py")
    assert "pool.shutdown(wait=False, cancel_futures=True)" in analysis
    assert "future.cancel()" in analysis


def test_cloudflare_doh_follows_cname_when_answer_has_no_address(monkeypatch):
    import json
    import urllib.parse
    import audioknigi.network_dns as dns

    class Response:
        status = 200
        def __init__(self, payload): self._payload = payload
        def read(self): return json.dumps(self._payload).encode("utf-8")

    class Connection:
        def __init__(self, _ip, timeout=None): self.path = ""
        def request(self, _method, path, headers=None): self.path = path
        def getresponse(self):
            name = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)["name"][0]
            if name == "alias.example":
                return Response({"Status": 0, "Answer": [{"type": 5, "TTL": 120, "data": "target.example."}]})
            return Response({"Status": 0, "Answer": [{"type": 1, "TTL": 60, "data": "203.0.113.9"}]})
        def close(self): return None

    monkeypatch.setattr(dns, "_BootstrapHTTPSConnection", Connection)
    addresses, ttl, _bootstrap = dns._query_cloudflare_json("alias.example", 1)
    assert addresses == ("203.0.113.9",)
    assert ttl == 60
