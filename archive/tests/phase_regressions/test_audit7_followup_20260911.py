from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from audioknigi.core import Cancelled, extract_extended_metadata_from_html
from audioknigi.downloader import DownloaderMixin
from audioknigi.i18n import ui_text

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_smart_format_mp3_codec_is_case_and_space_insensitive():
    class Host(DownloaderMixin):
        runtime_audio_preset = "96k_mono"
        runtime_normalization_mode = "off"

        def _cached_probe_audio_info(self, _path):
            return {"codec": " MP3 ", "bit_rate": 64_000, "channels": 1}

    copy_mode, bitrate, channels = Host()._effective_mp3_profile(Path("source.mp3"))
    assert copy_mode is True
    assert bitrate is None
    assert channels is None


def test_extended_json_ld_ignores_website_metadata_before_book():
    payload = {
        "@graph": [
            {
                "@type": "WebSite",
                "name": "Example portal",
                "description": "Description of the whole website",
            },
            {
                "@type": "AudioBook",
                "name": "The Book",
                "description": "Actual book description",
                "genre": ["Fantasy", "Adventure"],
                "datePublished": "2024-03-01",
                "readBy": {"@type": "Person", "name": "Reader Name"},
            },
        ]
    }
    html = '<script type="application/ld+json">' + json.dumps(payload) + "</script>"
    description, narrator, genre, year = extract_extended_metadata_from_html(html)
    assert description == "Actual book description"
    assert narrator == "Reader Name"
    assert genre == "Fantasy, Adventure"
    assert year == "2024"


def test_http_200_cloudflare_interstitial_is_detected_without_broad_false_positive():
    host = DownloaderMixin()
    assert host._looks_like_protection("<title>Just a moment...</title><div class='cf-chl-x'>", 200)
    assert not host._looks_like_protection("This site explains how Cloudflare works and mentions captcha.", 200)


def test_segmented_download_sanitizes_oversized_resume_before_aggregate():
    source = text("audioknigi/downloader.py")
    block = source[source.index("def _download_segmented"):source.index("def _download_with_resume", source.index("def _download_segmented"))]
    aggregate_pos = block.index("aggregate = 0")
    unlink_pos = block.index("seg.unlink(missing_ok=True)")
    meter_pos = block.index("meter.update(aggregate)")
    assert unlink_pos < meter_pos
    assert aggregate_pos < meter_pos
    assert "if task_count < 2" not in block


def test_cloudflare_bootstrap_has_ipv4_and_ipv6_addresses():
    from audioknigi.network_dns import CLOUDFLARE_BOOTSTRAP_IPS

    assert "1.1.1.1" in CLOUDFLARE_BOOTSTRAP_IPS
    assert "1.0.0.1" in CLOUDFLARE_BOOTSTRAP_IPS
    assert "2606:4700:4700::1111" in CLOUDFLARE_BOOTSTRAP_IPS
    assert "2606:4700:4700::1001" in CLOUDFLARE_BOOTSTRAP_IPS


def test_knigavuhe_reader_hydration_uses_typed_cancelled_and_does_not_swallow_it():
    source = text("audioknigi/knigavuhe.py")
    block = source[source.index("def _hydrate_narration_variant_readers"):source.index("def parse_book_html", source.index("def _hydrate_narration_variant_readers"))]
    assert 'raise Cancelled("Операция отменена пользователем")' in block
    assert "except Cancelled:\n                raise" in block
    assert 'raise RuntimeError("cancelled")' not in block


def test_queue_retry_uses_retry_translation_not_text_editor_redo():
    source = text("audioknigi/qt/main_window.py")
    assert 'self.queue_retry_button = QPushButton(self._l("Повторить задачу"), page)' in source
    assert ui_text("en", "Повторить задачу") == "Retry task"
    # The text editor context menu intentionally keeps the standard Redo term.
    assert ui_text("en", "Повторить") == "Redo"


def test_track_file_missing_status_remains_contextualized():
    source = text("audioknigi/qt/track_model.py")
    assert 'return ui_text(_lang(), "нет (файл)")' in source
    assert ui_text("en", "нет (файл)") == "missing"
    assert ui_text("de", "нет (файл)") == "fehlt"
