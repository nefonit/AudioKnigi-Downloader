from __future__ import annotations

import ast
import http.server
from pathlib import Path
import shutil
import socketserver
import subprocess
import sys
import threading

import pytest

from audioknigi.core import Cancelled
from audioknigi.download_engine import DownloadCallbacks, DownloadService, _DownloadEngine
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest, build_download_request


ROOT = Path(__file__).resolve().parents[1]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def _book(url="https://knigavuhe.org/book/phase3-test/"):
    return Book(
        url=url,
        title="Phase 3 Test",
        tracks=[Track(index=1, title="One", file="https://cdn.invalid/1.mp3")],
    )


def test_downloader_core_no_longer_imports_tk_or_ui_kit():
    path = ROOT / "audioknigi" / "downloader.py"
    imports = _imports(path)
    assert not any(name == "tkinter" or name.startswith("tkinter.") for name in imports)
    text = path.read_text(encoding="utf-8")
    assert "ui_kit" not in text
    assert "messagebox" not in text
    assert "activate_modal_window" not in text


def test_tk_frontend_keeps_interactive_download_hooks():
    text = (ROOT / "audioknigi" / "actions.py").read_text(encoding="utf-8")
    assert "def _report_download_error(self, message):" in text
    assert "def _ask_missing_media_action(self, track_indices" in text
    assert "activate_modal_window(window, self" in text


def test_headless_engine_import_does_not_load_tkinter_in_clean_process(tmp_path):
    code = (
        "import sys; import audioknigi.download_engine; "
        "assert 'tkinter' not in sys.modules, sorted(x for x in sys.modules if x.startswith('tkinter'))"
    )
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_download_request_uses_default_output_when_setting_is_blank():
    request = build_download_request(_book(), {}, [1])
    assert str(request.output_dir)
    assert str(request.output_dir) != "."


def test_download_service_cancelled_before_start(tmp_path):
    request = DownloadRequest(book=_book(), selected_indices=[1], output_dir=tmp_path)
    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        DownloadService(cancel_event=event).download(request)


def test_missing_media_callback_is_gui_neutral(tmp_path):
    request = DownloadRequest(book=_book(), selected_indices=[1], output_dir=tmp_path)
    seen = []
    callbacks = DownloadCallbacks(
        missing_media=lambda indices, detail, allow_skip: seen.append((indices, detail, allow_skip)) or "skip"
    )
    engine = _DownloadEngine(request, {}, threading.Event(), callbacks)
    assert engine._ask_missing_media_action([3, 2], detail="404", allow_skip=True) == "skip"
    assert seen == [([2, 3], "404", True)]


def test_qt_phase3_wires_real_download_worker_statically():
    text = (ROOT / "audioknigi" / "qt" / "main_window.py").read_text(encoding="utf-8")
    assert "class _DownloadWorker(QObject):" in text
    assert "DownloadService(" in text
    assert "self.download_button.clicked.connect(self.start_download)" in text
    assert "self.cancel_download_button.clicked.connect(self.cancel_download)" in text
    assert "def _resolve_missing_media" in text
    assert "QMessageBox.ButtonRole.AcceptRole" in text
    assert "from tkinter" not in text
    assert "import tkinter" not in text


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="FFmpeg required")
def test_headless_download_engine_real_two_track_smoke(tmp_path, monkeypatch):
    import audioknigi.download_engine as download_engine

    serve = tmp_path / "serve"
    output = tmp_path / "output"
    serve.mkdir()
    output.mkdir()

    for index, frequency in ((1, 440), (2, 660)):
        subprocess.run(
            [
                shutil.which("ffmpeg") or "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:duration=0.8",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "64k",
                str(serve / f"{index}.mp3"),
            ],
            check=True,
        )

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def translate_path(self, path):
            relative = path.split("?", 1)[0].lstrip("/")
            return str(serve / relative)

    server = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    monkeypatch.setattr(download_engine, "HISTORY_FILE", tmp_path / "history.json")
    book = Book(
        url="https://knigavuhe.org/book/phase3-smoke/",
        title="Phase 3 Smoke",
        author="Test",
        tracks=[
            Track(index=1, title="One", file=f"http://127.0.0.1:{port}/1.mp3"),
            Track(index=2, title="Two", file=f"http://127.0.0.1:{port}/2.mp3"),
        ],
    )
    request = DownloadRequest(book=book, selected_indices=[1, 2], output_dir=output)
    statuses = []
    stages = []
    progress = []
    callbacks = DownloadCallbacks(
        status=statuses.append,
        stage=lambda number, text: stages.append((number, text)),
        progress=progress.append,
    )

    try:
        result = DownloadService(
            settings={
                "delete_source": False,
                "embed_tags": False,
                "save_sidecars": False,
                "segment_count": "1",
            },
            callbacks=callbacks,
        ).download(request)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.skipped_indices == []
    assert (result.folder / "01.mp3").stat().st_size > 0
    assert (result.folder / "02.mp3").stat().st_size > 0
    assert not (result.folder / "resume.json").exists()
    assert (tmp_path / "history.json").exists()
    assert statuses[-1] == "Готово"
    assert stages[-1] == (5, "Готово")
    assert progress and max(progress) == 100.0
