from __future__ import annotations

import json
import zipfile
from pathlib import Path

from audioknigi.download.probe import ProbeMixin
from audioknigi.models import Book, Track
from audioknigi.services import library_service, source_health_service

ROOT = Path(__file__).resolve().parents[2]


def test_segmented_workers_rely_on_atomic_queue_get_not_empty_precheck():
    source = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    block = source[source.index("def worker(worker_id)"):source.index("self.log(", source.index("def worker(worker_id)"))]
    assert "jobs.empty()" not in block
    assert "jobs.get_nowait()" in block
    assert "except queue.Empty:" in block


def test_support_bundle_privacy_path_runs_embedded_regex_redaction_once():
    source = (ROOT / "audioknigi/diagnostics/support_bundle.py").read_text(encoding="utf-8")
    block = source[source.index("def _privacy_path"):source.index("def _sanitize_log_bytes")]
    for token in (
        "_EMBEDDED_DRIVE_FILE_RE.sub",
        "_EMBEDDED_UNC_FILE_RE.sub",
        "_EMBEDDED_DRIVE_PATH_RE.sub",
        "_EMBEDDED_UNC_PATH_RE.sub",
        "_EMBEDDED_POSIX_FILE_RE.sub",
        "_EMBEDDED_POSIX_PATH_RE.sub",
    ):
        assert block.count(token) == 1


def test_unknown_size_and_duration_still_reserve_disk_space(tmp_path):
    class Harness(ProbeMixin):
        runtime_audio_preset = "copy"

        def _book_folder(self, _book, *, create=True):
            return tmp_path

    track = Track(index=1, title="Unknown", file="https://example.invalid/a.mp3")
    book = Book(url="https://example.invalid/book", title="Book", tracks=[track], remote_size=0)
    required = Harness()._estimate_required_space(book)
    assert required >= 30 * 1024 * 1024


def test_source_health_403_is_reachable_but_blocked(monkeypatch):
    class Response:
        status_code = 403

        def close(self):
            pass

    class Session:
        def __init__(self):
            self.headers = {}
            self.trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(source_health_service.requests, "Session", Session)
    item = source_health_service._probe_source("example.invalid", timeout=1.0)
    assert item.reachable is True
    assert item.blocked is True
    assert item.status_code == 403
    assert item.error == ""


def test_backup_restore_accepts_legacy_wrapped_queue(tmp_path):
    for wrapper_key in ("items", "queue"):
        backup = tmp_path / f"legacy-{wrapper_key}.zip"
        with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("qt_queue.json", json.dumps({wrapper_key: [{"id": "demo"}]}))
        payloads = library_service._validated_backup_payloads(backup)
        assert payloads["qt_queue.json"] == [{"id": "demo"}]


def test_playwright_prefers_browser_playlist_body_before_http_fallback():
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    start = source.index("def _analyze_audioknigi_playwright")
    block = source[start:source.index("def _remote_size", start)]
    assert "captured_responses" in block
    assert "browser_response.body()" in block
    assert "if not playlist_text:" in block
    assert block.index("browser_response.body()") < block.index("browser.close()")
    assert block.index("browser.close()") < block.index("session.get(playlist_url")


def test_transient_message_boxes_are_scheduled_for_cleanup():
    source = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    start = source.index("def _show_message")
    end = source.index("@Slot(bool)", start)
    block = source[start:end]
    assert block.count("box.deleteLater()") >= 2
    assert block.count("result = box.standardButton(box.clickedButton())") >= 2


def test_reported_runtime_exact_duplicate_is_not_present():
    path = ROOT / "audioknigi/locales/runtime_exact.json"
    text = path.read_text(encoding="utf-8")
    assert text.count('"Проверить системный звук"') == 1

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f"duplicate JSON key: {key!r}"
            result[key] = value
        return result

    json.loads(text, object_pairs_hook=no_duplicates)
