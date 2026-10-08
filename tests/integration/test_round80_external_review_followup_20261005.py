from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.config.settings import AppSettings
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download_engine import _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track

ROOT = Path(__file__).resolve().parents[2]


def test_missing_source_diagnostic_survives_malformed_index(monkeypatch, tmp_path):
    track = Track(index=0, title="Prologue", file="", local_status="missing")
    book = Book(url="https://example.invalid/book", title="Demo", tracks=[track])

    class Harness(BookFlowMixin):
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"
        runtime_embed_tags = False
        runtime_save_sidecars = True
        runtime_delete_source = True

        def _check_cancel(self):
            pass

        def _scan_book_files(self, current, create_folder=False):
            # Simulate an unexpected stale/malformed model mutation after the
            # track has already been selected. The diagnostic must still stay
            # at the useful BookFlow boundary rather than falling through.
            current.tracks[0].index = None

        def _check_disk_space(self, *_args, **_kwargs):
            return True

        def _write_resume_manifest(self, *_args, **_kwargs):
            pass

        def _book_folder(self, *_args, **_kwargs):
            return tmp_path

        def _log_book_flow(self, *_args, **_kwargs):
            pass

        def log(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr("audioknigi.download.book_flow.resolve_executable", lambda _name: "/ffmpeg")
    with pytest.raises(RuntimeError, match=r"отсутствует адрес аудиофайла для частей: 1"):
        Harness()._process_book_once(book, [0])


def test_segmented_tiny_payload_never_creates_negative_or_empty_ranges(tmp_path):
    seen = []

    class Harness(NetworkDownloadMixin):
        runtime_segment_count = "2"
        runtime_bandwidth_limit = 0.0
        runtime_auto_chunk_min_kbytes_per_sec = 256
        cancel_event = None

        def _check_cancel(self):
            pass

        def _download_segment(self, _url, seg_path, start, end, _referer, progress_cb, peer_abort_event=None):
            seen.append((start, end))
            assert 0 <= start <= end
            payload = b"x" * (end - start + 1)
            Path(seg_path).write_bytes(payload)
            progress_cb(len(payload), force=True)
            return len(payload)

        def _cancel_active_network_io(self):
            pass

        def set_progress(self, *_args):
            pass

        def set_status(self, *_args):
            pass

        def log(self, *_args):
            pass

        def record_transfer_metrics(self, *_args):
            pass

    target = tmp_path / "tiny.bin"
    result = Harness()._download_segmented("https://example.invalid/tiny", target, "", 1, 8)
    assert Path(result).read_bytes() == b"x"
    assert seen == [(0, 0)]


def test_headless_missing_media_callback_filters_bool_and_malformed_indices():
    captured = []

    def callback(indices, detail, allow_skip):
        captured.append((indices, detail, allow_skip))
        return "skip"

    dummy = SimpleNamespace(callbacks=SimpleNamespace(missing_media=callback))
    decision = _DownloadEngine._ask_missing_media_action(
        dummy,
        [True, False, "3", "bad", -1, 0, 2],
        detail="expired",
        allow_skip=True,
    )
    assert decision == "skip"
    assert captured == [([0, 2, 3], "expired", True)]


def test_queue_reanalysis_preserves_zero_index_in_source_contract():
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    start = source.index("if self._queue_reanalyze_task_id and enabled:")
    block = source[start:source.index("def ", start + 10)]
    assert 'safe_int(getattr(track, "index", None), -1)) >= 0' in block
    assert 'safe_int(value, -1)) >= 0 and index in valid' in block
    assert 'safe_int(getattr(track, "index", None), 0)) > 0' not in block


def test_probe_strict_selection_validation_is_an_intentional_disk_space_guard():
    from audioknigi.download.probe import ProbeMixin

    book = Book(url="https://example.invalid/book", title="Book")
    with pytest.raises(ValueError, match="Invalid selected track index"):
        ProbeMixin()._estimate_required_space(book, [True])
    with pytest.raises(ValueError, match="Invalid selected track index"):
        ProbeMixin()._estimate_required_space(book, [1.5])


def test_settings_legacy_alias_membership_remains_canonical_storage_contract():
    settings = AppSettings({"normalization_mode": "single", "auto_chunk_min_kbytes_per_sec": 512})
    assert settings["normalize_audio"] is True
    assert settings.get("auto_chunk_min_kbps") == 512
    assert "normalize_audio" not in settings
    assert "auto_chunk_min_kbps" not in settings


def test_i18n_exact_precedes_regex_and_regex_precedes_prefix():
    exact = "Анализирую audioknigi.com.ua быстрым HTTP-способом…"
    assert localize_runtime_text("en", exact) == "Analyzing audioknigi.com.ua using the fast HTTP method…"
    assert localize_runtime_text("en", "История обновлена: 12 записей.") == "History refreshed: 12 entries."
    assert localize_runtime_text("en", "Скачано 15 MB из 100 MB") == "Downloaded 15 MB of 100 MB"


def test_windows_directory_redaction_stays_privacy_first_but_file_tail_is_preserved():
    assert _privacy_path(r"C:\Audio\My Book for Alice", collapse_whole_path=False) == "<configured-path>"
    assert _privacy_path(
        r"C:\Audio\Book\chapter.mp3 failed to download because timeout",
        collapse_whole_path=False,
    ) == "<configured-path> failed to download because timeout"


def test_source_health_proxy_policy_matches_global_http_policy():
    core = (ROOT / "audioknigi/core.py").read_text(encoding="utf-8")
    health = (ROOT / "audioknigi/services/source_health_service.py").read_text(encoding="utf-8")
    assert "session.trust_env = False" in core
    assert "session.trust_env = False" in health
