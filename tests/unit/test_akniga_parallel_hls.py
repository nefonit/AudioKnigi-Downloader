"""Focused no-network tests of the Akniga HLS segment fast path."""
from pathlib import Path
import time

import pytest

from audioknigi.download import hls_parallel

BASE = "https://audio.example.org/test/media.m3u8"
PLAIN = b"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:17
#EXT-X-TARGETDURATION:4
#EXTINF:4.0,
s1.ts
#EXTINF:4.0,
s2.ts
#EXT-X-ENDLIST
"""
ENCRYPTED = b"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:7
#EXT-X-KEY:METHOD=AES-128,URI="key.bin",IV=0x00000000000000000000000000000007
#EXTINF:3.0,
s1.ts
#EXTINF:4.0,
s2.ts
#EXT-X-ENDLIST
"""


def test_parallel_hls_preserves_sequence_even_when_finished_out_of_order(monkeypatch, tmp_path):
    monkeypatch.setattr(hls_parallel, "_get_bytes", lambda *_a, **_kw: PLAIN)
    completion_order = []

    def fake_worker(index, url, dest, *_args, **_kwargs):
        if index == 0:
            time.sleep(0.03)
        dest.write_bytes(f"segment-{index}".encode())
        completion_order.append(index)
        return index, dest.stat().st_size

    monkeypatch.setattr(hls_parallel, "_download_segment", fake_worker)
    progress = []
    result = hls_parallel.stage_hls_vod(
        BASE, tmp_path, referer="https://akniga.org/", user_agent="test",
        check_cancel=lambda: None, on_progress=lambda *v: progress.append(v), max_workers=2,
    )
    assert completion_order == [1, 0]
    assert result.is_file()
    local = result.read_text(encoding="utf-8")
    assert local.index("seq000000.ts") < local.index("seq000001.ts")
    assert "#EXT-X-MEDIA-SEQUENCE:17" in local
    assert progress[-1][0:2] == (2, 2)


def test_parallel_hls_stages_aes_keys_without_rewriting_iv(monkeypatch, tmp_path):
    def get_bytes(url, *_args, **_kwargs):
        return ENCRYPTED if url == BASE else b"K" * 16
    monkeypatch.setattr(hls_parallel, "_get_bytes", get_bytes)

    def fake_worker(index, url, dest, *_a, **_kw):
        dest.write_bytes(b"audio")
        return index, 5
    monkeypatch.setattr(hls_parallel, "_download_segment", fake_worker)
    result = hls_parallel.stage_hls_vod(
        BASE, tmp_path, referer="", user_agent="test",
        check_cancel=lambda: None, on_progress=lambda *_: None,
    )
    assert (tmp_path / "key000.key").read_bytes() == b"K" * 16
    local = result.read_text()
    assert 'URI="key000.key"' in local
    assert "IV=0x00000000000000000000000000000007" in local
    assert BASE not in local


def test_parallel_hls_rejects_live_and_master_playlists(monkeypatch, tmp_path):
    for raw in (
        b"#EXTM3U\n#EXTINF:2.0,\na.ts\n",  # No ENDLIST: live HLS
        b"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=128000\nx.m3u8\n#EXT-X-ENDLIST\n",
        b"#EXTM3U\n#EXT-X-BYTERANGE:128@0\n#EXTINF:2.0,\na.ts\n#EXT-X-ENDLIST\n",
    ):
        monkeypatch.setattr(hls_parallel, "_get_bytes", lambda *_a, **_kw: raw)
        result = hls_parallel.stage_hls_vod(
            BASE, tmp_path, referer="", user_agent="test",
            check_cancel=lambda: None, on_progress=lambda *_: None,
        )
        assert result is None
    assert not list(tmp_path.glob("seq*.ts"))


def test_parallel_hls_does_not_access_internal_private_urls(monkeypatch):
    assert not hls_parallel._safe_http_url("http://127.0.0.1:1234/a.ts")
    assert not hls_parallel._safe_http_url("https://10.1.1.1/a.ts")
    assert not hls_parallel._safe_http_url("file:///etc/passwd")
    assert hls_parallel._safe_http_url("https://cdn.example.org/a.ts")
