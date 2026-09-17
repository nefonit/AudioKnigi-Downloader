from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_poleknig_fetch_book_reraises_cancelled(monkeypatch):
    from audioknigi import poleknig
    from audioknigi.core import Cancelled
    from audioknigi.models import Book, Track

    class Response:
        url = "https://poleknig.com/books/123"
        text = "<html></html>"
        content = b"<html></html>"
        def raise_for_status(self):
            return None

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(poleknig, "get_http_session", lambda: Session())
    monkeypatch.setattr(
        poleknig,
        "parse_book_html",
        lambda *args, **kwargs: Book(
            url=Response.url, title="Book", tracks=[Track(index=1, title="1", file="https://cdn/a.mp3")]
        ),
    )
    monkeypatch.setattr(poleknig, "_book_page_metadata", lambda *args, **kwargs: {"title": "Book", "author": "", "narrator": ""})
    monkeypatch.setattr(
        poleknig,
        "_discover_narration_variants",
        lambda *args, **kwargs: (_ for _ in ()).throw(Cancelled("cancel")),
    )
    with pytest.raises(Cancelled):
        poleknig.fetch_book(Response.url)


def test_poleknig_meta_url_preserves_trailing_punctuation():
    from audioknigi.poleknig import _book_page_metadata

    html = '<h1>Book</h1><meta property="og:image" content="https://cdn.example/cover?v=x-">'
    meta = _book_page_metadata(html, "https://poleknig.com/books/1")
    assert meta["cover_url"] == "https://cdn.example/cover?v=x-"


def test_download_engine_has_shared_cover_fetch_method():
    from audioknigi.download_engine import _DownloadEngine
    assert callable(getattr(_DownloadEngine, "_fetch_cover_bytes", None))


def test_shared_cover_fetch_preserves_cancelled(monkeypatch):
    from audioknigi import cover_fetch
    from audioknigi.core import Cancelled

    event = SimpleNamespace(is_set=lambda: True)
    with pytest.raises(Cancelled):
        cover_fetch.fetch_cover_bytes("https://example.test/cover.jpg", cancel_event=event)


def test_media_sidecar_supports_webp_and_central_json_writer():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    assert 'elif "webp" in mime_text:' in source
    assert 'save_json(folder / "metadata.json", payload, raise_errors=True)' in source
    assert "_atomic_write_text(" not in source


def test_connect_proxy_ends_relay_on_upstream_eof():
    source = (ROOT / "audioknigi/network_dns.py").read_text(encoding="utf-8")
    connect_block = source[source.index('if method.upper() == "CONNECT"'):source.index('parsed = urlsplit(target)')]
    assert '_relay_bidirectional(client, upstream, return_when_right_closes=True)' in connect_block


def test_crash_report_survives_traceback_format_failure(monkeypatch, tmp_path):
    import audioknigi.crash_report as crash_report

    monkeypatch.setattr(crash_report, "CRASH_REPORT_FILE", tmp_path / "crash.txt")
    monkeypatch.setattr(
        crash_report.traceback,
        "format_exception",
        lambda *args, **kwargs: (_ for _ in ()).throw(RecursionError("format failed")),
    )
    exc = RecursionError("original")
    text = crash_report.build_report(RecursionError, exc, None, component="test")
    assert "RecursionError: original" in text
    assert "traceback formatting failed" in text
    assert (tmp_path / "crash.txt").exists()


def test_playlist_null_title_uses_numeric_fallback():
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    assert 'raw_track_title = html_lib.unescape(' in source
    assert 'title=raw_track_title or f"{track_index:02d}"' in source


def test_playlist_worker_cancelled_is_not_swallowed():
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    parse_block = source[source.index("def _parse_playlist_data"):source.index("def _analyze_audioknigi_requests")]
    assert "except Cancelled:" in parse_block
    assert "except Cancelled:\n                    raise" in parse_block


def test_onboarding_accepted_settings_use_normalized_writer():
    source = (ROOT / "audioknigi/qt/application.py").read_text(encoding="utf-8")
    assert "settings = onboarding.result_settings()\n            save_app_settings(settings)" in source


def test_worker_snapshot_drops_native_cover_before_deepcopy():
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert "normalized_cover = normalize_cover_cache(raw_cover)" in source
    assert "snapshot_source.book.cover_cache = None" in source
    assert "worker_request = copy.deepcopy(snapshot_source)" in source


def test_missing_uk_literals_are_complete():
    from audioknigi.i18n import ui_text

    assert ui_text("uk", "Нет активной операции для отмены.") == "Немає активної операції для скасування."
    assert ui_text("uk", "Очередь очищена.") == "Чергу очищено."


def test_download_progress_runtime_translation_is_complete():
    from audioknigi.i18n import localize_runtime_text

    assert localize_runtime_text("en", "Скачано 15 MB из 100 MB") == "Downloaded 15 MB of 100 MB"
    assert localize_runtime_text("de", "Скачано 15 MB из 100 MB") == "Heruntergeladen 15 MB von 100 MB"
    assert localize_runtime_text("uk", "Скачано 15 MB из 100 MB") == "Завантажено 15 MB із 100 MB"


def test_queue_unresolved_summary_uses_stable_translations():
    from audioknigi.i18n import tr

    assert tr("en", "queue_stopped_unresolved", details=tr("en", "queue_unresolved_errors", count=2)) == "Queue stopped; tasks remain (with error: 2)."
    source = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    assert 'details.append(f"на паузе:' not in source
    assert 'tr(self.language, "queue_stopped_unresolved"' in source


def test_version_and_runtime_stage_41239():
    from audioknigi.metadata import APP_VERSION
    from audioknigi.qt import QT_RUNTIME_STAGE

    assert APP_VERSION == "4.12.42"
    assert QT_RUNTIME_STAGE == "qt-only-4.12.42"
