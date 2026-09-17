from __future__ import annotations

import json
from pathlib import Path
import pytest

from audioknigi import core
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.models import Book, SearchResult, Track
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import scan_unfinished


ROOT = Path(__file__).resolve().parents[2]


def test_persist_browser_cookies_accepts_legacy_headers(monkeypatch):
    captured = {}

    def fake(cookies, headers=None):
        captured["cookies"] = cookies
        captured["headers"] = headers

    monkeypatch.setattr(core, "persist_browser_session", fake)
    core.persist_browser_cookies([{"name": "a", "value": "b"}], {"User-Agent": "UA"})
    assert captured["headers"] == {"User-Agent": "UA"}


def test_deliberate_settings_save_preserves_explicit_125_percent(tmp_path):
    path = tmp_path / "settings.json"
    assert save_app_settings({"scale": 125}, path)
    saved = load_json(path, {})
    assert saved["scale"] == 125
    assert saved[core.UI_SCALE_MIGRATION_KEY] is True


def test_download_request_reports_invalid_track_index_cleanly(tmp_path):
    book = Book(url="https://example.invalid", title="Book", tracks=[Track(index=None, title="x", file="x")])  # type: ignore[arg-type]
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    with pytest.raises(ValueError, match="Некорректный индекс части"):
        request.validate()


def test_loudnorm_nonfinite_statistics_fall_back_to_single_pass(monkeypatch):
    class Dummy(MediaProcessingMixin):
        pass

    dummy = Dummy()
    monkeypatch.setattr("audioknigi.download.media.resolve_executable", lambda _name: "ffmpeg")
    monkeypatch.setattr(
        dummy,
        "_run_ffmpeg_capture",
        lambda *_args, **_kwargs: '{"input_i":"-inf","input_lra":"0.0","input_tp":"-inf","input_thresh":"-70.0","target_offset":"0.0"}',
    )
    value = dummy._measure_loudnorm("silent.wav")
    assert value == "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json"


def test_support_bundle_windows_path_is_redacted_and_tail_is_valid_utf8(tmp_path):
    # Import inside the test to preserve the package's normal import order.
    from audioknigi.diagnostics import support_bundle

    assert support_bundle._privacy_path(r"D:\\Audiobooks\\Private\\{Book_Title}") == "<configured-path>"
    path = tmp_path / "application.log"
    path.write_bytes(b"valid line\ntruncated \xd0")
    tail = support_bundle._tail(path, max_bytes=512_000)
    assert tail.decode("utf-8") == "valid line\ntruncated "


def test_scan_unfinished_accepts_utf8_bom_manifest(tmp_path):
    folder = tmp_path / "Book"
    folder.mkdir()
    payload = {"url": "https://knigavuhe.org/book/sample/", "selected_indices": None}
    (folder / "resume.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8-sig")
    found = scan_unfinished(tmp_path)
    assert len(found) == 1


def test_accessibility_fallback_keeps_visible_text_independent_of_script():
    source = (ROOT / "audioknigi/qt/accessibility.py").read_text(encoding="utf-8")
    block = source[source.index("def _fallback_accessible_name"):source.index("def _default_accessible_description")]
    assert "if visible:\n                return visible" in block
    assert "re.search" not in block


def test_ambiguous_dash_title_is_not_invented_as_author():
    class Response:
        text = "<html><title>Гарри Поттер — Философский камень</title></html>"

        def raise_for_status(self):
            return None

    class Session:
        def get(self, *_args, **_kwargs):
            return Response()

    result = SearchResult(
        title="Гарри Поттер — Философский камень",
        author="",
        url="https://audioknigi.com.ua/audio-1-test",
        source="audioknigi.com.ua",
    )
    enriched = _audioknigi_page_metadata(
        result,
        session_factory=Session,
        metadata_extractor=lambda _html, fallback: (fallback, "", ""),
        extended_metadata_extractor=lambda _html: ("", "", "", ""),
    )
    assert enriched.author == ""
    assert enriched.title == "Гарри Поттер — Философский камень"


def test_easy_mode_empty_search_focus_and_clipboard_suppression_are_hardened():
    search_source = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    assert 'if self.current_ui_mode() == "easy":\n                self.easy_input.setFocus' in search_source

    clipboard_source = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    assert "same_clipboard_url = text == suppress" in clipboard_source
    assert "normalize_supported_url(text) == normalize_supported_url(suppress)" in clipboard_source


def test_f1_shortcut_targets_shortcuts_help_and_history_delete_is_in_place():
    access_source = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert 'show_context_help(topic="shortcuts")' in access_source
    assert "weakref.ref(combo)" in access_source

    history_source = (ROOT / "audioknigi/qt/mixins/history.py").read_text(encoding="utf-8")
    block = history_source[history_source.index("def history_delete"):history_source.index("def export_library")]
    assert "self._load_history()" in block
    assert "history_table.removeRow(row)" not in block
