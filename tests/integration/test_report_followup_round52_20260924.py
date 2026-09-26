from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest, build_download_request


def test_support_log_redacts_filename_with_spaces_without_eating_status_text() -> None:
    value = r"error at D:\Audiobooks\01. Введение.mp3 not found"
    cleaned = support_bundle._privacy_path(value, collapse_whole_path=False)
    assert cleaned == "error at <configured-path> not found"
    assert "Введение.mp3" not in cleaned


def test_support_log_redacts_unc_filename_with_spaces_and_accepts_path_objects() -> None:
    value = r"Network \\server\share\My Book.mp3 failed"
    assert support_bundle._privacy_path(value, collapse_whole_path=False) == "Network <configured-path> failed"
    assert support_bundle._privacy_path(Path(r"D:\Audio Books\My Collection")) == "<configured-path>"


def test_settings_migrate_legacy_chunk_value_when_new_key_is_none() -> None:
    data, _changed = settings_module.migrate_settings(
        {"auto_chunk_min_kbytes_per_sec": None, "auto_chunk_min_kbps": 640}
    )
    assert data["auto_chunk_min_kbytes_per_sec"] == 640
    assert "auto_chunk_min_kbps" not in data


def test_segment_count_normalizes_zero_and_out_of_range_values() -> None:
    assert settings_module.normalize_settings({"segment_count": "0"})["segment_count"] == "auto"
    assert settings_module.normalize_settings({"segment_count": 0})["segment_count"] == "auto"
    assert settings_module.normalize_settings({"segment_count": "9"})["segment_count"] == "auto"
    assert settings_module.normalize_settings({"segment_count": "3"})["segment_count"] == "3"


def test_download_request_rejects_boolean_track_indices(tmp_path: Path) -> None:
    book = Book(
        url="https://example.invalid/book",
        title="Book",
        tracks=[Track(index=1, title="One", file="https://example.invalid/1.mp3")],
    )
    with pytest.raises(ValueError, match="Некорректный индекс части"):
        DownloadRequest.track_index(True)
    with pytest.raises(ValueError, match="Некорректный индекс части"):
        build_download_request(book, {"output_dir": str(tmp_path)}, [True])


def test_book_flow_skips_malformed_internal_track_indices() -> None:
    captured = {}

    class Flow(BookFlowMixin):
        def _process_book_once(self, _book, selected_indices=None, status_callback=None):
            captured["selected"] = set(selected_indices or set())
            return "ok"

    book = SimpleNamespace(
        tracks=[
            SimpleNamespace(index=1),
            SimpleNamespace(index="2"),
            SimpleNamespace(index=None),
            SimpleNamespace(index="bad"),
            SimpleNamespace(index=True),
        ]
    )
    assert Flow()._process_book(book) == "ok"
    assert captured["selected"] == {1, 2}


def test_qt_entrypoint_normalizes_none_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    import audioknigi_qt

    fake = ModuleType("audioknigi.qt.application")
    fake.run_qt = lambda _argv: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "audioknigi.qt.application", fake)
    monkeypatch.setattr(sys, "argv", ["audioknigi_qt.py"])
    assert audioknigi_qt.main() == 0
