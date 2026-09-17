"""4.12.8 regressions for FFmpeg diagnostics and non-MP3 source compatibility."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, Track


class _ProfileHost(DownloaderMixin):
    def __init__(self, info):
        self.runtime_audio_preset = "copy"
        self.runtime_normalization_mode = "off"
        self._info = dict(info)
        self.messages = []

    def _probe_audio_info(self, _source_path):
        return dict(self._info)

    def log(self, text):
        self.messages.append(str(text))


class _SplitHost(DownloaderMixin):
    def __init__(self, output: Path):
        self.output = Path(output)
        self.runtime_audio_preset = "copy"
        self.runtime_normalization_mode = "off"
        self.messages = []
        self.commands = []

    def _check_cancel(self):
        return None

    def _track_path(self, _book, _track, mode=None):
        return self.output

    def _effective_mp3_profile(self, _source_path):
        return True, None, None

    def _normalization_filter_for_track(self, _source_path, _start, _duration):
        return ""

    def _probe_audio_info(self, _source_path):
        return {"codec": "mp3", "bit_rate": 96000, "channels": 2}

    def _run_ffmpeg(self, cmd, timeout=7200):
        self.commands.append(list(cmd))
        if len(self.commands) == 1:
            raise RuntimeError("simulated stream-copy failure")
        self.output.write_bytes(b"ok")

    def log(self, text):
        self.messages.append(str(text))


def test_original_quality_copy_is_used_only_for_real_mp3():
    mp3 = _ProfileHost({"codec": "mp3", "bit_rate": 128000, "channels": 2})
    assert mp3._effective_mp3_profile("source") == (True, None, None)

    aac = _ProfileHost({"codec": "aac", "bit_rate": 128000, "channels": 2})
    copy_mode, bitrate, channels = aac._effective_mp3_profile("source")
    assert copy_mode is False
    assert bitrate == "128k"
    assert channels == 2
    assert any("кодек aac" in message for message in aac.messages)


def test_unknown_codec_falls_back_to_mp3_encode_instead_of_copy():
    host = _ProfileHost({})
    copy_mode, bitrate, channels = host._effective_mp3_profile("source")
    assert copy_mode is False
    assert bitrate == "96k"
    assert channels == 2
    assert any("не определён" in message for message in host.messages)


def test_stream_copy_failure_retries_same_track_with_libmp3lame(tmp_path):
    out = tmp_path / "01.mp3"
    source = tmp_path / "source.mp3"
    source.write_bytes(b"source")
    host = _SplitHost(out)
    book = Book(url="https://example.invalid/book", title="Book")
    track = Track(index=1, title="One", file="https://example.invalid/source.mp3")

    result = host._split_track(book, track, source)

    assert result == out
    assert len(host.commands) == 2
    assert ["-c:a", "copy"] == host.commands[0][host.commands[0].index("-c:a"):host.commands[0].index("-c:a") + 2]
    assert "libmp3lame" in host.commands[1]
    assert any("повторяю" in message for message in host.messages)


def test_real_aac_source_is_transcoded_to_valid_mp3_under_copy_preset(tmp_path):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("ffmpeg/ffprobe are not installed")

    source = tmp_path / "source.m4a"
    out = tmp_path / "01.mp3"
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:a", "aac", "-b:a", "96k", str(source),
        ],
        check=True,
    )

    class RealHost(DownloaderMixin):
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"

        def __init__(self):
            self.cancel_event = type("Cancel", (), {"wait": lambda self, _seconds: False})()
            self.messages = []

        def _check_cancel(self):
            return None

        def _track_path(self, _book, _track, mode=None):
            return out

        def log(self, text):
            self.messages.append(str(text))

    host = RealHost()
    book = Book(url="https://example.invalid/book", title="Book")
    track = Track(index=1, title="One", file="https://example.invalid/source.m4a")
    host._split_track(book, track, source)

    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1", str(out)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "mp3"
    assert any("кодек aac" in message for message in host.messages)
