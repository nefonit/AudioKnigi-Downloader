"""Offline regressions for safe playlist refresh, HLS fallback and localization."""
from __future__ import annotations

import pytest

from audioknigi.download import book_flow
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track, TRACK_STATUS_MISSING, TRACK_STATUS_READY
from audioknigi.services.source_health_service import classify_network_error


def _playlist_book(old_track):
    return Book(url="https://akniga.org/sample-book", title="Before", tracks=[old_track])


@pytest.mark.parametrize("as_mapping", [False, True])
def test_refresh_playlist_preserves_legacy_track_state(as_mapping):
    original = Track(
        index=3, title="Old", file="https://old.example/stream.m3u8",
        selected=False, local_status=TRACK_STATUS_READY,
        actual_duration=12.5, local_path="C:/Audio/03.mp3",
    )
    old_track = {
        "index": original.index, "title": original.title, "file": original.file,
        "selected": original.selected, "local_status": original.local_status,
        "actual_duration": original.actual_duration, "local_path": original.local_path,
    } if as_mapping else original
    book = _playlist_book(old_track)
    replacement = Track(index=3, title="New", file="https://new.example/stream.m3u8")

    class Flow(BookFlowMixin):
        runtime_language = "ru"

        def _check_cancel(self):
            pass

        def set_status(self, *_a):
            pass

        def set_stage(self, *_a):
            pass

        def log(self, *_a):
            pass

        def _analyze_book(self, _url):
            return Book(url=book.url, title="After", tracks=[replacement])

        def _clear_stale_source_downloads(self, _book):
            return 0

    assert Flow()._refresh_book_media_playlist(book, [3]) == 1
    assert book.title == "After"
    assert book.tracks == [replacement]
    assert replacement.selected is False
    assert replacement.local_status == TRACK_STATUS_READY
    assert replacement.actual_duration == 12.5
    assert replacement.local_path == "C:/Audio/03.mp3"


def test_direct_hls_failure_preserves_verified_chapter_and_falls_back_only_for_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(book_flow, "resolve_executable", lambda _name: "ffmpeg")
    url = "https://cdn.example.test/shared.m3u8"
    book = Book(url="https://akniga.org/sample-book", title="Test", tracks=[
        Track(index=3, title="Chapter 3", file=url, start=20, end=30, duration=10),
        Track(index=4, title="Chapter 4", file=url, start=30, end=40, duration=10),
    ])
    plans = []

    class FallbackReached(Exception):
        pass

    class Flow(BookFlowMixin):
        def _check_cancel(self):
            pass

        def set_status(self, *_a):
            pass

        def set_stage(self, *_a):
            pass

        def set_progress(self, *_a):
            pass

        def log(self, *_a):
            pass

        def _track_path(self, _book, tr):
            return tmp_path / f"{tr.index:02d}.mp3"

        def _verify_track_file(self, _book, tr, **_kwargs):
            path = self._track_path(book, tr)
            status = TRACK_STATUS_READY if path.exists() and path.read_bytes() == b"verified" else TRACK_STATUS_MISSING
            return status, 10.0 if status == TRACK_STATUS_READY else None, path

        def _download_hls_chapter(self, _book, tr, **_kwargs):
            path = self._track_path(book, tr)
            if tr.index == 3:
                path.write_bytes(b"verified")
            else:
                path.write_bytes(b"partial")
                raise RuntimeError("HLS seek failed")

        def _scan_book_files(self, _book, *, create_folder=True):
            for tr in book.tracks:
                status, actual, path = self._verify_track_file(book, tr)
                tr.local_status = status
                tr.actual_duration = actual
                tr.local_path = str(path)
            return {}

        def _check_disk_space(self, *_a, **_kwargs):
            return True

        def _write_resume_manifest(self, *_a, **_kwargs):
            pass

        def _book_folder(self, *_a, **_kwargs):
            return tmp_path

        def _log_book_flow(self, event, _book, **kwargs):
            if event == "download_plan":
                plans.append(kwargs)

        def _akniga_direct_chapters_eligible(self, *_a):
            return True

        def _source_target_assignments(self, *_a):
            raise FallbackReached

    with pytest.raises(FallbackReached):
        Flow()._process_book_once(book, {3, 4})
    assert (tmp_path / "03.mp3").read_bytes() == b"verified"
    assert not (tmp_path / "04.mp3").exists()
    assert book.tracks[0].local_status == TRACK_STATUS_READY
    assert book.tracks[1].local_status == TRACK_STATUS_MISSING
    assert len(plans) == 1
    assert plans[0]["mp3_to_create"] == 1
    assert plans[0]["existing_mp3"] == 1


@pytest.mark.parametrize("language", ["en", "de", "uk"])
def test_download_engine_messages_have_runtime_translations(language):
    sources = [
        "FFmpeg не найден. Он необходим для обработки полного файла MP3.",
        "Недостаточно места для обработки полного MP3. Нужно ещё ~40 MB, свободно 20 MB.",
        "Не удалось сохранить файл восстановления: C:/Books/recovery.json",
    ]
    for russian in sources:
        translated = localize_runtime_text(language, russian)
        assert translated != russian, (language, russian)
        if "40 MB" in russian:
            assert "40 MB" in translated and "20 MB" in translated


@pytest.mark.parametrize("language", ["en", "de", "uk"])
def test_network_errors_have_runtime_translations(language):
    import requests
    errors = [
        classify_network_error(requests.exceptions.ConnectTimeout("timeout")),
        classify_network_error(requests.exceptions.ProxyError("proxy")),
        classify_network_error(requests.exceptions.SSLError("tls")),
        classify_network_error(OSError("connection refused")),
    ]
    for message in errors:
        assert localize_runtime_text(language, message) != message


@pytest.mark.parametrize("language", ["en", "de", "uk"])
def test_provider_errors_have_runtime_translations(language):
    messages = [
        "akniga.org: не найдена область книг в подборке.",
        "akniga.org: не найдена область результатов поиска (возможно, изменился сайт).",
        "izib.uk: настройки XSPlayer не найдены либо книга недоступна.",
        "izib.uk: не найдена область результатов поиска (возможно, изменился сайт).",
        "yakniga.org: эта книга доступна только по лицензии; скачивание недоступно.",
    ]
    for message in messages:
        assert localize_runtime_text(language, message) != message
