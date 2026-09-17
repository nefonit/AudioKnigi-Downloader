from __future__ import annotations

import inspect
import socket
import threading
from pathlib import Path
from types import SimpleNamespace

from audioknigi import core, poleknig
from audioknigi.download_engine import _DownloadEngine
from audioknigi.network_dns import _relay_bidirectional
from audioknigi.services.download_request import DownloadRequest


ROOT = Path(__file__).resolve().parents[2]


def test_safe_name_replaces_windows_control_characters() -> None:
    value = core.safe_name("part\x00one\x1f?.mp3")
    assert value.endswith(".mp3")
    assert "?" not in value
    assert all(ord(ch) >= 32 for ch in value)
    assert "part_one__" in value


def test_delete_existing_outputs_uses_download_request_track_index_for_mappings(tmp_path) -> None:
    target = tmp_path / "003.mp3"
    target.write_bytes(b"old")
    book = SimpleNamespace(tracks=[{"index": "3"}])
    request = DownloadRequest(book=book, selected_indices=[3], output_dir=tmp_path)
    engine = object.__new__(_DownloadEngine)
    engine.request = request
    engine._track_path = lambda *_a, **_k: target

    assert engine.delete_existing_outputs() == 1
    assert not target.exists()


def test_poleknig_book_title_preserves_meaningful_edge_punctuation() -> None:
    meta = poleknig._book_page_metadata(
        "<html><body><h1>— Название книги —</h1></body></html>",
        "https://poleknig.com/books/123",
    )
    assert meta["title"] == "— Название книги —"


def test_playwright_cookie_restore_is_fault_isolated_and_event_callback_does_not_raise_cancelled() -> None:
    pole_source = inspect.getsource(poleknig._fetch_book_playwright)
    analysis_source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")

    assert "context.add_cookies([cookie])" in pole_source
    assert "Failed to restore PoleKnig cookie" in pole_source
    callback = pole_source[pole_source.index("def on_request(request):"): pole_source.index('page.on("request", on_request)')]
    assert 'raise Cancelled("Операция отменена пользователем")' not in callback
    assert "return" in callback

    assert "context.add_cookies([cookie])" in analysis_source
    assert "Failed to restore audioknigi cookie" in analysis_source


def test_book_flow_counts_only_sources_that_really_existed() -> None:
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    block = source[source.index("removed_sources = 0"): source.index('self._log_book_flow("source_cleanup"')]
    assert "unlink_with_retry(path, missing_ok=False)" in block
    assert "except FileNotFoundError:" in block


def test_connect_relay_preserves_reverse_direction_after_upstream_half_close() -> None:
    client, left = socket.socketpair()
    right, upstream = socket.socketpair()
    worker = threading.Thread(target=_relay_bidirectional, args=(left, right), daemon=True)
    worker.start()
    try:
        upstream.sendall(b"response")
        upstream.shutdown(socket.SHUT_WR)
        client.settimeout(2.0)
        assert client.recv(8) == b"response"

        # The upstream has half-closed its write side, but CONNECT is a tunnel:
        # client -> upstream traffic must still be relayed until the client closes.
        client.sendall(b"late-client")
        upstream.settimeout(2.0)
        assert upstream.recv(11) == b"late-client"
        client.shutdown(socket.SHUT_WR)
        worker.join(2.0)
        assert not worker.is_alive()
    finally:
        for sock in (client, left, right, upstream):
            try:
                sock.close()
            except OSError:
                pass


def test_connect_handler_uses_full_duplex_relay_but_plain_http_can_end_on_upstream_eof() -> None:
    source = (ROOT / "audioknigi/network_dns.py").read_text(encoding="utf-8")
    connect_block = source[source.index('if method.upper() == "CONNECT":'): source.index("parsed = urlsplit(target)")]
    assert "_relay_bidirectional(client, upstream)" in connect_block
    assert "return_when_right_closes=True" not in connect_block
    assert source.count("return_when_right_closes=True") == 1


def test_round22_removes_only_confirmed_dead_checks_and_redundant_range_noop() -> None:
    analysis_source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    network_source = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    settings_source = (ROOT / "audioknigi/config/settings.py").read_text(encoding="utf-8")

    assert "if playlist_response is None:" not in analysis_source
    range_block = network_source[network_source.index("if status == 200:"): network_source.index('cr = response.headers.get("content-range", "")')]
    assert range_block.count("response.raise_for_status()") == 1
    # The reported legacy string type is already normalized later; retain that migration contract.
    assert 'raw["auto_chunk_min_kbytes_per_sec"] = max(1, safe_int(' in settings_source
