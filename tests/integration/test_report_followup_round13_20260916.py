from __future__ import annotations

import csv
import json
import threading
import zipfile
from pathlib import Path
from types import SimpleNamespace


def test_support_bundle_preserves_dotted_name_and_masks_case_and_camel_secrets(tmp_path, monkeypatch):
    from audioknigi.diagnostics import support_bundle as support

    queue_path = tmp_path / "qt_queue.json"
    queue_path.write_text(
        json.dumps([
            {
                "url": "https://knigavuhe.org/book/example/",
                "status": "Ошибка",
                "status_code": "error",
                "attempts": 2,
            }
        ], ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(support, "QT_QUEUE_FILE", queue_path)

    sanitized = support.sanitized_settings(
        {
            "Geometry": "private-geometry",
            "apiKey": "secret-a",
            "authToken": "secret-b",
            "adminPassword": "secret-c",
        }
    )
    assert sanitized["Geometry"] == "<window-geometry>"
    assert sanitized["apiKey"] == "<redacted>"
    assert sanitized["authToken"] == "<redacted>"
    assert sanitized["adminPassword"] == "<redacted>"

    target = support.create_support_bundle(tmp_path / "bundle_1.0", settings={})
    assert target.name == "bundle_1.0.zip"
    with zipfile.ZipFile(target) as archive:
        summary = json.loads(archive.read("diagnostics/queue.summary.json").decode("utf-8"))
    assert summary[0]["status"] == "Ошибка"
    assert summary[0]["status_code"] == "error"


def test_support_bundle_directory_destination_creates_zip_inside_directory(tmp_path):
    from audioknigi.diagnostics.support_bundle import create_support_bundle

    target = create_support_bundle(tmp_path, settings={})
    assert target.parent == tmp_path
    assert target.suffix == ".zip"
    assert target.name.startswith("support_bundle_")


def test_app_settings_uses_mapping_equality_contract():
    from audioknigi.config.settings import AppSettings

    settings = AppSettings({"scale": 100, "language": "ru"})
    assert settings == {"scale": 100, "language": "ru"}
    assert settings != {"scale": 125, "language": "ru"}


def test_audioknigi_query_filter_ignores_noise_and_accepts_initials():
    from audioknigi.providers.audioknigi_search import _matches_query

    assert _matches_query("Метель", "Метель аудиокнига")
    assert _matches_query("Метель", "аудиокнига")
    assert _matches_query("Война и мир", "Лев Толстой", author="Л. Н. Толстой")
    assert not _matches_query("Дозор", "Лев Толстой", author="С. Лукьяненко")


def test_cloudflare_just_a_moment_is_only_strong_in_page_title():
    from audioknigi.services.book_analysis_service import BookAnalysisService

    normal = "<html><head><title>Real book</title></head><body>Wait just a moment, he said.</body></html>"
    challenge = "<html><head><title>Just a moment...</title></head><body>Checking</body></html>"
    assert BookAnalysisService._looks_like_protection(normal, 200) is False
    assert BookAnalysisService._looks_like_protection(challenge, 200) is True


def test_player_position_uses_saved_duration_when_runtime_duration_unknown(tmp_path):
    from audioknigi.services.player_position_store import PlayerPositionStore

    media = tmp_path / "chapter.mp3"
    media.write_bytes(b"x")
    store_path = tmp_path / "positions.json"
    key = PlayerPositionStore.key(media)
    store_path.write_text(
        json.dumps({key: {"position": 99.5, "duration": 100.0, "file": media.name}}),
        encoding="utf-8",
    )
    store = PlayerPositionStore(store_path)
    assert store.saved_seconds(media) == 0.0


def test_csv_export_neutralizes_formula_cells(tmp_path):
    from audioknigi.services.library_service import export_history

    target = export_history(
        [
            {
                "date": "2026-09-16",
                "title": "=1+1",
                "author": "@cmd",
                "narrator": "+reader",
                "genre": "-formula",
                "year": "2026",
                "parts": 1,
                "folder": "C:/Books",
                "url": "https://example.test/book",
            }
        ],
        tmp_path / "history.csv",
        "csv",
    )
    with target.open("r", encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["title"] == "'=1+1"
    assert row["author"] == "'@cmd"
    assert row["narrator"] == "'+reader"
    assert row["genre"] == "'-formula"
    assert row["url"] == "https://example.test/book"


def test_dynamic_download_progress_is_localized():
    from audioknigi.i18n import localize_runtime_text

    assert localize_runtime_text("en", "Скачивается 1/3") == "Downloading 1/3"
    assert localize_runtime_text("de", "Скачивается 2/5") == "Wird heruntergeladen 2/5"


def test_media_id3_accepts_string_track_index(monkeypatch, tmp_path):
    from audioknigi.download import media

    saved = {}

    class FakeTags:
        def delall(self, _name):
            pass

        def add(self, frame):
            text = frame.get("text") if isinstance(frame, dict) else None
            if text:
                saved.setdefault("texts", []).append(text)

        def save(self, _path):
            saved["saved"] = True

    monkeypatch.setattr(media, "ID3", lambda *_args, **_kwargs: FakeTags())
    monkeypatch.setattr(media, "TIT2", lambda **kwargs: kwargs)
    monkeypatch.setattr(media, "TALB", lambda **kwargs: kwargs)
    monkeypatch.setattr(media, "TRCK", lambda **kwargs: kwargs)
    monkeypatch.setattr(media, "TPE1", lambda **kwargs: kwargs)
    monkeypatch.setattr(media, "APIC", lambda **kwargs: kwargs)

    host = SimpleNamespace(runtime_embed_tags=True, log=lambda *_args, **_kwargs: None)
    book = SimpleNamespace(title="Book", author="")
    track = SimpleNamespace(title="")
    media.MediaProcessingMixin._write_id3(host, tmp_path / "part.mp3", book, "2", "10", None, track)
    assert saved.get("saved") is True
    assert any("часть 02" in str(text) for text in saved.get("texts", []))
    assert "2/10" in saved.get("texts", [])


def test_split_track_parses_clock_start_end(monkeypatch, tmp_path):
    from audioknigi.download.media import MediaProcessingMixin

    source = tmp_path / "source.mp3"
    source.write_bytes(b"source")
    output = tmp_path / "out.mp3"
    commands = []

    class Host(MediaProcessingMixin):
        runtime_normalization_mode = "off"

        def _track_path(self, _book, _track):
            return output

        def _effective_mp3_profile(self, _source):
            return True, None, None

        def _run_ffmpeg(self, cmd, timeout=7200):
            commands.append(list(cmd))
            output.write_bytes(b"done")

    host = Host()
    book = SimpleNamespace(tracks=[])
    track = SimpleNamespace(index=1, start="00:01:00", end="00:01:30", duration=None)
    book.tracks = [track]
    host._split_track(book, track, source)
    cmd = commands[0]
    assert cmd[cmd.index("-ss") + 1] == "60"
    assert cmd[cmd.index("-t") + 1] == "30"


def test_audio_probe_cache_does_not_hold_lock_during_ffprobe(tmp_path):
    from audioknigi.download.media import MediaProcessingMixin

    first = tmp_path / "one.mp3"
    second = tmp_path / "two.mp3"
    first.write_bytes(b"1")
    second.write_bytes(b"2")
    first_entered = threading.Event()
    second_entered = threading.Event()
    release = threading.Event()

    class Host(MediaProcessingMixin):
        def _probe_audio_info(self, path):
            if Path(path) == first:
                first_entered.set()
                release.wait(2.0)
            else:
                second_entered.set()
            return {"codec": "mp3"}

    host = Host()
    results = []
    t1 = threading.Thread(target=lambda: results.append(host._cached_probe_audio_info(first)))
    t2 = threading.Thread(target=lambda: results.append(host._cached_probe_audio_info(second)))
    t1.start()
    assert first_entered.wait(1.0)
    t2.start()
    try:
        assert second_entered.wait(0.5), "second probe was blocked behind the cache lock"
    finally:
        release.set()
        t1.join(2.0)
        t2.join(2.0)
    assert len(results) == 2


def test_qt_sources_harden_invalid_track_index_and_keyboard_seek_without_importing_pyside():
    root = Path(__file__).resolve().parents[2]
    track_model = (root / "audioknigi/qt/track_model.py").read_text(encoding="utf-8")
    player_controller = (root / "audioknigi/qt/player_controller.py").read_text(encoding="utf-8")
    player_mixin = (root / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")

    assert "def _safe_track_index" in track_model
    assert "safe_int(getattr(track, \"index\"" in track_model
    assert "self.save_position(force=False, explicit_seconds=target / 1000.0)" in player_controller
    assert "seek(int(value) * 1000)" in player_mixin
