"""Regression tests for confirmed Round 90 audit findings."""

import json

from audioknigi.brand import DISPLAY_NAME
from audioknigi.config.settings import save_app_settings
from audioknigi.crash_report import crash_report_is_current, read_current_crash_report
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.metadata import APP_VERSION


def test_crash_report_accepts_string_path(tmp_path):
    report = tmp_path / "last_crash_report.txt"
    report.write_text(f"{DISPLAY_NAME} {APP_VERSION}\nTraceback detail\n", encoding="utf-8")
    assert crash_report_is_current(str(report))
    assert "Traceback detail" in read_current_crash_report(str(report))


def test_log_secret_redaction_hides_quoted_spaces():
    sanitized = sanitize_log_text('{"password": "my secret phrase", "token": "abc def"}')
    assert "my secret phrase" not in sanitized
    assert "abc def" not in sanitized
    assert "<hidden>" in sanitized


def test_partial_settings_save_does_not_complete_onboarding(tmp_path):
    path = tmp_path / "settings.json"
    assert save_app_settings({"language": "ru"}, path=path)
    assert json.loads(path.read_text(encoding="utf-8"))["first_run_complete"] is False
    assert save_app_settings({"language": "de"}, path=path)
    assert json.loads(path.read_text(encoding="utf-8"))["first_run_complete"] is False


def test_loudnorm_missing_measurements_fall_back(monkeypatch):
    from audioknigi.download import media

    monkeypatch.setattr(media, "resolve_executable", lambda _name: "ffmpeg")
    class Processor(media.MediaProcessingMixin):
        def __init__(self):
            self.messages = []
        def _run_ffmpeg_capture(self, _cmd, timeout=None):
            return "decoder warning without loudnorm statistics"
        def log(self, message):
            self.messages.append(message)

    processor = Processor()
    result = processor._measure_loudnorm("sample.mp3")
    assert result == "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json"
    assert any("однопроходную" in message for message in processor.messages)


def test_disk_preflight_rejects_invalid_explicit_selection():
    import pytest
    from audioknigi.download.probe import ProbeMixin
    from types import SimpleNamespace

    for selected in ([None], [-1], ["invalid"]):
        with pytest.raises(ValueError, match="Invalid selected track index"):
            ProbeMixin()._estimate_required_space(SimpleNamespace(tracks=[], remote_size=0), selected)


def test_runtime_status_translations_include_refresh_and_loudness():
    from pathlib import Path
    translations = json.loads(
        (Path(__file__).resolve().parents[2] / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8")
    )
    for phrase in (
        "Аудиоссылка устарела — обновляю плейлист…",
        "Качественная нормализация: анализ громкости…",
    ):
        assert set(("en", "de", "uk")).issubset(translations[phrase])


def test_download_request_rejects_invalid_indices_explicitly():
    import pytest
    from audioknigi.services.download_request import DownloadRequest
    for invalid in (None, -1, True, "not-a-number"):
        with pytest.raises(ValueError):
            DownloadRequest.track_index(invalid)


def test_skipped_parts_runtime_translation_uses_captured_suffix():
    from audioknigi.i18n import localize_runtime_text
    source = "Скачивание завершено. Пропущены недоступные части: 2, 4"
    translated = localize_runtime_text("en", source)
    assert translated == "Download completed. Unavailable parts were skipped: 2, 4"
    assert "2, 4" in localize_runtime_text("uk", source)
    assert "2, 4" in localize_runtime_text("de", source)


def test_support_bundle_windows_path_multiline_keeps_following_diagnostics():
    from audioknigi.diagnostics.support_bundle import _privacy_path

    message = "Failed: C:\\Users\\Alice\\My Books\\recording.mp3\nRetrying source lookup"
    redacted = _privacy_path(message, collapse_whole_path=False)
    assert "Alice" not in redacted
    assert "My Books" not in redacted
    assert "<configured-path>" in redacted
    assert "Retrying source lookup" in redacted


def test_support_bundle_windows_file_path_preserves_error_suffix():
    from audioknigi.diagnostics.support_bundle import _privacy_path

    message = "Failed: C:\\Users\\Alice\\My Books\\recording.mp3: decoder error"
    redacted = _privacy_path(message, collapse_whole_path=False)
    assert redacted.endswith(": decoder error")
    assert "Alice" not in redacted


def test_support_bundle_ambiguous_windows_directory_path_stays_private():
    from audioknigi.diagnostics.support_bundle import _privacy_path

    message = "Cannot use C:\\Users\\Alice\\My Books Access denied"
    redacted = _privacy_path(message, collapse_whole_path=False)
    assert "Alice" not in redacted
    assert "My Books" not in redacted
