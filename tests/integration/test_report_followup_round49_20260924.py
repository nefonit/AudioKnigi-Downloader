from __future__ import annotations

import hashlib
import json
import math
import zipfile
from pathlib import Path

import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle
import audioknigi.download.source_analysis as source_analysis_module
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.models import Book, SearchResult
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.player_position_store import PlayerPositionStore


def test_support_settings_redacts_string_windows_path_with_spaces() -> None:
    cleaned = support_bundle.sanitized_settings({"output_dir": r"D:\Audio Books\My Collection"})
    assert cleaned["output_dir"] == "<configured-path>"
    assert "Audio Books" not in str(cleaned)
    assert "My Collection" not in str(cleaned)


def test_support_bundle_hashes_modern_nested_queue_book_url(tmp_path, monkeypatch) -> None:
    queue_file = tmp_path / "qt_queue.json"
    private_url = "https://example.invalid/private-modern-book"
    queue_file.write_text(
        json.dumps([
            {
                "id": "task-1",
                "title": "PRIVATE TITLE",
                "status": "Ожидает",
                "status_code": "pending",
                "attempts": 2,
                "request": {"book": {"url": private_url}},
            }
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(support_bundle, "QT_QUEUE_FILE", queue_file)

    target = support_bundle.create_support_bundle(tmp_path / "bundle.zip", settings={"language": "ru"})
    with zipfile.ZipFile(target) as archive:
        summary = json.loads(archive.read("diagnostics/queue.summary.json").decode("utf-8"))
        combined = b"\n".join(archive.read(name) for name in archive.namelist())

    expected = hashlib.sha256(private_url.encode("utf-8")).hexdigest()[:12]
    assert summary[0]["id"] == expected
    assert summary[0]["id"] != "row-1"
    assert private_url.encode("utf-8") not in combined
    assert b"PRIVATE TITLE" not in combined


def test_support_bundle_accepts_versioned_queue_wrapper(tmp_path, monkeypatch) -> None:
    queue_file = tmp_path / "qt_queue.json"
    queue_file.write_text(
        json.dumps({"version": 1, "items": [{"status_code": "pending", "attempts": 1}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(support_bundle, "QT_QUEUE_FILE", queue_file)
    target = support_bundle.create_support_bundle(tmp_path / "bundle.zip", settings={})
    with zipfile.ZipFile(target) as archive:
        summary = json.loads(archive.read("diagnostics/queue.summary.json").decode("utf-8"))
    assert summary == [{"id": "row-1", "status": "", "status_code": "pending", "attempts": 1}]


class _FallbackHost(SourceAnalysisMixin):
    cancel_event = None
    _book_identity_hints = staticmethod(BookAnalysisService._book_identity_hints)
    _identity_tokens = staticmethod(BookAnalysisService._identity_tokens)

    def _check_cancel(self) -> None:
        return None


def test_download_fallback_continues_past_unknown_narrator_to_exact_match(monkeypatch) -> None:
    original = Book(
        title="Book",
        author="Author",
        narrator="Exact Narrator",
        url="https://audioknigi.com.ua/audio-1",
    )
    # Search cards deliberately omit narrator metadata.  With equal scores the
    # z-unknown URL sorts first, reproducing the old early-return failure.
    results = [
        SearchResult(title="Book", author="Author", narrator="", url="https://knigavuhe.org/book/z-unknown/", source="knigavuhe"),
        SearchResult(title="Book", author="Author", narrator="", url="https://knigavuhe.org/book/a-exact/", source="knigavuhe"),
    ]
    monkeypatch.setattr(source_analysis_module, "search_knigavuhe_books", lambda *_a, **_k: results)

    class Provider:
        def fetch_book(self, url, *, cancel_event=None):
            narrator = "" if "z-unknown" in url else "Exact Narrator"
            return Book(title="Book", author="Author", narrator=narrator, url=url)

    monkeypatch.setattr(source_analysis_module, "provider_for_key", lambda _key: Provider())
    selected = _FallbackHost()._knigavuhe_fallback_candidate(original)
    assert selected is not None
    assert selected.url.endswith("/a-exact/")


def test_resume_guard_rejects_nan_duration() -> None:
    guard = PlayerPositionStore._resume_guard_seconds(float("nan"))
    assert math.isfinite(guard)
    assert guard == 3.0


def test_smart_format_log_explains_no_lossy_upsampling() -> None:
    class Dummy(MediaProcessingMixin):
        runtime_audio_preset = "128k_stereo"
        runtime_normalization_mode = "off"

        def __init__(self):
            self.messages: list[str] = []

        def _cached_probe_audio_info(self, _source):
            return {"codec": "mp3", "bit_rate": 64_000, "channels": 1}

        def log(self, message):
            self.messages.append(str(message))

    dummy = Dummy()
    copy_mode, bitrate, channels = dummy._effective_mp3_profile("source.mp3")
    assert (copy_mode, bitrate, channels) == (True, None, None)
    message = " ".join(dummy.messages)
    assert "не хуже" not in message
    assert "повышать" in message
    assert "без потери качества" in message


def test_direct_appsettings_constructor_normalizes_types_and_ranges() -> None:
    settings = settings_module.AppSettings({"scale": "150", "player_volume": 150, "minimize_to_tray": "false"})
    assert settings["scale"] == 150
    assert settings["player_volume"] == 100
    assert settings["minimize_to_tray"] is False


def test_easy_card_minimum_matches_declared_900px_window_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert "self.setMinimumSize(900, 620)" in source
    assert "card.setMinimumWidth(820)" in source
    assert "card.setMinimumWidth(860)" not in source
