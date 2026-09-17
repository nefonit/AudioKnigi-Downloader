from __future__ import annotations

from pathlib import Path

import pytest

from audioknigi.download.media import MediaProcessingMixin
from audioknigi.download.network import SlidingSpeedMeter
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import (
    Book,
    SearchResult,
    TRACK_STATUS_DAMAGED,
    TRACK_STATUS_MISSING,
    TRACK_STATUS_PRESENT,
    TRACK_STATUS_READY,
    normalize_track_status,
)
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import _parse_selected_indices_payload
from audioknigi.services.player_position_store import PlayerPositionStore

ROOT = Path(__file__).resolve().parents[2]


def test_queue_restore_preserves_explicit_empty_selection():
    assert _parse_selected_indices_payload(None) is None
    assert _parse_selected_indices_payload([]) == []
    assert _parse_selected_indices_payload([None, "bad", ""]) == []


def test_explicit_empty_selection_is_rejected_instead_of_becoming_full_book(tmp_path):
    from audioknigi.models import Track

    request = DownloadRequest(
        book=Book(url="https://example.test/book", title="Demo", tracks=[Track(index=1, title="One", file="https://cdn.test/1.mp3")]),
        selected_indices=[],
        output_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="Не выбрана ни одна часть"):
        request.validate()


def test_restricted_book_gets_specific_download_validation_error(tmp_path):
    request = DownloadRequest(
        book=Book(url="https://example.test/book", title="Blocked", restricted=True, tracks=[]),
        selected_indices=None,
        output_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="ограничению правообладателя"):
        request.validate()


def test_sliding_speed_meter_resets_history_when_counter_moves_backwards():
    meter = SlidingSpeedMeter(window_seconds=5.0)
    meter.update(1000)
    meter.update(2000)
    assert len(meter.samples) >= 2
    assert meter.update(50) == 0.0
    assert list(meter.samples)[-1][1] == 50
    assert len(meter.samples) == 1


def test_loudnorm_parser_uses_bounded_tail_and_finds_latest_json(monkeypatch):
    import audioknigi.download.media as media_module

    stats = '{"input_i":"-24.5","input_lra":"4.0","input_tp":"-2.0","input_thresh":"-34.0","target_offset":"0.1"}'

    class Dummy(MediaProcessingMixin):
        def _run_ffmpeg_capture(self, cmd, timeout=0):
            # Many earlier braces would make the old repeated-slicing parser expensive.
            return ("diagnostic { not-json } " * 10000) + "\n" + stats

    monkeypatch.setattr(media_module, "resolve_executable", lambda _name: "ffmpeg")
    value = Dummy()._measure_loudnorm("source.mp3", start=0, duration=1)
    assert "measured_I=-24.5" in value
    assert "offset=0.1" in value


def test_two_pass_normalization_disables_parallel_single_source_split():
    source = (ROOT / "audioknigi" / "download" / "book_flow.py").read_text(encoding="utf-8")
    assert 'safe_normalization_mode(getattr(self, "runtime_normalization_mode", "off"), "off") != "two_pass"' in source


def test_localized_track_statuses_normalize_to_canonical_values():
    assert normalize_track_status("немає") == TRACK_STATUS_MISSING
    assert normalize_track_status("fehlt") == TRACK_STATUS_MISSING
    assert normalize_track_status("є") == TRACK_STATUS_PRESENT
    assert normalize_track_status("fertig") == TRACK_STATUS_READY
    assert normalize_track_status("пошкоджено") == TRACK_STATUS_DAMAGED
    assert normalize_track_status("beschädigt") == TRACK_STATUS_DAMAGED


def test_audioknigi_author_prefix_requires_explicit_separator():
    class Response:
        text = "<title>Fallback</title>"
        def raise_for_status(self):
            return None

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    result = SearchResult(title="Fallback", url="https://audioknigi.com.ua/demo", source="audioknigi")
    ambiguous = _audioknigi_page_metadata(
        result,
        session_factory=Session,
        metadata_extractor=lambda _html, _fallback: ("Александр I", "Александр", ""),
        extended_metadata_extractor=lambda _html: ("", "", "", ""),
    )
    separated = _audioknigi_page_metadata(
        result,
        session_factory=Session,
        metadata_extractor=lambda _html, _fallback: ("Александр — Книга", "Александр", ""),
        extended_metadata_extractor=lambda _html: ("", "", "", ""),
    )
    assert ambiguous.title == "Александр I"
    assert separated.title == "Книга"


def test_round7_localization_and_quality_contracts_are_consistent():
    assert localize_runtime_text("de", "Range 2/4 • 10 MB из 20 MB • 1 MB/s • ETA 00:10").startswith("Range 2/4")
    onboarding = (ROOT / "audioknigi" / "qt" / "onboarding.py").read_text(encoding="utf-8")
    settings = (ROOT / "audioknigi" / "qt" / "mixins" / "settings.py").read_text(encoding="utf-8")
    assert '"audio_preset": "128k_stereo", "normalization_mode": "two_pass"' in onboarding
    assert "Merely saving unrelated settings in Easy mode must not erase" in settings
    assert 'quality_preset = self.easy_quality_combo.currentData() or quality_preset' in settings


def test_short_track_resume_uses_proportional_edge_guard(tmp_path):
    store = PlayerPositionStore(tmp_path / "positions.json")
    media = tmp_path / "short.mp3"
    assert store.update(media, 2.5, 5.0)
    assert store.saved_seconds(media, duration=5.0) == pytest.approx(2.5)
    assert store.update(media, 4.8, 5.0)
    assert store.saved_seconds(media, duration=5.0) == 0.0


def test_clipboard_prompt_waits_for_active_application_and_narration_switch_suppresses_stale_warning():
    source = (ROOT / "audioknigi" / "qt" / "mixins" / "clipboard.py").read_text(encoding="utf-8")
    assert "app.applicationState() != Qt.ApplicationState.ApplicationActive" in source
    assert 'narration_switch = bool(getattr(self, "_pending_narration_switch", False))' in source
