from __future__ import annotations

from pathlib import Path

import pytest

from audioknigi.core import effective_track_duration, safe_float
from audioknigi.i18n import localize_runtime_text, tr
from audioknigi.models import Book, Track

ROOT = Path(__file__).resolve().parents[2]


def test_safe_float_rejects_non_finite_values():
    assert safe_float(float("nan"), 1.25) == 1.25
    assert safe_float(float("inf"), 2.5) == 2.5
    assert safe_float(float("-inf"), 3.75) == 3.75


def test_effective_track_duration_rejects_zero_length_span():
    track = Track(index=1, title="One", file="https://example.test/1.mp3", start=10, end=10)
    assert effective_track_duration(track) is None


def test_knigavuhe_fetch_normalizes_scheme_less_url(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe

    requested = []

    class Response:
        url = "https://knigavuhe.org/book/sample/"
        text = "unused"

        @staticmethod
        def raise_for_status():
            return None

    class Session:
        def get(self, url, **kwargs):
            requested.append((url, kwargs))
            return Response()

    expected = Book(
        url="https://knigavuhe.org/book/sample/",
        title="Sample",
        tracks=[Track(index=1, title="1", file="https://cdn.test/1.mp3")],
    )
    monkeypatch.setattr(knigavuhe, "get_http_session", lambda: Session())
    monkeypatch.setattr(knigavuhe, "parse_book_html", lambda text, url: expected)
    monkeypatch.setattr(
        knigavuhe,
        "_hydrate_narration_variant_readers",
        lambda variants, current_url, cancel_event=None: variants,
    )

    result = knigavuhe.fetch_book("knigavuhe.org/book/sample/")
    assert result is expected
    assert requested[0][0] == "https://knigavuhe.org/book/sample/"


def test_knigavuhe_fetch_rejects_other_host_before_request(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe

    monkeypatch.setattr(
        knigavuhe,
        "get_http_session",
        lambda: pytest.fail("unsupported host must be rejected before opening a session"),
    )
    with pytest.raises(RuntimeError):
        knigavuhe.fetch_book("https://example.com/book/sample/")


def test_knigavuhe_invalid_bookcontroller_json_falls_back_to_direct_mp3():
    from audioknigi.knigavuhe import parse_book_html

    html = """
    <html><head><title>Fallback Book</title></head><body>
    <script>
      BookController.enter({book: 'legacy'}, secondArg);
      window.audio = "https://cdn.example.test/audio/001.mp3";
    </script>
    </body></html>
    """
    book = parse_book_html(html, "https://knigavuhe.org/book/fallback/")
    assert book.title == "Fallback Book"
    assert [track.file for track in book.tracks] == ["https://cdn.example.test/audio/001.mp3"]


def test_range_and_full_mp3_log_are_fully_localized():
    range_text = "Range 2/4 • 10 MB из 20 MB • 1 MB/s • ETA 00:10"
    assert localize_runtime_text("de", range_text) == "Range 2/4 • 10 MB von 20 MB • 1 MB/s • ETA 00:10"
    full_text = "Обрабатываю полный файл (исходный кодек: aac) с выбранным профилем качества и нормализацией."
    assert localize_runtime_text("en", full_text) == (
        "Processing full file (source codec: aac) with the selected quality profile and normalization."
    )


def test_full_mp3_stage_ids_exist_for_all_languages():
    for language in ("ru", "uk", "de", "en"):
        assert tr(language, "stage_full_mp3_download")
        assert tr(language, "stage_full_mp3_processing")
        assert tr(language, "stage_full_mp3_tags")


def test_reported_hardening_changes_are_present_in_sources():
    book_flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert 'owned = re.compile(' in book_flow
    assert 'candidate.is_file() or not owned.fullmatch(candidate.name)' in book_flow
    assert "self._scan_book_files(book, create_folder=False)" in book_flow

    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    assert 'startswith(("_source", "_repair"))' in player

    engine = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    assert "tags.save(str(target))" in engine

    media = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    assert 'author = str(getattr(book, "author", "") or "").strip()' in media

    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    invalid_result_block = analysis[analysis.index("if not isinstance(book, Book):"):analysis.index("pending = self._pending_search_result")]
    assert "self._queue_after_analysis = False" in invalid_result_block
    assert "self._download_after_analysis = False" in invalid_result_block
    assert "self._queue_reanalyze_task_id = None" in invalid_result_block
    assert "self._full_mp3_after_analysis = False" in invalid_result_block


def test_analysis_service_uses_shared_subprocess_pipe_cleanup():
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    helper = source[source.index("def _probe_remote_duration"):source.index("def _populate_missing_track_durations")]
    assert "close_subprocess_pipes(proc)" in helper
    assert 'for stream_name in ("stdin", "stdout", "stderr")' not in helper
