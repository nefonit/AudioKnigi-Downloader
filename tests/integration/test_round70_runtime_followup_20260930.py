from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from audioknigi.config.settings import AppSettings
from audioknigi.download.probe import ProbeMixin
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.player_position_store import PlayerPositionStore

ROOT = Path(__file__).resolve().parents[2]


def test_multisource_disk_preflight_scales_to_selected_chapters_without_bookflow_mixin(tmp_path):
    class ProbeOnly(ProbeMixin):
        runtime_audio_preset = "copy"

        def _book_folder(self, _book, *, create=False):
            return tmp_path

    tracks = [
        Track(index=index, title=f"Part {index}", file=f"https://cdn.invalid/{index}.mp3", duration=60.0)
        for index in range(1, 51)
    ]
    book = Book(
        url="https://example.invalid/book",
        title="Book",
        tracks=tracks,
        remote_size=2_000_000_000,
    )
    required = ProbeOnly()._estimate_required_space(book, [1])
    # Roughly one fiftieth of source + one fiftieth of output + margin,
    # not the entire 2 GB book.
    assert 1_000_000 < required < 150_000_000


def test_source_target_assignment_is_shared_helper_not_probe_bookflow_dependency():
    probe = (ROOT / "audioknigi/download/probe.py").read_text(encoding="utf-8")
    book_flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    common = (ROOT / "audioknigi/download/common.py").read_text(encoding="utf-8")
    assert "def source_target_assignments(" in common
    assert "assignments = source_target_assignments(book, source_urls, folder)" in probe
    assert "return source_target_assignments(book, source_urls, folder)" in book_flow


def test_retained_repair_promotes_fresh_source_to_canonical_path():
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert 'not bool(getattr(self, "runtime_delete_source", True))' in source
    assert "replace_with_retry(src, original_source)" in source
    assert "src = Path(original_source)" in source


def test_manifest_boundary_error_does_not_trigger_wrong_source_fallback():
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    start = source.index("except SharedSourceTimelineError as exc:")
    block = source[start:source.index("if source_key(", start) + 120]
    assert 'issue.get("reason") == "non_increasing_middle_boundary"' in block
    assert "Повторите анализ книги или выберите другой источник." in block


def test_playwright_uses_only_successful_playlist_response_body_and_shorter_navigation_timeout():
    analysis = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    start = analysis.index("for browser_response in reversed(captured_responses):")
    block = analysis[start:analysis.index("try:\n                    browser_cookies", start)]
    assert 'status = int(getattr(browser_response, "status", 0) or 0)' in block
    assert "if not 200 <= status < 300:" in block
    assert block.index("if not 200 <= status < 300:") < block.index("browser_response.body()")
    assert 'page.goto(url, wait_until="domcontentloaded", timeout=30000)' in analysis

    poleknig = (ROOT / "audioknigi/poleknig.py").read_text(encoding="utf-8")
    assert 'page.goto(url, wait_until="domcontentloaded", timeout=30000)' in poleknig


def test_player_position_reload_serializes_against_disk_persistence(tmp_path):
    path = tmp_path / "positions.json"
    path.write_text(json.dumps({"a": {"position": 10.0}}), encoding="utf-8")
    store = PlayerPositionStore(path)

    events = []

    class TrackingLock:
        def __enter__(self):
            events.append("persist-enter")
            return self

        def __exit__(self, *_args):
            events.append("persist-exit")
            return False

    store._persist_lock = TrackingLock()
    store.reload()
    assert events == ["persist-enter", "persist-exit"]


def _full_mp3_engine(tmp_path, *, selected):
    tracks = [
        Track(index=1, title="One", file="https://cdn.invalid/book.mp3", duration=60.0),
        Track(index=2, title="Two", file="https://cdn.invalid/book.mp3", duration=60.0),
    ]
    book = Book(
        url="https://audioknigi.com.ua/audio-1-demo",
        title="Demo",
        tracks=tracks,
        remote_size=7,
    )
    request = DownloadRequest(book=book, selected_indices=list(selected), output_dir=tmp_path)
    engine = _DownloadEngine(
        request,
        {"delete_source": True, "embed_tags": False, "save_sidecars": False, "audio_preset": "copy"},
        threading.Event(),
        DownloadCallbacks(),
    )
    engine._write_resume_manifest = lambda *_args, **_kwargs: None
    engine._disk_free_for_path = lambda _path: 10**9
    engine._download_source_with_fallback = (
        lambda _url, _fallback, target, _referer: Path(target).write_bytes(b"mp3data")
    )
    engine._cached_probe_audio_info = lambda _path: {"codec": "mp3", "bit_rate": 128000}
    engine._effective_mp3_profile = lambda _path: (True, None, None)
    engine._save_book_sidecars = lambda *_args, **_kwargs: None
    engine._scan_audiobookshelf_after_book = lambda *_args, **_kwargs: None
    engine._add_history = lambda *_args, **_kwargs: None
    engine._remove_resume_manifest = lambda *_args, **_kwargs: None
    return engine


def test_full_mp3_reports_and_persists_all_processed_indices(tmp_path):
    engine = _full_mp3_engine(tmp_path, selected=[1])
    result = engine.run_full_mp3()
    assert isinstance(result, DownloadResult)
    assert result.selected_indices == [1, 2]
    assert engine.request.selected_indices == [1, 2]


def test_full_mp3_duplicate_preflight_treats_stat_race_as_missing(tmp_path):
    engine = _full_mp3_engine(tmp_path, selected=[1])

    class FlakyTarget:
        def is_file(self):
            return True

        def stat(self):
            raise OSError("file disappeared")

    engine._book_folder = lambda *_args, **_kwargs: tmp_path
    engine._full_mp3_target = lambda *_args, **_kwargs: FlakyTarget()
    result = engine.duplicate_preflight(full_mp3=True)
    assert isinstance(result, DuplicatePreflight)
    assert result.exact_duplicate is False
    assert result.evidence == "full-mp3-missing"


def test_player_accepts_webp_sidecar_cover_and_search_progress_rejects_tiny_rects():
    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    assert '"cover.webp"' in player
    assert '"folder.webp"' in player
    assert '"front.webp"' in player

    progress = (ROOT / "audioknigi/qt/search_progress.py").read_text(encoding="utf-8")
    start = progress.index("def paintEvent")
    block = progress[start:progress.index("__all__", start)]
    assert "if side < 16:" in block
    assert block.index("if side < 16:") < block.index("QPainter(self)")


def test_advanced_search_edit_no_longer_overwrites_analyzed_book_url():
    source = (ROOT / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    start = source.index("def _sync_book_input_text")
    end = source.index("@Slot(int)", start)
    block = source[start:end]
    assert "if source is book_edit:" in block
    assert "elif source is search_edit:" in block
    assert block.count("targets = (easy_edit,)") == 2
    assert "targets = (book_edit, search_edit)" in block


def test_settings_bulk_replace_normalizes_once_and_preserves_identity_contract():
    settings = AppSettings({"language": "ru", "scale": 100, "first_run_complete": True})
    identity = id(settings)
    settings.replace_all({"language": "en", "scale": 999, "first_run_complete": True})
    assert id(settings) == identity
    assert settings["language"] == "en"
    assert settings["scale"] == 200
    assert settings["first_run_complete"] is True

    ui_source = (ROOT / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    assert 'replace_all = getattr(self.settings, "replace_all", None)' in ui_source


def test_history_clear_is_blocked_during_active_long_operation_and_cover_icons_scale():
    history = (ROOT / "audioknigi/qt/mixins/history.py").read_text(encoding="utf-8")
    start = history.index("def history_clear")
    block = history[start:history.index("@Slot()", start + 20)]
    assert "if self._long_operation_active():" in block
    assert "setIconSize(QSize(icon_px, icon_px))" in history
    assert "setDefaultSectionSize(max(28, icon_px + 4))" in history

    queue = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    assert "setIconSize(QSize(icon_px, icon_px))" in queue
    assert "setDefaultSectionSize(max(28, icon_px + 4))" in queue


@pytest.mark.parametrize(
    ("language", "source", "expected_fragment"),
    [
        ("en", "Auto-Chunker: снижаю активные Range-потоки 4 → 2 из-за низкой скорости на поток.", "reducing active Range workers"),
        ("de", "Сегментированная загрузка: 4 поток(а/ов), 8 Range-задач.", "Segmentierter Download"),
        ("uk", "Range-запрос временно не удался (2/5); повторяю с того же байта.", "Range-запит тимчасово не вдався"),
        ("en", "chapter.mp3: прямое копирование аудиопотока не удалось; повторяю с совместимым MP3-кодированием.", "direct audio stream copy failed"),
        ("de", "Загрузка остановлена: выбранная часть отсутствует в обновлённом плейлисте.", "Download gestoppt"),
    ],
)
def test_new_core_runtime_messages_are_localized(language, source, expected_fragment):
    translated = localize_runtime_text(language, source)
    assert translated != source
    assert expected_fragment in translated


def test_packaged_locale_path_matches_pyinstaller_destination():
    i18n = (ROOT / "audioknigi/i18n.py").read_text(encoding="utf-8")
    build = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    assert '_LOCALE_DIR = Path(__file__).with_name("locales")' in i18n
    assert '"--add-data", "audioknigi\\locales;audioknigi\\locales"' in build
