from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from audioknigi.downloader import DownloaderMixin, SharedSourceTimelineError
from audioknigi.i18n import localize_runtime_text
from audioknigi.knigavuhe import _book_page_search_metadata, _description_from_html, _extract_narration_variants
from audioknigi.models import Book, Track
from audioknigi.poleknig import _canonical_author_url, _extract_meta_content, _normalize_js_literals_for_python
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.library_service import scan_unfinished
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict

ROOT = Path(__file__).resolve().parents[1]


def source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class _FallbackHost(DownloaderMixin):
    def __init__(self, original: Book, fallback: Book):
        self.fallback = fallback
        self.request = SimpleNamespace(book=original, selected_indices=[], callbacks=SimpleNamespace(request_changed=None))
        self.callbacks = SimpleNamespace(request_changed=None)
        self.calls = []

    def _process_book_once(self, book, selected_indices, status_callback):
        self.calls.append((book.url, set(selected_indices)))
        if "audioknigi.com.ua" in book.url:
            raise SharedSourceTimelineError({"expected_end": 100.0, "actual_duration": 50.0, "reason": "short"})
        return "done"

    def _clear_stale_source_downloads(self, _book):
        return None

    def _knigavuhe_fallback_candidate(self, _book):
        return self.fallback

    def _populate_missing_track_durations(self, _book):
        return 0


def _book(url: str, count: int) -> Book:
    return Book(url=url, title="Book", tracks=[Track(index=i, title=str(i), file=f"https://cdn/{i}.mp3") for i in range(1, count + 1)])


def test_cross_provider_fallback_refuses_partial_index_mapping():
    original = _book("https://audioknigi.com.ua/audio-1", 30)
    fallback = _book("https://knigavuhe.org/book/book/", 15)
    host = _FallbackHost(original, fallback)
    with pytest.raises(RuntimeError, match="нельзя безопасно сопоставить"):
        host._process_book(original, selected_indices=[25, 26])
    assert len(host.calls) == 1


def test_cross_provider_fallback_can_switch_when_whole_book_was_selected():
    original = _book("https://audioknigi.com.ua/audio-1", 3)
    fallback = _book("https://knigavuhe.org/book/book/", 2)
    host = _FallbackHost(original, fallback)
    result = host._process_book(original, selected_indices=[1, 2, 3])
    assert result == "done"
    assert host.calls[-1][1] == {1, 2}
    assert host.request.selected_indices == [1, 2]


def test_complex_loudnorm_includes_primary_source_before_extra_inputs():
    class Host(DownloaderMixin):
        def __init__(self):
            self.command = None

        def _run_ffmpeg_capture(self, cmd, timeout=None):
            self.command = list(cmd)
            return '{"input_i":"-20.0","input_lra":"3.0","input_tp":"-1.0","input_thresh":"-30.0","target_offset":"0.1"}'

    host = Host()
    host._measure_loudnorm(
        Path("primary.mp3"),
        filter_complex="[0:a]anull[a]",
        map_label="[a]",
        extra_inputs=[Path("secondary.mp3")],
    )
    first_i = host.command.index("-i")
    second_i = host.command.index("-i", first_i + 1)
    assert host.command[first_i + 1] == "primary.mp3"
    assert host.command[second_i + 1] == "secondary.mp3"


def test_track_duration_tolerance_scales_for_long_chapters(tmp_path):
    path = tmp_path / "01.mp3"
    path.write_bytes(b"x")

    class Host(DownloaderMixin):
        def _track_path(self, book, track, *, create_folder=True):
            return path

        def _probe_duration(self, _path):
            return self.actual

    host = Host()
    book = _book("https://knigavuhe.org/book/book/", 1)
    track = book.tracks[0]
    track.duration = 1000.0
    host.actual = 1010.0
    assert host._verify_track_file(book, track)[0] == "готово"
    host.actual = 1020.0
    assert host._verify_track_file(book, track)[0] == "повреждён"


def test_downloader_mixin_has_headless_safe_defaults_and_hooks():
    host = DownloaderMixin()
    assert host.cancel_event is None
    assert host.runtime_naming_mode == "number"
    assert host.ui(lambda: 7) == 7
    assert host._write_resume_manifest(None, []) is None
    assert host._remove_resume_manifest(None) is None
    assert host._add_history(None, None, 0) is None


def test_full_mp3_resume_mode_survives_unfinished_scan(tmp_path):
    folder = tmp_path / "Book"
    folder.mkdir()
    (folder / "resume.json").write_text(
        '{"url":"https://knigavuhe.org/book/book/","title":"Book","selected_indices":[1,2],"download_mode":"full_mp3"}',
        encoding="utf-8",
    )
    rows = scan_unfinished(tmp_path)
    assert len(rows) == 1
    assert rows[0].download_mode == "full_mp3"
    ui_source = source("audioknigi/qt/main_window.py")
    assert "self._full_mp3_after_analysis" in ui_source
    assert "QTimer.singleShot(0, self.start_full_mp3)" in ui_source


def test_partial_files_append_suffix_instead_of_replacing_it():
    downloader = source("audioknigi/downloader.py")
    assert 'target.with_name(target.name + ".part")' in downloader
    assert 'part.with_name(part.name + ".assembling")' in downloader


def test_knigavuhe_description_heading_and_en_dash_metadata():
    html = '<div class="book_description">Полное <div>вложенное</div> описание.</div>'
    assert "Полное вложенное описание." == _description_from_html(html)

    meta = _book_page_search_metadata(
        '<title>Книга (слушать аудиокнигу онлайн) – автор Иван Иванов, читает Пётр Петров</title>'
    )
    assert meta["title"] == "Книга"
    assert meta["author"] == "Иван Иванов"
    assert meta["narrator"] == "Пётр Петров"

    variants = _extract_narration_variants(
        '<div class="block_title">Другие озвучки</div><a href="/book/other/">Другой чтец</a>',
        "https://knigavuhe.org/book/main/",
        title="Книга",
        current_narrator="Первый чтец",
    )
    assert any(v.url.endswith("/book/other/") for v in variants)


def test_poleknig_author_slug_meta_order_and_js_literal_normalization():
    assert _canonical_author_url("https://poleknig.com/", "/authors/789-aleksandr-pushkin") == "https://poleknig.com/authors/789"
    assert _extract_meta_content('<meta content="Описание" name="description">', "description") == "Описание"
    raw = "[{'title':'true detective and not false','autostart':false,'value':null}]"
    normalized = _normalize_js_literals_for_python(raw)
    assert "true detective and not false" in normalized
    assert "'autostart':False" in normalized
    assert "'value':None" in normalized


def test_recover_short_source_ignores_empty_or_invalid_end_values():
    service = BookAnalysisService()
    book = Book(
        url="https://audioknigi.com.ua/audio-1",
        title="Book",
        tracks=[Track(index=1, title="1", file="https://cdn/book.mp3", end="")],
    )
    assert service._recover_short_audioknigi_source(book) is book


def test_queue_stale_textual_running_status_becomes_interrupted(tmp_path):
    book = _book("https://knigavuhe.org/book/book/", 1)
    request = DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path)
    data = task_to_dict(QueueTask(id="1", request=request, title="Book", status="Скачивается", status_code="pending"))
    restored = task_from_dict(data)
    assert restored.status_code == "interrupted"
    assert restored.status == "Незавершено"


def test_dynamic_short_source_status_is_localized():
    message = "Источник audioknigi.com.ua короче плейлиста (100 с вместо 200 с). Ищу резервный источник…"
    assert localize_runtime_text("en", message).startswith("The audioknigi.com.ua source is shorter")
    assert localize_runtime_text("de", message).startswith("Die Quelle audioknigi.com.ua")


def test_qt_regressions_are_wired_without_importing_qt_runtime():
    player = source("audioknigi/qt/player_controller.py")
    assert "explicit_seconds=target / 1000.0" in player
    assert "explicit_seconds: float | None = None" in player

    window = source("audioknigi/qt/main_window.py")
    assert "def _save_settings(self, _checked: bool = False, *, silent: bool = False):" in window
    assert "self._search_thread, self._abs_thread" in window or "self._search_thread, self._abs_thread)" in window
    assert "self._abs_thread.requestInterruption()" in window

    application = source("audioknigi/qt/application.py")
    assert 'getattr(app, "_audioknigi_base_font_py", None)' in application

    sounds = source("audioknigi/qt/event_sounds.py")
    assert "mediaStatusChanged.connect(play_when_loaded)" in sounds
    assert "QMediaPlayer.MediaStatus.LoadingMedia" in sounds


def test_audiobookshelf_ssl_error_is_explicit(monkeypatch):
    import audioknigi.integrations as integrations

    class Session:
        def get(self, *args, **kwargs):
            raise requests.exceptions.SSLError("self signed")

    monkeypatch.setattr(integrations, "get_http_session", lambda: Session())
    with pytest.raises(RuntimeError, match="недоверенный HTTPS-сертификат"):
        integrations.audiobookshelf_get_libraries("https://local.example", "key")


def test_crash_report_uses_brand_display_name():
    crash = source("audioknigi/crash_report.py")
    assert "from .brand import DISPLAY_NAME" in crash
    assert 'f"{DISPLAY_NAME} {APP_VERSION}' in crash
    assert "import os" not in crash
