from __future__ import annotations

import json
from pathlib import Path

import pytest

from audioknigi.core import effective_track_duration
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService

ROOT = Path(__file__).resolve().parents[2]


def test_effective_track_duration_accepts_mapping_tracks():
    assert effective_track_duration({"duration": "12.5"}) == pytest.approx(12.5)
    assert effective_track_duration({"start": "00:01", "end": "00:06"}) == pytest.approx(5.0)
    assert effective_track_duration({"actual_duration": 7}) == pytest.approx(7.0)


def test_sidecars_tolerate_mapping_track_and_missing_index(tmp_path):
    class Harness(MediaProcessingMixin):
        runtime_save_sidecars = True

        def _cover_bytes(self, _book):
            return None

        def _log_book_flow(self, *_args, **_kwargs):
            pass

        def log(self, text):
            raise AssertionError(text)

    book = Book(url="https://example.invalid/book", title="Demo")
    tracks = [
        {"index": None, "title": "", "start": 0, "end": 10, "duration": None},
        {"index": "2", "title": "Second", "duration": 5},
    ]
    book.tracks = tracks
    Harness()._save_book_sidecars(book, tmp_path, tracks)
    payload = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert payload["tracks"][0]["index"] == 1
    assert payload["tracks"][0]["title"] == "Часть 01"
    assert payload["tracks"][0]["duration"] == pytest.approx(10.0)
    assert payload["tracks"][1]["index"] == 2


def test_refresh_playlist_ignores_invalid_track_indices_instead_of_crashing(tmp_path):
    original = Book(
        url="https://example.invalid/book",
        title="Demo",
        tracks=[Track(index=1, title="One", file="old.mp3")],
    )
    fresh = Book(
        url=original.url,
        title="Demo",
        tracks=[
            Track(index=None, title="Broken", file="broken.mp3"),
            Track(index=1, title="One", file="new.mp3"),
        ],
    )

    class Harness(BookFlowMixin):
        runtime_language = "ru"

        def _check_cancel(self):
            pass

        def set_status(self, _text):
            pass

        def set_stage(self, *_args):
            pass

        def log(self, _text):
            pass

        def _analyze_book(self, _url):
            return fresh

        def _clear_stale_source_downloads(self, _book):
            return 0

    changed = Harness()._refresh_book_media_playlist(original, [1, "bad", None])
    assert changed == 1
    assert len(original.tracks) == 2
    assert original.tracks[1].file == "new.mp3"


def test_parallel_multisource_split_does_not_race_per_track_status_announcements():
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert "def split_group(source_url, group_tracks, *, announce_track=True):" in source
    assert "if announce_track:" in source
    assert "pool.submit(split_group, url, group, announce_track=False)" in source


def test_runtime_template_with_named_count_is_already_exact_format_safe():
    from audioknigi.i18n import ui_text

    assert ui_text("en", "Найдено вариантов озвучки: {count}. Выберите чтеца.", count=3) == (
        "Narration options found: 3. Choose a narrator."
    )


def test_runtime_regex_still_precedes_prefix_fallback():
    from audioknigi.i18n import localize_runtime_text

    assert localize_runtime_text("en", "История обновлена: 10 записей.") == "History refreshed: 10 entries."


def test_short_source_fallback_fetches_missing_cover(monkeypatch):
    source = Book(
        url="https://audioknigi.com.ua/demo",
        title="Demo",
        tracks=[
            Track(index=1, title="One", file="https://cdn.invalid/shared.mp3", start=0, end=100),
            Track(index=2, title="Two", file="https://cdn.invalid/shared.mp3", start=100, end=200),
        ],
    )
    fallback = Book(
        url="https://knigavuhe.org/book/demo",
        title="Demo",
        cover_url="https://img.invalid/cover.jpg",
        tracks=[Track(index=1, title="One", file="https://cdn.invalid/one.mp3")],
    )
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=True, fetch_remote_size=False))
    monkeypatch.setattr(service, "_probe_remote_duration", lambda *_args, **_kwargs: 50.0)
    monkeypatch.setattr(service, "_knigavuhe_fallback_candidate", lambda _book: fallback)
    monkeypatch.setattr(service, "_populate_missing_track_durations", lambda _book: None)
    monkeypatch.setattr(service, "_fetch_cover_bytes", lambda *_args, **_kwargs: (b"cover", "image/jpeg"))

    recovered = service._recover_short_audioknigi_source(source)
    assert recovered is fallback
    assert recovered.cover_cache == (b"cover", "image/jpeg")


def test_identity_tokens_preserve_ukrainian_and_belarusian_letters():
    service_tokens = BookAnalysisService._identity_tokens("Марія Ґрунт Ўзор")
    assert {"марія", "ґрунт", "ўзор"} <= service_tokens

    probe_source = (ROOT / "audioknigi/download/probe.py").read_text(encoding="utf-8")
    assert 're.findall(r"[^\\W_]+", text, re.UNICODE)' in probe_source


def test_queue_deserializer_does_not_shadow_dataclasses_fields_function():
    source = (ROOT / "audioknigi/services/queue_service.py").read_text(encoding="utf-8")
    block = source[source.index("def _book_from_dict"):source.index("def task_to_dict")]
    assert "book_fields = Book.__dataclass_fields__" in block
    assert "\n    fields = Book.__dataclass_fields__" not in block


def test_full_mp3_refresh_updates_manifest_and_result_indices():
    source = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    block = source[source.index("def run_full_mp3"):source.index("def run(self)")]
    assert "full_indices = list(req.selected_indices)" in block
    assert 'self._write_resume_manifest(book, full_indices, download_mode="full_mp3")' in block
    assert 'selected_indices=list(getattr(self.request, "selected_indices", None) or full_indices)' in block


def test_provider_variant_availability_is_case_insensitive_and_current_is_explicit():
    poleknig = (ROOT / "audioknigi/poleknig.py").read_text(encoding="utf-8")
    assert 'str(getattr(item, "availability", "") or "").casefold() == "restricted"' in poleknig
    assert 'str(getattr(item, "availability", "") or "").casefold() == "available"' in poleknig

    from audioknigi.knigavuhe import _extract_narration_variants

    available = _extract_narration_variants("", "https://knigavuhe.org/book/demo", current_available=True)
    restricted = _extract_narration_variants("", "https://knigavuhe.org/book/demo", current_available=False)
    assert available and available[0].available is True
    assert restricted and restricted[0].available is False


def test_track_model_source_uses_safe_selected_indices_without_importing_qt():
    source = (ROOT / "audioknigi/qt/track_model.py").read_text(encoding="utf-8")
    block = source[source.index("def selected_indices"):source.index("def selected_count")]
    assert "self._safe_track_index(track, row)" in block
    assert "int(track.index)" not in block


def test_german_onboarding_and_commands_use_sie_form_and_restart_badge_has_no_period():
    onboarding = (ROOT / "audioknigi/qt/onboarding.py").read_text(encoding="utf-8")
    assert "Wählen Sie die wichtigsten Einstellungen" in onboarding
    assert "können Sie später" in onboarding
    assert "kannst du" not in onboarding

    legacy = json.loads((ROOT / "audioknigi/locales/legacy_literals.json").read_text(encoding="utf-8"))
    assert legacy["de"]["Дождитесь завершения анализа книги."].startswith("Warten Sie")
    assert legacy["de"]["Сначала остановите очередь загрузок."].startswith("Stoppen Sie")
    assert "Analysieren Sie" in legacy["de"]["Повтор невозможен: сначала заново проанализируйте импортированную книгу."]
    assert legacy["de"]["Сначала завершите текущую загрузку или очередь."].startswith("Beenden Sie")

    exact = json.loads((ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8"))
    restart = exact["Применится после перезапуска"]
    assert restart["de"] == "Wird nach einem Neustart angewendet"
    assert restart["en"] == "Applies after restart"
    assert restart["uk"] == "Застосується після перезапуску"


def test_output_dir_none_and_easy_download_state_are_guarded():
    pages = (ROOT / "audioknigi/qt/main_window_pages.py").read_text(encoding="utf-8")
    assert 'self.output_edit = QLineEdit(str(self.settings.get("output_dir") or DEFAULT_OUTPUT))' in pages

    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    block = main[main.index("def _update_easy_action_text"):main.index("def _set_operation_ui_blocked")]
    assert 'elif hasattr(self, "easy_download_button"):' in block
    assert "self.easy_download_button.setEnabled(False)" in block


def test_analysis_requeue_and_delayed_actions_guard_state_and_indices():
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert 'safe_int(getattr(track, "index", None), 0)' in source
    assert "self.current_book is not expected_book" in source
    assert 'if bool(getattr(self, "_exit_requested", False)):' in source


def test_clipboard_shortcut_read_is_bounded_and_track_index_is_safe():
    source = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    assert 'shortcut_file.read(65536)' in source
    assert 'track_index = safe_int(getattr(track, "index", None), 0)' in source
    assert "int(track.index)" not in source[source.index("def download_selected_track_only"):]


def test_round73_high_value_fixes_remain_present():
    library = (ROOT / "audioknigi/services/library_service.py").read_text(encoding="utf-8")
    assert "_history_rows(data, strict=True, limit=None)" in library

    engine = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    full = engine[engine.index("def run_full_mp3"):engine.index("def run(self)")]
    assert "if source_ready:" in full
    assert 'tags.delall("TRCK")' in full

    media = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    split = media[media.index("def _split_track"):media.index("def _save_book_sidecars")]
    assert "unlink_with_retry(out, missing_ok=True)" in split
