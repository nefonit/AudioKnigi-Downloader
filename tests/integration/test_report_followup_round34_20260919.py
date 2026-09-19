from __future__ import annotations

import json
from pathlib import Path

from audioknigi.config.settings import migrate_settings
from audioknigi.download_engine import _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_poleknig_annotation_prefers_visible_synopsis_over_seo_meta() -> None:
    html = """
    <html><head>
      <meta name="description" content="Скачать аудиокнигу Автор Крыса и слушать аудиокнигу онлайн">
    </head><body>
      <h1>Крыса</h1><a href="/authors/12-author">Автор</a>
      <div class="book-description">
        Настоящая аннотация книги рассказывает о герое, который оказывается перед трудным выбором.
        Это содержательное описание сюжета, а не служебный SEO-текст страницы.
      </div>
    </body></html>
    """
    meta = _book_page_metadata(html, "https://poleknig.com/books/1")
    assert meta["description"].startswith("Настоящая аннотация книги")
    assert "Скачать аудиокнигу" not in meta["description"]


def test_standalone_tracks_are_not_trimmed_to_rounded_metadata_duration() -> None:
    block = src("audioknigi/download/media.py")
    block = block[block.index("def _split_track"):block.index("def _save_book_sidecars")]
    assert "elif start is None and end is None:" in block
    assert "process the complete source to EOF" in block


def test_segmented_cancel_waits_for_windows_file_handles() -> None:
    source = src("audioknigi/download/network.py")
    assert "thread.join(timeout=min(1.0, remaining))" in source
    assert "event=segmented_cancel_workers_lingering" in source


def test_retained_source_suffix_uses_container_or_codec() -> None:
    assert _DownloadEngine._retained_source_suffix("https://x/source", {"codec":"mp3"}) == ".mp3"
    assert _DownloadEngine._retained_source_suffix("https://x/source", {"codec":"aac","format_name":"mov,mp4,m4a"}) == ".m4a"


def test_knigavuhe_marker_must_be_actual_call() -> None:
    assert _extract_call_argument('BookController.enter = function(x) {}; foo({"wrong":1});') == ""
    assert '"ok": 1' in _extract_call_argument('BookController.enter ({"ok": 1}, true);')


def test_settings_boolean_strings_are_normalized() -> None:
    settings, _ = migrate_settings({"embed_tags":"false","clipboard_auto":"true"})
    assert settings["embed_tags"] is False
    assert settings["clipboard_auto"] is True


def test_cover_sidecar_uses_atomic_binary_writer() -> None:
    assert "def atomic_write_bytes" in src("audioknigi/download/common.py")
    assert 'atomic_write_bytes(folder / ("cover" + ext), data)' in src("audioknigi/download/media.py")


def test_audioknigi_author_prefix_accepts_reordered_full_name() -> None:
    assert _strip_author_prefix_from_title("Лев Толстой - Война и мир", "Толстой Лев Николаевич") == "Война и мир"


def test_ui_and_queue_runtime_guards_are_present() -> None:
    assert 'f"Ошибка источника {provider.display_name}"' in src("audioknigi/services/search_service.py")
    assert "self.rowAt(int(event.position().y()))" in src("audioknigi/qt/workers.py")
    assert 'self.set_ui_mode("advanced")' in src("audioknigi/qt/player_mixin.py")
    assert 'if task.status_code == "error" and not task_requires_analysis(task):' in src("audioknigi/qt/mixins/queue.py")
    assert 'if getattr(self, "_exit_requested", False):' in src("audioknigi/qt/mixins/search.py")
    assert "focus_table_row(self.track_table, 0, focus=False)" in src("audioknigi/qt/mixins/clipboard.py")


def test_runtime_regex_contains_round34_dynamic_messages() -> None:
    entries = json.loads((ROOT / "audioknigi/locales/runtime_regex.json").read_text(encoding="utf-8"))
    mapping = {pattern: value for pattern, value in entries}
    assert mapping[r"^Озвучка (\d+)$"]["de"] == "Sprecherfassung {0}"
    assert r"^Ошибка источника (.+)$" in mapping
    assert r"^Найден исправный резервный источник knigavuhe\.org\. Переключаю загрузку автоматически: (.+)\.$" in mapping
