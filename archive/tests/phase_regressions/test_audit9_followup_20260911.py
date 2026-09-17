from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_is_current_qt_only_without_retired_launcher_commands():
    readme = text("README.md")
    assert "py audioknigi_qt.py" in readme
    assert "py audioknigi_gui.py" not in readme
    assert "rollback_to_legacy.bat" not in readme
    assert "pip install .[legacy]" not in readme
    assert "playwright install chromium" not in readme


def test_changelog_has_one_root_header_and_one_493_entry():
    changelog = text("CHANGELOG.md")
    assert changelog.count("# Changelog") == 1
    assert changelog.count("## 4.9.3") == 1


def test_third_party_notices_do_not_list_retired_tk_uia():
    assert "tk-uia" not in text("THIRD_PARTY_NOTICES.md").casefold()


def test_current_entry_point_no_longer_labels_product_as_qt_migration():
    source = text("audioknigi_qt.py")
    assert "Phase 39 is Qt-only" in source
    assert '(Qt migration)' not in source


def test_stale_source_cleanup_does_not_create_book_folder():
    source = text("audioknigi/downloader.py")
    body = source[source.index("def _clear_stale_source_downloads"):source.index("def _refresh_book_media_playlist")]
    assert "self._book_folder(book, create=False)" in body
    assert "if not folder.exists():" in body


def test_loudnorm_reports_missing_ffmpeg_before_spawning(monkeypatch):
    import audioknigi.downloader as downloader

    monkeypatch.setattr(downloader, "resolve_executable", lambda _name: None)
    with pytest.raises(RuntimeError, match="FFmpeg не найден"):
        downloader.DownloaderMixin._measure_loudnorm(object(), "book.mp3")


def test_explicit_empty_browser_cookie_snapshot_clears_cookie_file(monkeypatch):
    import audioknigi.core as core

    calls = []
    monkeypatch.setattr(core, "save_json", lambda path, payload: calls.append((path, payload)))
    monkeypatch.setattr(core, "_load_persisted_profile", lambda: {"headers": {"User-Agent": "old"}})
    monkeypatch.setattr(core, "refresh_http_session_profile", lambda: None)
    core.persist_browser_session([], headers={"User-Agent": "new"})
    cookie_calls = [payload for path, payload in calls if path == core.COOKIE_FILE]
    assert cookie_calls == [[]]


def test_proxy_http_header_reader_has_total_deadline(monkeypatch):
    import audioknigi.network_dns as dns

    class SlowSocket:
        def __init__(self):
            self.timeouts = []
        def settimeout(self, value):
            self.timeouts.append(value)
        def recv(self, _size):
            return b"x"

    times = iter((0.0, 0.0, 2.0))
    monkeypatch.setattr(dns.time, "monotonic", lambda: next(times))
    sock = SlowSocket()
    with pytest.raises(TimeoutError):
        dns._read_http_head(sock, deadline_seconds=1.0)
    assert sock.timeouts and sock.timeouts[0] <= 1.0


def test_mapping_base_to_dict_is_safe():
    from audioknigi.models import MappingDataclass
    assert MappingDataclass().to_dict() == {}


def test_poleknig_title_variant_prefilter_allows_harmless_suffix_only():
    from audioknigi.poleknig import _logical_title_compatible
    assert _logical_title_compatible("Название книги", "Название книги — том 1")
    assert _logical_title_compatible("Пьеса: Сказ про Федота", "Про Федота")
    assert not _logical_title_compatible("Война и мир", "Преступление и наказание")


def test_context_menus_select_row_under_pointer_before_using_selection():
    source = text("audioknigi/qt/main_window.py")
    track = source[source.index("def _show_track_context_menu"):source.index("def open_selected_track_file")]
    search = source[source.index("def _show_search_context_menu"):source.index("def _selected_search_result")]
    assert "self.track_table.indexAt(pos)" in track
    assert track.index("selectRow(index.row())") < track.index("self._selected_track()")
    assert "table.indexAt(pos)" in search
    assert search.index("selectRow(index.row())") < search.index("self._selected_search_result(table)")


def test_phase39_i18n_block_has_no_future_phase40_internal_name():
    source = text("audioknigi/i18n.py")
    assert "_PHASE40_LITERAL_TRANSLATIONS" not in source
    assert "_PHASE39_ACCESSIBILITY_LITERAL_TRANSLATIONS" in source
