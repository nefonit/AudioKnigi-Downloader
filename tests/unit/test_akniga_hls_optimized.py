"""Offline HLS regressions: selected chapters, fallback, progress and remux."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.models import Book, Track, TRACK_STATUS_READY

URL = "https://akniga.org/glubina-pogruzhenie-76-e"
HLS = "https://cdn.example.org/a/stream.m3u8?token=fake"


def book_with_chapters(count=10):
    return Book(url=URL, title="Test Book", tracks=[
        Track(index=i, title=f"Part {i}", file=HLS, start=(i-1)*10, end=i*10, duration=10)
        for i in range(1, count+1)
    ])


def test_direct_hls_only_for_small_unchanged_audiobooks():
    book = book_with_chapters()
    engine = SimpleNamespace(runtime_audio_preset="copy", runtime_normalization_mode="off")
    eligible = BookFlowMixin._akniga_direct_chapters_eligible
    assert eligible(engine, book, book.tracks[:2])
    assert eligible(engine, book, book.tracks[:5]) is False
    engine.runtime_normalization_mode = "two_pass"
    assert not eligible(engine, book, book.tracks[:2])
    engine.runtime_normalization_mode = "off"
    engine.runtime_audio_preset = "128k_stereo"
    assert not eligible(engine, book, book.tracks[:2])
    book.url = "https://knigavuhe.org/book/foo/"
    assert not eligible(engine, book, book.tracks[:2])


def test_direct_hls_success_does_not_change_chapter_timeline(tmp_path):
    book = book_with_chapters()
    selected = book.tracks[2:4]
    old = [(tr.start, tr.end, tr.file) for tr in book.tracks]
    results = []

    class Engine:
        def log(self, text): results.append(text)
        def set_stage(self, *_args): pass
        def set_status(self, *_args): pass
        def set_progress(self, *_args): pass
        def _check_cancel(self): pass
        def _track_path(self, _book, tr): return tmp_path / f"{tr.index:02}.mp3"
        def _download_hls_chapter(self, book, tr, **kwargs):
            assert kwargs['chapter_number'] in (1, 2)
            self._track_path(book, tr).write_bytes(b"ID3" + b"good"*100)
        def _verify_track_file(self, book, tr):
            return TRACK_STATUS_READY, 10.0, self._track_path(book, tr)

    assert BookFlowMixin._try_akniga_direct_chapters(Engine(), book, selected, lambda _x: None)
    assert [(tr.start, tr.end, tr.file) for tr in book.tracks] == old
    assert all((tmp_path / f"{tr.index:02}.mp3").exists() for tr in selected)
    assert not list(tmp_path.glob("_source*.mp3"))


def test_direct_hls_failure_cleans_owned_outputs_only(tmp_path):
    book = book_with_chapters()
    selected = book.tracks[2:4]
    existing = tmp_path / '01.mp3'
    existing.write_bytes(b'original')
    class Engine:
        def log(self, _text): pass
        def set_stage(self, *_args): pass
        def set_status(self, *_args): pass
        def set_progress(self, *_args): pass
        def _check_cancel(self): pass
        def _track_path(self, _book, tr): return tmp_path / f"{tr.index:02}.mp3"
        def _download_hls_chapter(self, book, tr, **_kwargs):
            if tr.index == 4:
                raise RuntimeError("seek not available")
            self._track_path(book, tr).write_bytes(b"partial")
        def _verify_track_file(self, book, tr):
            return TRACK_STATUS_READY, 10.0, self._track_path(book, tr)
    assert not BookFlowMixin._try_akniga_direct_chapters(Engine(), book, selected, lambda _x: None)
    assert existing.read_bytes() == b'original'
    # Chapter 3 completed and passed verification before chapter 4 failed.
    assert (tmp_path/'03.mp3').read_bytes() == b'partial'
    assert not (tmp_path/'04.mp3').exists()


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg required")
def test_local_hls_seek_cut_and_copy_fallback(tmp_path):
    manifest = tmp_path / "test.m3u8"
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=660:duration=12",
        "-c:a", "aac", "-b:a", "96k", "-f", "hls", "-hls_time", "2",
        "-hls_playlist_type", "vod", str(manifest),
    ], check=True)
    progress = []
    logs = []
    class Engine:
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"
        def _check_cancel(self): pass
        def _register_active_subprocess(self, _p): pass
        def _unregister_active_subprocess(self, _p): pass
        def set_progress(self, value): progress.append(value)
        def set_status(self, _s): pass
        def log(self, text): logs.append(text)
    engine = Engine()
    source = tmp_path / '_source.mp3'
    old_part = tmp_path / '_source.mp3.part'
    old_part.write_bytes(b'locked-file-do-not-touch')
    NetworkDownloadMixin._run_hls_ffmpeg(engine, str(manifest), source, "", expected_duration=12)
    assert source.stat().st_size > 0
    assert any('перекодирую' in message for message in logs)
    assert old_part.read_bytes() == b'locked-file-do-not-touch'
    clip = tmp_path / '03.mp3'
    NetworkDownloadMixin._run_hls_ffmpeg(
        engine, str(manifest), clip, "", start=4, duration=3,
        expected_duration=3, progress_offset=25, progress_span=25,
    )
    duration = float(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(clip),
    ], text=True))
    assert duration == pytest.approx(3, abs=0.3)
    assert progress[-1] == 50
    assert not list(tmp_path.glob('.*.hls-*.mp3'))
