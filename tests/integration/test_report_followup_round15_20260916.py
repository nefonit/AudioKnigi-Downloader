from __future__ import annotations

import base64
from pathlib import Path
from types import SimpleNamespace

from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.common import atomic_write_text
from audioknigi.i18n import localize_runtime_text
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.queue_service import task_from_dict


ROOT = Path(__file__).resolve().parents[2]


def test_stale_source_cleanup_removes_only_engine_owned_artifacts(tmp_path):
    owned = [
        tmp_path / "_source.mp3",
        tmp_path / "_source_01.mp3.part",
        tmp_path / "_source_02.mp3.part.seg000",
        tmp_path / "_repair_source_01.mp3.part.segments.json",
    ]
    keep = [
        tmp_path / "_source of wisdom.mp3",
        tmp_path / "_source_notes.mp3",
        tmp_path / "normal.mp3",
    ]
    for item in [*owned, *keep]:
        item.write_bytes(b"x")

    class Flow(BookFlowMixin):
        def _book_folder(self, _book, create=False):
            assert create is False
            return tmp_path

        def log(self, _message):
            pass

    removed = Flow()._clear_stale_source_downloads(SimpleNamespace())
    assert removed == len(owned)
    assert all(not item.exists() for item in owned)
    assert all(item.exists() for item in keep)


def test_atomic_write_text_retries_transient_permission_error(monkeypatch, tmp_path):
    import audioknigi.download.common as common

    target = tmp_path / "book_info.txt"
    real_replace = common.os.replace
    calls = {"count": 0}

    def flaky_replace(src, dst):
        calls["count"] += 1
        if calls["count"] < 3:
            raise PermissionError("sharing violation")
        return real_replace(src, dst)

    monkeypatch.setattr(common.os, "replace", flaky_replace)
    monkeypatch.setattr(common.time, "sleep", lambda _seconds: None)
    atomic_write_text(target, "ok")
    assert target.read_text(encoding="utf-8") == "ok"
    assert calls["count"] == 3


def test_legacy_queue_base64_cover_and_normalize_audio_are_preserved(tmp_path):
    payload = b"\x89PNG\r\n\x1a\nlegacy-cover"
    task = task_from_dict(
        {
            "url": "https://knigavuhe.org/book/test/",
            "title": "Legacy",
            "output_dir": str(tmp_path),
            "cover_cache": base64.b64encode(payload).decode("ascii"),
            "cover_cache_mime": "image/png",
            "normalize_audio": True,
        }
    )
    assert task.request.book.cover_cache == (payload, "image/png")
    assert task.request.normalization_mode == "single"


def test_full_mp3_queue_parts_count_is_one_file():
    source = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    block = source[source.index("def _queue_parts_count"):source.index("def _queue_row_summary")]
    assert 'download_mode", "selected"' in block
    assert '== "full_mp3"' in block
    assert "return 1" in block


def test_range_runtime_translation_accepts_flexible_bullet_spacing():
    text = "Range 2/4  •   1 MB из 10 MB   •  2 MB/s •   ETA 00:04"
    assert localize_runtime_text("en", text) == "Range 2/4 • 1 MB of 10 MB • 2 MB/s • ETA 00:04"


def test_incomplete_loudnorm_stats_fall_back_instead_of_raising():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    assert '"Неполная статистика loudnorm первого прохода."' not in source
    assert "использую безопасную однопроходную нормализацию" in source
    block = source[source.index("required = ("):source.index("def _normalization_filter_for_track")]
    assert "return base" in block


def test_clipboard_suppression_compares_canonical_supported_urls():
    source = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    block = source[source.index("suppress = str(self._suppress_clipboard_prompt_text"):]
    assert "same_clipboard_url = text == suppress" in block
    assert "normalize_supported_url(text) == normalize_supported_url(suppress)" in block


def test_history_delete_reloads_rows_to_refresh_accessibility_descriptions():
    source = (ROOT / "audioknigi/qt/mixins/history.py").read_text(encoding="utf-8")
    block = source[source.index("def history_delete"):source.index("def export_library")]
    assert "self._load_history()" in block
    assert "history_table.removeRow(row)" not in block


def test_duration_probe_cancel_kills_registered_children_before_pool_wait():
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    assert "def _cancel_duration_probe_processes" in source
    block = source[source.index("def _populate_missing_track_durations"):source.index("@staticmethod", source.index("def _populate_missing_track_durations"))]
    assert "self._cancel_duration_probe_processes()" in block
    assert block.index("self._cancel_duration_probe_processes()") < block.index("pool.shutdown(wait=True")


def test_duration_probe_registry_kills_live_processes():
    service = BookAnalysisService()

    class FakeProc:
        def __init__(self):
            self.killed = False

        def poll(self):
            return None

        def kill(self):
            self.killed = True

    proc = FakeProc()
    service._register_duration_probe_process(proc)  # type: ignore[arg-type]
    service._cancel_duration_probe_processes()
    assert proc.killed is True
    service._unregister_duration_probe_process(proc)  # type: ignore[arg-type]
