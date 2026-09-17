from __future__ import annotations

import ast
from pathlib import Path

import pytest

from audioknigi.models import Book, Track
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.download_request import build_download_request


ROOT = Path(__file__).resolve().parents[1]
QT_DIR = ROOT / "audioknigi" / "qt"
SERVICES_DIR = ROOT / "audioknigi" / "services"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_phase2_services_stay_gui_independent():
    paths = list(SERVICES_DIR.glob("*.py"))
    assert paths
    for path in paths:
        imports = _imports(path)
        assert not any(name == "tkinter" or name.startswith("tkinter.") for name in imports), path
        assert not any(name == "PySide6" or name.startswith("PySide6.") for name in imports), path
        text = path.read_text(encoding="utf-8")
        assert "ui_kit" not in text, path
        assert "audioknigi.downloader" not in text, path
        assert "..downloader" not in text, path


def test_phase2_qt_uses_independent_analysis_and_track_model():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    track_model = (QT_DIR / "track_model.py").read_text(encoding="utf-8")
    assert "BookAnalysisService" in text
    assert "_AnalysisWorker" in text
    assert "cancel_analysis" in text
    assert "TrackTableModel" in text
    assert "QTableView" in text
    assert "ItemIsUserCheckable" in track_model
    assert "CheckStateRole" in track_model
    assert "DownloaderMixin" not in text
    assert "tkinter" not in text


def test_audioknigi_playlist_parser_builds_tracks_without_gui_or_network():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/audio-1-test",
        html_text='<html><head><title>Автор - Книга аудиокнига</title></head><body></body></html>',
        page_title="Автор - Книга аудиокнига",
        playlist_url="https://cdn.example/book.pl.txt",
        playlist_text='[{"title":"Глава 1","file":"1.mp3","start":"00:00:00","end":"00:01:30"},'
        '{"title":"Глава 2","file":"2.mp3","duration":"95"}]',
    )
    assert len(book.tracks) == 2
    assert book.tracks[0].file == "https://cdn.example/1.mp3"
    assert book.tracks[0].duration == 90
    assert book.tracks[1].duration == 95
    assert all(track.selected for track in book.tracks)


def test_playlist_url_detection_handles_escaped_slashes():
    html = r'<script>file:"https:\/\/cdn.example\/abc.pl.txt?x=1"</script>'
    assert BookAnalysisService._extract_playlist_url(html) == "https://cdn.example/abc.pl.txt?x=1"


def test_download_request_contract_validates_selected_tracks(tmp_path):
    book = Book(
        url="https://example/book",
        title="Книга",
        tracks=[Track(index=1, title="1", file="a.mp3"), Track(index=2, title="2", file="b.mp3")],
    )
    request = build_download_request(
        book,
        {
            "output_dir": str(tmp_path),
            "audio_preset": "copy",
            "naming_mode": "number",
            "normalization_mode": "off",
        },
        [2],
    )
    assert request.selected_indices == [2]
    assert request.output_dir == tmp_path
    assert request.audio_preset == "copy"

    with pytest.raises(ValueError, match="Не выбрана"):
        build_download_request(book, {"output_dir": str(tmp_path)}, [])
    with pytest.raises(ValueError, match="неизвестные"):
        build_download_request(book, {"output_dir": str(tmp_path)}, [99])
