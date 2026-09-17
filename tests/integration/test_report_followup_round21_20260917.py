from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

from audioknigi import core, knigavuhe, poleknig
from audioknigi.diagnostics.support_bundle import create_support_bundle
from audioknigi.download_engine import _DownloadEngine
from audioknigi.services.player_position_store import PlayerPositionStore


ROOT = Path(__file__).resolve().parents[2]


def test_save_json_retries_transient_replace_lock(tmp_path, monkeypatch) -> None:
    target = tmp_path / "settings.json"
    real_replace = core.os.replace
    attempts = {"count": 0}

    def flaky_replace(source, destination):
        if Path(destination) == target and attempts["count"] < 2:
            attempts["count"] += 1
            raise PermissionError("sharing violation")
        return real_replace(source, destination)

    monkeypatch.setattr(core.os, "replace", flaky_replace)
    assert core.save_json(target, {"round": 21}, raise_errors=True)
    assert target.read_text(encoding="utf-8").strip().endswith("}")
    assert attempts["count"] == 2


def test_delete_existing_outputs_uses_retry_helper(tmp_path, monkeypatch) -> None:
    target = tmp_path / "book.mp3"
    target.write_bytes(b"old")
    engine = object.__new__(_DownloadEngine)
    engine.request = SimpleNamespace(book=SimpleNamespace())
    engine._book_folder = lambda *_a, **_k: tmp_path
    engine._full_mp3_target = lambda *_a, **_k: target

    calls = []

    def fake_unlink(path, *, missing_ok=True, attempts=5):
        calls.append((Path(path), missing_ok, attempts))
        Path(path).unlink(missing_ok=missing_ok)
        return True

    import audioknigi.download_engine as engine_module

    monkeypatch.setattr(engine_module, "unlink_with_retry", fake_unlink)
    assert engine.delete_existing_outputs(full_mp3=True) == 1
    assert calls and calls[0][0] == target
    assert not target.exists()


def test_knigavuhe_script_fallback_exposes_current_narration_variant() -> None:
    html = '''
        <html><head><title>Тестовая книга — автор Автор Тест</title></head>
        <body><script>const audio = "https://cdn.example.test/book/001.mp3";</script></body></html>
    '''
    book = knigavuhe._fallback_script_book(html, "https://knigavuhe.org/book/test/")
    assert book is not None
    assert len(book.narration_variants) == 1
    variant = book.narration_variants[0]
    assert variant.current is True
    assert variant.available is True
    assert variant.url == book.url
    assert variant.title == book.title


def test_poleknig_author_keys_accept_initials_but_reject_unrelated_people() -> None:
    full = poleknig._person_key("Илья Ильф, Евгений Петров")
    initials = poleknig._person_key("И. Ильф, Е. Петров")
    unrelated = poleknig._person_key("Иван Бунин")
    assert poleknig._person_keys_compatible(full, initials)
    assert poleknig._person_keys_compatible(initials, full)
    assert not poleknig._person_keys_compatible(full, unrelated)


def test_network_cleanup_uses_windows_retry_helper_everywhere() -> None:
    source = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    assert "from .common import atomic_write_text, replace_with_retry, unlink_with_retry" in source
    assert ".unlink(" not in source
    assert "unlink_with_retry(seg, missing_ok=True)" in source
    assert 'unlink_with_retry(part.with_name(part.name + ".assembling"), missing_ok=True)' in source


def test_support_bundle_trailing_separator_means_explicit_missing_directory(tmp_path) -> None:
    folder = tmp_path / "new-diagnostics"
    target = create_support_bundle(str(folder) + os.sep, settings={"language": "en"})
    assert folder.is_dir()
    assert target.parent == folder
    assert target.name.startswith("support_bundle_")
    assert target.suffix == ".zip"


def test_player_position_store_rejects_empty_media_path(tmp_path) -> None:
    store_path = tmp_path / "positions.json"
    store = PlayerPositionStore(store_path)
    assert PlayerPositionStore.key("") == ""
    assert store.saved_seconds("") == 0.0
    assert store.update("", 120.0, 600.0) is False
    assert store.clear("") is False
    assert store.snapshot() == {}
    assert not store_path.exists()


def test_round21_does_not_change_queue_empty_selection_or_proxy_drain_contracts() -> None:
    queue_source = (ROOT / "audioknigi/services/queue_service.py").read_text(encoding="utf-8")
    assert 'An explicit empty' in queue_source
    assert 'return result' in queue_source

    proxy_source = (ROOT / "audioknigi/network_dns.py").read_text(encoding="utf-8")
    assert "half_close_deadline" in proxy_source
    assert "return_when_right_closes=True" in proxy_source


def test_ci_installs_pytest_and_python314_synthetic_global_is_allowlisted() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    audit = (ROOT / "tools/undefined_global_audit.py").read_text(encoding="utf-8")
    assert "python -m pip install pytest" in ci
    assert "choco install ffmpeg -y --no-progress" in ci
    assert '"__conditional_annotations__"' in audit
