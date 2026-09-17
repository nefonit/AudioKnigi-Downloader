from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from audioknigi.core import _walk_json
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.common import replace_with_retry
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services import library_service


ROOT = Path(__file__).resolve().parents[2]


def test_forward_slash_unc_redaction_requires_real_server_share_shape() -> None:
    assert _privacy_path("// TODO") == "// TODO"
    assert _privacy_path("//server/share/book.mp3") == "<configured-path>"
    assert _privacy_path("failure at //server/share/book.mp3 now") == "failure at <configured-path> now"
    assert _privacy_path("https://example.test/audio.mp3") == "https://example.test/audio.mp3"


def test_audioknigi_initial_matching_uses_person_fields_not_title_one_letter_words() -> None:
    assert _matches_query("Евгений Онегин", "Александр Пушкин", author="А. С. Пушкин")
    # The title contains a standalone "а", but that must not satisfy the first
    # initial of an unrelated query name.
    assert not _matches_query("Море а ветер", "Александр море", author="")


def test_json_walk_handles_extreme_programmatic_depth_without_recursion() -> None:
    root: object = {"leaf": 1}
    for _ in range(2500):
        root = [root]
    nodes = list(_walk_json(root))
    assert nodes == [{"leaf": 1}]


def test_replace_with_retry_recovers_from_transient_permission_error(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source.bin"
    target = tmp_path / "target.bin"
    source.write_bytes(b"new")
    target.write_bytes(b"old")
    original = Path.replace
    attempts = {"count": 0}

    def flaky_replace(self, other):
        if self == source and attempts["count"] < 2:
            attempts["count"] += 1
            raise PermissionError("sharing violation")
        return original(self, other)

    monkeypatch.setattr(Path, "replace", flaky_replace)
    assert replace_with_retry(source, target) == target
    assert target.read_bytes() == b"new"
    assert attempts["count"] == 2


def test_restore_backup_rolls_back_already_written_members_on_late_failure(tmp_path, monkeypatch) -> None:
    first = tmp_path / "settings.json"
    second = tmp_path / "player_positions.json"
    first.write_text(json.dumps({"old": 1}), encoding="utf-8")
    second.write_text(json.dumps({"old": 2}), encoding="utf-8")
    backup = tmp_path / "backup.zip"
    with zipfile.ZipFile(backup, "w") as archive:
        archive.writestr("settings.json", json.dumps({"new": 1}))
        archive.writestr("player_positions.json", json.dumps({"new": 2}))

    monkeypatch.setattr(
        library_service,
        "BACKUP_MEMBERS",
        {"settings.json": first, "player_positions.json": second},
    )
    real_save = library_service.save_json

    def flaky_save(path, data, *, raise_errors=False):
        if Path(path) == second and isinstance(data, dict) and data.get("new") == 2:
            raise OSError("simulated disk failure")
        return real_save(path, data, raise_errors=raise_errors)

    monkeypatch.setattr(library_service, "save_json", flaky_save)
    with pytest.raises(OSError, match="simulated disk failure"):
        library_service.restore_backup(backup)

    assert json.loads(first.read_text(encoding="utf-8")) == {"old": 1}
    assert json.loads(second.read_text(encoding="utf-8")) == {"old": 2}


def test_round18_network_and_probe_cancellation_contracts_are_present() -> None:
    network = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    probe = (ROOT / "audioknigi/download/probe.py").read_text(encoding="utf-8")
    assert 'part.with_name(part.name + ".assembling").unlink(missing_ok=True)' in network
    assert "replace_with_retry(assembling, target)" in network
    assert 'wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)' in probe
    assert 'cancel_active = getattr(self, "_cancel_active_subprocesses", None)' in probe


def test_round18_full_mp3_history_and_event_sound_hardening_contracts() -> None:
    engine = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    sounds = (ROOT / "audioknigi/qt/event_sounds.py").read_text(encoding="utf-8")
    assert "history_saved = bool(save_json(HISTORY_FILE" in engine
    assert "replace_with_retry(source_target, target)" in engine
    assert "replace_with_retry(source_target, retained)" in engine
    assert sounds.count("player.setAudioOutput(None)") >= 2


def test_round18_accessibility_and_easy_settings_contracts() -> None:
    search_model = (ROOT / "audioknigi/qt/search_model.py").read_text(encoding="utf-8")
    settings = (ROOT / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    accessibility = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert "Qt.ItemDataRole.AccessibleDescriptionRole" in search_model
    assert "Merely saving unrelated settings in Easy mode must not erase" in settings
    assert 'combo.accessibleName() or self._l("Список")' in accessibility
    assert "combo.objectName()" not in accessibility.split("def _announce_combo_value", 1)[1].split("@Slot(int)", 1)[0]


def test_round18_explicit_cancel_stops_dropped_url_batch() -> None:
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    cancelled = source.split('if kind == "cancelled":', 1)[1].split('if kind == "error":', 1)[0]
    assert "self._pending_queue_urls = []" in cancelled
    assert "self._queue_next_dropped_url" not in cancelled


def test_round18_media_key_registration_rechecks_native_window_handle() -> None:
    source = (ROOT / "audioknigi/qt/media_keys.py").read_text(encoding="utf-8")
    assert "new_hwnd = int(pointer_value)" in source
    assert "self._hwnd == new_hwnd" in source
    assert "self._hwnd != new_hwnd" in source
