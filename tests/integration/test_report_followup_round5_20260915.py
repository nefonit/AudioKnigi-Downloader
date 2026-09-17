from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from audioknigi.brand import version_label
from audioknigi.core import Cancelled
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.download_request import DownloadRequest

ROOT = Path(__file__).resolve().parents[2]


def test_version_label_does_not_return_bare_v_for_empty_value():
    assert version_label("") == ""
    assert version_label("  ") == ""
    assert version_label(None) == ""
    assert version_label("4.12.42") == "v4.12.42"
    assert version_label("v4.12.42") == "v4.12.42"


def test_knigavuhe_variant_enrichment_propagates_cancelled(monkeypatch):
    import audioknigi.knigavuhe as module

    result = SearchResult(title="Demo", url="https://knigavuhe.org/book/demo/", source="knigavuhe.org")

    def cancelled(_item):
        raise Cancelled("cancel")

    monkeypatch.setattr(module, "_enrich_search_result_variants", cancelled)
    with pytest.raises(Cancelled):
        module.enrich_search_variants([result])


def test_knigavuhe_search_hydration_marks_restricted_book(monkeypatch):
    import audioknigi.knigavuhe as module

    result = SearchResult(title="Fallback", url="https://knigavuhe.org/book/demo/", source="knigavuhe.org")

    class Response:
        text = (
            "<title>Demo — автор Author, читает Reader</title>"
            "<p>Доступ к аудиокниге ограничен по просьбе правообладателя</p>"
        )
        def raise_for_status(self):
            pass

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(module, "get_http_session", Session)
    hydrated = module._resolve_search_result_title(result)
    assert hydrated.title == "Demo"
    assert hydrated.availability == "restricted"


def test_probe_audio_info_uses_container_bitrate_when_stream_bitrate_is_na(monkeypatch, tmp_path):
    import audioknigi.download.media as module

    payload = json.dumps({
        "streams": [{"codec_name": "mp3", "bit_rate": "N/A", "sample_rate": "44100", "channels": 2}],
        "format": {"bit_rate": "128000"},
    })

    class FakeProc:
        returncode = 0
        stdin = stdout = stderr = None
        def communicate(self, timeout=None):
            return payload, ""
        def poll(self):
            return 0
        def kill(self):
            pass

    class Dummy(MediaProcessingMixin):
        cancel_event = threading.Event()
        def _check_cancel(self):
            pass
        def _register_active_subprocess(self, proc):
            pass
        def _unregister_active_subprocess(self, proc):
            pass

    seen = {}
    monkeypatch.setattr(module, "resolve_executable", lambda _name: "ffprobe")
    def fake_popen(cmd, **kwargs):
        seen["cmd"] = cmd
        return FakeProc()
    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)

    info = Dummy()._probe_audio_info(tmp_path / "demo.mp3")
    assert info["bit_rate"] == 128000
    assert "stream=codec_name,bit_rate,sample_rate,channels:format=bit_rate" in seen["cmd"]


def test_book_analysis_accepts_utf8_bom_playlist():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    playlist = "\ufeff" + json.dumps([{"file": "1.mp3", "title": "One"}])
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/book/1",
        html_text="<title>Demo</title>",
        page_title="Demo",
        playlist_url="https://cdn.example/demo.pl.txt",
        playlist_text=playlist,
    )
    assert [track.index for track in book.tracks] == [1]


def test_full_mp3_copy_mode_retains_source_when_delete_source_is_false(monkeypatch, tmp_path):
    book = Book(
        url="https://audioknigi.com.ua/book/1",
        title="Demo",
        tracks=[Track(index=1, title="One", file="https://cdn.example/demo.mp3")],
        remote_size=4,
    )
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    engine = _DownloadEngine(
        request,
        {"delete_source": False, "embed_tags": False, "save_sidecars": False, "audio_preset": "copy"},
        threading.Event(),
        DownloadCallbacks(),
    )
    monkeypatch.setattr(engine, "_write_resume_manifest", lambda *a, **k: None)
    monkeypatch.setattr(engine, "_book_folder", lambda _book, create=True: tmp_path)
    monkeypatch.setattr(engine, "_full_mp3_target", lambda _book, _folder: tmp_path / "Demo.mp3")
    monkeypatch.setattr(engine, "_disk_free_for_path", lambda _path: 10**9)
    monkeypatch.setattr(engine, "set_stage", lambda *a, **k: None)
    monkeypatch.setattr(engine, "set_status", lambda *a, **k: None)
    monkeypatch.setattr(engine, "set_progress", lambda *a, **k: None)
    monkeypatch.setattr(engine, "_download_source_with_fallback", lambda _url, _fallback, target, _referer: Path(target).write_bytes(b"mp3data"))
    monkeypatch.setattr(engine, "_cached_probe_audio_info", lambda _path: {"codec": "mp3", "bit_rate": 128000})
    monkeypatch.setattr(engine, "_effective_mp3_profile", lambda _path: (True, None, None))
    monkeypatch.setattr(engine, "_save_book_sidecars", lambda *a, **k: None)
    monkeypatch.setattr(engine, "_scan_audiobookshelf_after_book", lambda *a, **k: None)
    monkeypatch.setattr(engine, "_add_history", lambda *a, **k: None)
    monkeypatch.setattr(engine, "_remove_resume_manifest", lambda *a, **k: None)

    result = engine.run_full_mp3()
    assert result.target_file == tmp_path / "Demo.mp3"
    assert (tmp_path / "Demo.mp3").read_bytes() == b"mp3data"
    assert (tmp_path / "Demo (исходник).mp3").read_bytes() == b"mp3data"


def test_round5_static_hardening_contracts_are_present():
    book_flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert 'getattr(self, "runtime_delete_source", True)' in book_flow
    assert 'getattr(self, "runtime_delete_source", False)' not in book_flow

    network = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    report_block = network[network.index("def report(delta, force=False):"):network.index("jobs = queue.Queue()")]
    assert "with progress_lock:" in report_block
    assert "last_target[0] = target_workers" in report_block

    probe = (ROOT / "audioknigi/download/probe.py").read_text(encoding="utf-8")
    assert '"packet=pts_time,dts_time"' in probe

    queue_ui = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    assert "def _same_supported_url" in queue_ui
    assert "normalize_supported_url" in queue_ui
    assert 'task.url.rstrip("/") == url.rstrip("/")' not in queue_ui

    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert "pending_url = normalize_supported_url" in analysis
    assert "force_redownload" in analysis

    main_window = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    easy = main_window[main_window.index("def easy_add_another_book"):main_window.index("def _play_event_sound")]
    assert "self.book_url_edit.clear()" in easy

    prefixes = json.loads((ROOT / "audioknigi/locales/runtime_prefixes.json").read_text(encoding="utf-8"))
    assert "Обрабатываю полный файл" not in prefixes


def test_accessibility_descriptions_are_localized():
    cases = [
        ("Введите название/автора для поиска или вставьте ссылку на поддерживаемый сайт", "Enter a title/author"),
        ("Найти resume.json, повторно проанализировать книгу и восстановить выбранные части", "Find resume.json"),
        ("Получить сведения о книге и список доступных частей", "Get book information"),
        ("Применится после перезапуска", "Applies after restart"),
    ]
    for source, prefix in cases:
        translated = localize_runtime_text("en", source)
        assert translated.startswith(prefix)
        assert translated != source
