from __future__ import annotations

import http.server
import json
from pathlib import Path
import re
import shutil
import socketserver
import subprocess
import threading

import pytest

from audioknigi.download_engine import DownloadService
from audioknigi.models import Book, Track
from audioknigi.qt.feature_parity import CRITICAL_FUNCTIONAL_KEYS, PARITY_ITEMS, critical_functional_parity_complete
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services import library_service


ROOT = Path(__file__).resolve().parents[1]
QT = ROOT / "audioknigi" / "qt" / "main_window.py"


def test_phase9_critical_functional_parity_matrix_is_complete_and_honest():
    assert critical_functional_parity_complete()
    native = {item.key for item in PARITY_ITEMS if item.status == "native"}
    assert CRITICAL_FUNCTIONAL_KEYS <= native
    assert "full_mp3" in native
    deferred = {item.key for item in PARITY_ITEMS if item.status == "deferred"}
    assert {"event_voice_sounds", "localization", "cover_cards"} <= deferred
    assert any(item.status == "intentional-difference" for item in PARITY_ITEMS)


def test_phase9_qt_ui_contains_advanced_download_settings_and_abs_without_legacy_ui():
    text = QT.read_text(encoding="utf-8")
    for needle in (
        '"naming_mode"', '"audio_preset"', '"normalization_mode"',
        '"segment_count"', '"segment_threshold"', '"auto_chunk_threshold"',
        'identifier="bandwidth_limit"', 'identifier="embed_tags"', 'identifier="save_sidecars"',
        'identifier="delete_source"', 'identifier="parallel_processing"', 'identifier="use_templates"',
        'identifier="folder_template"', 'identifier="track_template"', 'identifier="abs_enabled"',
        'identifier="abs_url"', 'identifier="abs_api_key"', 'identifier="abs_library_id"',
        'def _settings_from_ui(self) -> dict:', 'audiobookshelf_get_libraries',
    ):
        assert needle in text
    import_lines = '\n'.join(line for line in text.splitlines() if line.lstrip().startswith(('import ', 'from ')))
    for forbidden in ('ttk', 'tkinter', 'pygame', 'pystray'):
        assert forbidden not in import_lines


def test_phase9_history_backup_recovery_queue_and_track_actions_are_wired():
    text = QT.read_text(encoding="utf-8")
    for needle in (
        '"history_open_folder"', '"history_redownload"', '"history_delete"',
        '"history_export_json"', '"history_export_csv"', '"history_clear"',
        'identifier="create_backup"', 'identifier="restore_backup"', 'identifier="continue_unfinished"',
        'identifier="download_full_mp3"', 'def start_full_mp3(self):', 'service.download_full_mp3(self.request)',
        '"queue_add_url"', '"queue_clear"', 'def queue_add_url(self):', 'def clear_queue(self):',
        'def _show_track_context_menu(self, pos):', 'def download_selected_track_only(self):',
        'def continue_unfinished(self):', 'scan_unfinished(output)', 'self._download_after_analysis = True',
    ):
        assert needle in text


def test_phase9_narration_clipboard_and_legacy_hotkey_parity_are_present():
    text = QT.read_text(encoding="utf-8")
    for needle in (
        'identifier="narration_variant"', 'identifier="narration_first_available"', 'def _update_narration_combo(self, book: Book):',
        'def select_first_available_narration(self):',
        'def _narration_selected(self, index: int):', 'self._known_narration_variants',
        'identifier="clipboard_auto"', 'def _application_state_changed(self, state):',
        'QShortcut(QKeySequence("Ctrl+D")', 'QShortcut(QKeySequence("Ctrl+Q")',
        'QShortcut(QKeySequence("Ctrl+H")', 'QShortcut(QKeySequence("Escape")',
    ):
        assert needle in text


def test_library_service_scan_export_backup_restore_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    app_dir = tmp_path / "app"
    output = tmp_path / "books"
    settings = app_dir / "settings.json"
    history = app_dir / "history.json"
    positions = app_dir / "player_positions.json"
    queue = app_dir / "qt_queue.json"
    app_dir.mkdir()
    output.mkdir()

    monkeypatch.setattr(library_service, "APP_DIR", app_dir)
    monkeypatch.setattr(library_service, "SETTINGS_FILE", settings)
    monkeypatch.setattr(library_service, "HISTORY_FILE", history)
    monkeypatch.setattr(library_service, "PLAYER_POSITIONS_FILE", positions)
    monkeypatch.setattr(library_service, "QT_QUEUE_FILE", queue)
    monkeypatch.setattr(library_service, "BACKUP_MEMBERS", {
        "settings.json": settings, "history.json": history,
        "player_positions.json": positions, "qt_queue.json": queue,
    })

    settings.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
    rows = [{"title": "Book", "url": "https://knigavuhe.org/book/1", "parts": 2, "folder": str(output / "Book")}]
    history.write_text(json.dumps(rows), encoding="utf-8")
    positions.write_text(json.dumps({"x": {"position": 10}}), encoding="utf-8")
    queue.write_text(json.dumps([]), encoding="utf-8")

    exported_json = library_service.export_history(rows, tmp_path / "library.json", "json")
    exported_csv = library_service.export_history(rows, tmp_path / "library.csv", "csv")
    assert exported_json.exists() and "Book" in exported_json.read_text(encoding="utf-8")
    assert exported_csv.exists() and "Book" in exported_csv.read_text(encoding="utf-8-sig")

    book_dir = output / "Book"
    book_dir.mkdir()
    (book_dir / "resume.json").write_text(json.dumps({
        "url": "https://knigavuhe.org/book/1", "title": "Book", "selected_indices": [1, 2],
        "audio_preset": "64k_mono", "normalization_mode": "off",
    }), encoding="utf-8")
    unfinished = library_service.scan_unfinished(output)
    assert len(unfinished) == 1 and unfinished[0].selected_indices == [1, 2]

    backup = library_service.create_backup(tmp_path / "backup.zip")
    settings.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
    history.write_text("[]", encoding="utf-8")
    restored = library_service.restore_backup(backup)
    assert set(restored) == {"settings.json", "history.json", "player_positions.json", "qt_queue.json"}
    assert json.loads(settings.read_text(encoding="utf-8"))["theme"] == "dark"
    assert json.loads(history.read_text(encoding="utf-8"))[0]["title"] == "Book"


def test_library_service_rejects_malformed_backup_before_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import zipfile
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    settings = app_dir / "settings.json"
    settings.write_text(json.dumps({"keep": True}), encoding="utf-8")
    monkeypatch.setattr(library_service, "APP_DIR", app_dir)
    monkeypatch.setattr(library_service, "SETTINGS_FILE", settings)
    monkeypatch.setattr(library_service, "BACKUP_MEMBERS", {"settings.json": settings})
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("settings.json", "[]")
    with pytest.raises(ValueError):
        library_service.restore_backup(archive)
    assert json.loads(settings.read_text(encoding="utf-8")) == {"keep": True}



def test_phase9_accessibility_audit_covers_new_interactive_parity_controls():
    text = (ROOT / "audioknigi" / "qt" / "accessibility_audit.py").read_text(encoding="utf-8")
    for ident in (
        "paste_book_url", "continue_unfinished", "download_full_mp3", "narration_variant",
        "narration_first_available", "queue_add_url", "queue_clear", "history_open_folder",
        "history_redownload", "history_export_json", "history_export_csv", "history_clear",
        "naming_mode", "audio_preset", "normalization_mode", "bandwidth_limit",
        "abs_url", "abs_api_key", "abs_library_id", "abs_test", "create_backup", "restore_backup",
    ):
        assert f'"{ident}"' in text


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg required to generate a valid MP3 fixture")
def test_phase9_full_mp3_download_is_headless_and_real(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import audioknigi.download_engine as download_engine

    serve = tmp_path / "serve"
    output = tmp_path / "output"
    serve.mkdir()
    output.mkdir()
    source = serve / "whole.mp3"
    subprocess.run(
        [shutil.which("ffmpeg") or "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=1.2", "-c:a", "libmp3lame",
         "-b:a", "64k", str(source)],
        check=True,
    )

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def translate_path(self, path):
            return str(serve / path.split("?", 1)[0].lstrip("/"))

    server = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/whole.mp3"
    monkeypatch.setattr(download_engine, "HISTORY_FILE", tmp_path / "history.json")
    book = Book(
        url="https://knigavuhe.org/book/phase9-full/",
        title="Phase 9 Full",
        author="Test",
        tracks=[Track(index=1, title="One", file=url), Track(index=2, title="Two", file=url)],
    )
    request = DownloadRequest(book=book, selected_indices=[1, 2], output_dir=output)
    try:
        result = DownloadService(
            settings={"embed_tags": False, "segment_count": "1"}
        ).download_full_mp3(request)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.target_file is not None
    assert result.target_file.name == "Phase 9 Full.mp3"
    assert result.target_file.is_file() and result.target_file.stat().st_size > 0
    assert result.folder == result.target_file.parent
    assert (tmp_path / "history.json").exists()


def test_migration_stage_is_phase9_or_later():
    text = (ROOT / "audioknigi" / "qt" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'QT_MIGRATION_STAGE = "phase-(\d+)"', text)
    assert match and int(match.group(1)) >= 9
