from __future__ import annotations

import threading
from collections import UserDict
from pathlib import Path

import pytest

from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle
from audioknigi.download_engine import _DownloadEngine
from audioknigi.models import Book, Track
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.download_request import build_download_request

ROOT = Path(__file__).resolve().parents[2]


def test_support_bundle_masks_forward_slash_unc_paths():
    assert support_bundle._privacy_path("//server/private/audiobooks") == "<configured-path>"
    assert support_bundle._privacy_path("//?/UNC/server/private") == "<configured-path>"


def test_support_tail_keeps_valid_utf8_when_byte_window_cuts_codepoints(tmp_path):
    path = tmp_path / "app.log"
    path.write_bytes(("я" * 20).encode("utf-8"))
    payload = support_bundle._tail(path, max_bytes=7)
    payload.decode("utf-8")
    assert payload


def test_structured_book_nodes_accept_schema_org_uri_and_prefix_types():
    html = """
    <script type="application/ld+json">
    [
      {"@type":"https://schema.org/Book","name":"One"},
      {"@type":"http://schema.org/Audiobook","name":"Two"},
      {"@type":"schema:CreativeWork","name":"Three"},
      {"@type":"WebSite","name":"Ignore"}
    ]
    </script>
    """
    assert [row["name"] for row in _structured_book_nodes(html)] == ["One", "Two", "Three"]


def test_knigavuhe_fetch_book_honors_already_cancelled_event(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe

    event = threading.Event()
    event.set()

    def should_not_open_session():
        raise AssertionError("HTTP session must not be opened after cancellation")

    monkeypatch.setattr(knigavuhe, "get_http_session", should_not_open_session)
    with pytest.raises(Cancelled):
        knigavuhe.fetch_book("https://knigavuhe.org/book/demo/", cancel_event=event)


def test_remote_size_requests_identity_encoding(monkeypatch):
    import audioknigi.services.book_analysis_service as module

    captured = {}

    class Response:
        status_code = 206
        headers = {"content-range": "bytes 0-0/12345"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @staticmethod
        def raise_for_status():
            return None

    class Session:
        def get(self, url, **kwargs):
            captured.update(kwargs)
            return Response()

    monkeypatch.setattr(module, "get_http_session", lambda: Session())
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    assert service._remote_size("https://cdn.example/audio.mp3", "https://example.test/book") == 12345
    assert captured["headers"]["Accept-Encoding"] == "identity"


def test_retained_full_source_path_never_aliases_processed_target(tmp_path):
    target = tmp_path / "Book (исходник).mp3"
    retained = _DownloadEngine._retained_full_source_path(tmp_path, "Book", ".mp3", target)
    assert retained != target
    assert retained.name == "Book (исходник, оригинал).mp3"


def test_build_download_request_accepts_mapping_settings(tmp_path):
    book = Book(url="https://knigavuhe.org/book/demo/", title="Demo", tracks=[Track(index=1, title="One", file="1.mp3")])
    settings = UserDict({"output_dir": str(tmp_path), "audio_preset": "copy"})
    request = build_download_request(book, settings, [1])
    assert request.output_dir == tmp_path
    assert request.selected_indices == [1]


def test_parallel_ffmpeg_failure_and_drop_queue_contracts_are_present():
    flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    split_start = flow.index('self.log("Параллельная нарезка одного исходника')
    split_end = flow.index('if want_mp3 and mp3_needs_creation:', split_start)
    split_block = flow[split_start:split_end]
    assert split_block.count("self._cancel_active_subprocesses()") >= 2

    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    start = analysis.index("if not isinstance(book, Book):")
    end = analysis.index("pending = self._pending_search_result", start)
    block = analysis[start:end]
    assert 'getattr(self, "_pending_queue_urls", None)' in block
    assert "QTimer.singleShot(0, self._queue_next_dropped_url)" in block


def test_shortcut_parser_only_adopts_supported_url():
    source = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    start = source.index('match = re.search(r"(?im)^URL=(.+)$", content)')
    block = source[start : start + 320]
    assert "shortcut_url = match.group(1).strip()" in block
    assert "if valid_site_url(shortcut_url):" in block
