from __future__ import annotations

import socket
import threading
from pathlib import Path

from audioknigi.models import NarrationVariant

ROOT = Path(__file__).resolve().parents[2]


def test_connect_relay_forwards_payload_before_returning_on_upstream_eof():
    from audioknigi.network_dns import _relay_bidirectional

    client_side, relay_left = socket.socketpair()
    relay_right, upstream_side = socket.socketpair()
    thread = threading.Thread(
        target=_relay_bidirectional,
        args=(relay_left, relay_right),
        kwargs={"return_when_right_closes": True},
        daemon=True,
    )
    thread.start()
    try:
        payload = b"payload-before-fin"
        upstream_side.sendall(payload)
        upstream_side.shutdown(socket.SHUT_WR)
        assert client_side.recv(len(payload)) == payload
        thread.join(timeout=2.0)
        assert not thread.is_alive()
    finally:
        for sock in (client_side, relay_left, relay_right, upstream_side):
            try:
                sock.close()
            except OSError:
                pass


def test_connect_handler_keeps_bounded_upstream_eof_contract():
    source = (ROOT / "audioknigi" / "network_dns.py").read_text(encoding="utf-8")
    connect_start = source.index('if method.upper() == "CONNECT":')
    plain_start = source.index("parsed = urlsplit(target)", connect_start)
    connect_block = source[connect_start:plain_start]
    assert "_relay_bidirectional(client, upstream, return_when_right_closes=True)" in connect_block

def test_poleknig_title_fallback_extracts_only_quoted_book_name():
    from audioknigi.poleknig import _book_page_metadata

    html = """
    <html><head><title>«Книга» Автор: слушать аудиокнигу онлайн</title></head>
    <body><a href="/authors/123">Автор</a></body></html>
    """
    meta = _book_page_metadata(html, "https://poleknig.com/books/1")
    assert meta["title"] == "Книга"
    assert meta["author"] == "Автор"


def test_poleknig_meta_extractor_never_crosses_meta_tag_boundary():
    from audioknigi.poleknig import _extract_meta_content

    html = '<meta property="description"><meta property="og:image" content="https://example.test/cover.jpg">'
    assert _extract_meta_content(html, "description") == ""


def test_knigavuhe_reader_hydration_does_not_mutate_input_variants(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe

    variants = [
        NarrationVariant(url="https://knigavuhe.org/book/main/", narrator="Reader One", current=True),
        NarrationVariant(url="https://knigavuhe.org/book/alt/", narrator="", current=False),
    ]

    class Response:
        text = '<title>Book — автор Author, читает Reader Two (слушать аудиокнигу)</title>'

        @staticmethod
        def raise_for_status():
            return None

    class Session:
        @staticmethod
        def get(*args, **kwargs):
            return Response()

    monkeypatch.setattr(knigavuhe, "get_http_session", lambda: Session())
    hydrated = knigavuhe._hydrate_narration_variant_readers(
        variants,
        current_url="https://knigavuhe.org/book/main/",
    )
    assert variants[1].narrator == ""
    assert hydrated[1].narrator == "Reader Two"
    assert hydrated[1] is not variants[1]


def test_template_with_space_before_literal_extension_stays_single_extension():
    from audioknigi.models import Book, Track
    from audioknigi.templates import render_track_filename

    book = Book(url="", title="Book", tracks=[])
    track = Track(index=1, title="Part 01.mp3", file="")
    assert render_track_filename("{Track_Title} .mp3", book, track) == "Part 01.mp3"


def test_qt_accessibility_selftest_passes_offscreen_platform_explicitly():
    source = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    start = source.index("def _qt_accessibility_selftest")
    end = source.index("def main", start)
    block = source[start:end]
    assert 'create_application([sys.argv[0], "-platform", "offscreen"])' in block


def test_remote_ffprobe_paths_use_cloudflare_proxy_args():
    probe = (ROOT / "audioknigi" / "download" / "probe.py").read_text(encoding="utf-8")
    analysis = (ROOT / "audioknigi" / "services" / "book_analysis_service.py").read_text(encoding="utf-8")
    assert "*cloudflare_ffmpeg_input_args()" in probe[probe.index("def _probe_remote_duration"):]
    assert "*cloudflare_ffmpeg_input_args()" in analysis[analysis.index("def _probe_remote_duration"):]
