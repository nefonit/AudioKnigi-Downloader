from __future__ import annotations

import json
from pathlib import Path

import pytest

from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.models import Book, Track
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider
from audioknigi.services import library_service
from audioknigi.services.queue_service import _book_to_dict

ROOT = Path(__file__).resolve().parents[2]


def test_ffmpeg_workers_never_inherit_parent_stdin():
    source = (ROOT / "audioknigi" / "download" / "media.py").read_text(encoding="utf-8")
    run_block = source[source.index("def _run_ffmpeg("):source.index("def _probe_audio_info(")]
    assert run_block.count("stdin=subprocess.DEVNULL") >= 2
    loudnorm = source[source.index("def _measure_loudnorm("):source.index("def _normalization_filter_for_track(")]
    assert '"-nostdin"' in loudnorm


def test_parallel_split_reports_progress_inside_same_lock():
    source = (ROOT / "audioknigi" / "download" / "book_flow.py").read_text(encoding="utf-8")
    block = source[source.index("def split_one(tr):"):source.index("with ThreadPoolExecutor(max_workers=2)")]
    lock_pos = block.index("with progress_lock:")
    stage_pos = block.index("self.set_stage(3, split_text)")
    report_pos = block.index("report(split_text)")
    # The UI/report calls must remain indented inside the progress lock so worker
    # completion messages cannot arrive out of order and move progress backwards.
    lines = block[lock_pos:report_pos].splitlines()
    lock_indent = len(lines[0]) - len(lines[0].lstrip())
    stage_line = next(line for line in lines if "self.set_stage(3, split_text)" in line)
    report_line = next(line for line in block[lock_pos:].splitlines() if "report(split_text)" in line)
    assert len(stage_line) - len(stage_line.lstrip()) > lock_indent
    assert len(report_line) - len(report_line.lstrip()) > lock_indent


def test_secret_redaction_does_not_hide_unrelated_token_settings():
    assert _is_secret_key("token")
    assert _is_secret_key("oauth_token")
    assert _is_secret_key("abs_api_key")
    assert not _is_secret_key("folder_tokens")
    assert not _is_secret_key("tokenize_words")


def test_runtime_progress_and_duration_messages_are_fully_localized():
    text = "Скачано 15 MB из 100 MB  •  2 MB/s  •  ETA 00:42"
    assert localize_runtime_text("en", text) == "Downloaded 15 MB of 100 MB • 2 MB/s • ETA 00:42"
    assert localize_runtime_text("de", text) == "Heruntergeladen 15 MB von 100 MB • 2 MB/s • ETA 00:42"
    assert localize_runtime_text("uk", "Определена длительность частей: 2/4") == "Визначено тривалість частин: 2/4"


def test_stage_messages_use_stable_message_ids():
    assert tr("en", "stage_playlist_refresh") == "Refreshing playlist"
    assert tr("de", "stage_source_download") == "Quelldatei wird heruntergeladen"
    source = (ROOT / "audioknigi" / "download" / "book_flow.py").read_text(encoding="utf-8")
    assert '"stage_playlist_refresh"' in source
    assert '"stage_source_download"' in source


def test_restore_and_present_terminology_is_consistent():
    assert ui_text("en", "Восстановить") == "Restore"
    assert ui_text("de", "Восстановить") == "Wiederherstellen"
    assert ui_text("en", "есть") == "present"


def test_backup_multiline_runtime_translation_accepts_multiple_lines():
    raw = "Резервная копия создана:\nC:/Backup/file.zip\nsettings, history"
    out = localize_runtime_text("en", raw)
    assert out == "Backup created:\nC:/Backup/file.zip\nsettings, history"


def test_queue_model_dataclasses_are_serialized_with_tracks():
    book = Book(url="https://example.invalid/book", title="Book", tracks=[Track(index=1, title="One", file="https://example.invalid/1.mp3")])
    payload = _book_to_dict(book)
    assert payload["tracks"] and payload["tracks"][0]["index"] == 1


def test_provider_fetch_contract_delegates_to_analysis_service(monkeypatch):
    from audioknigi.services.book_analysis_service import BookAnalysisService

    seen = []
    expected = Book(url="https://knigavuhe.org/book/1", title="Book")

    def fake_analyze(self, url):
        seen.append(url)
        return expected

    monkeypatch.setattr(BookAnalysisService, "analyze", fake_analyze)
    assert KnigavuheProvider().fetch_book("https://knigavuhe.org/book/1") is expected
    assert PoleKnigProvider().fetch_book("https://poleknig.com/book/1") is expected
    assert len(seen) == 2


def test_history_lock_is_shared_by_engine_and_library_service():
    import audioknigi.download_engine as engine
    assert engine.HISTORY_LOCK is library_service.HISTORY_LOCK


def test_backup_uses_memory_snapshots_instead_of_zipfile_write(tmp_path, monkeypatch):
    source = tmp_path / "settings.json"
    source.write_text('{"ok": true}', encoding="utf-8")
    monkeypatch.setattr(library_service, "BACKUP_MEMBERS", {"settings.json": source})
    target = tmp_path / "backup.zip"
    library_service.create_backup(target)
    import zipfile
    with zipfile.ZipFile(target) as archive:
        assert json.loads(archive.read("settings.json").decode("utf-8")) == {"ok": True}
        manifest = json.loads(archive.read("backup_manifest.json").decode("utf-8"))
        assert manifest["includes"] == ["settings.json"]
    source_text = (ROOT / "audioknigi" / "services" / "library_service.py").read_text(encoding="utf-8")
    assert "archive.write(source" not in source_text


def test_cover_fetch_rejects_non_http_schemes_without_network(monkeypatch):
    import audioknigi.cover_fetch as module

    def explode():
        raise AssertionError("network session must not be created for data/file URLs")

    monkeypatch.setattr(module, "get_http_session", explode)
    assert fetch_cover_bytes("data:image/png;base64,AAAA") is None
    assert fetch_cover_bytes("file:///tmp/cover.jpg") is None


def test_accessibility_worker_path_never_calls_widget_window():
    source = (ROOT / "audioknigi" / "qt" / "accessibility.py").read_text(encoding="utf-8")
    announce = source[source.index("def announce("):source.index("class AccessibleAnnouncer")]
    assert "widget.window()" not in announce
    assert "_DEFAULT_ANNOUNCER_REF" in announce


def test_player_tab_has_alt_shortcut_too():
    source = (ROOT / "audioknigi" / "qt" / "mixins" / "accessibility_ui.py").read_text(encoding="utf-8")
    marker = "for number, tab_index in enumerate([self.TAB_BOOK, self.TAB_SEARCH, self.TAB_QUEUE, self.TAB_HISTORY, self.TAB_SETTINGS, self.TAB_PLAYER], start=1):"
    assert source.count(marker) >= 2


def test_version_and_runtime_stage_41240():
    from audioknigi.metadata import APP_VERSION
    from audioknigi.qt import QT_RUNTIME_STAGE
    assert APP_VERSION == "4.12.42"
    assert QT_RUNTIME_STAGE == "qt-only-4.12.42"
