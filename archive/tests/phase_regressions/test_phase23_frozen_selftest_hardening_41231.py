from __future__ import annotations

import importlib.metadata as metadata
from pathlib import Path

import audioknigi_qt


def test_safe_distribution_version_falls_back_when_metadata_is_missing(monkeypatch):
    def missing(_name: str):
        raise metadata.PackageNotFoundError(_name)

    monkeypatch.setattr(metadata, "version", missing)
    assert audioknigi_qt._safe_distribution_version("PySide6", "6.test") == "6.test"
    assert audioknigi_qt._safe_distribution_version("playwright") == "unknown"


def test_official_pyinstaller_build_copies_selftest_metadata():
    source = Path("build_qt_ci.ps1").read_text(encoding="utf-8")
    assert '"--copy-metadata", "PySide6"' in source
    assert '"--copy-metadata", "playwright"' in source


def test_accessibility_selftest_cleans_event_sounds_before_app_disposal():
    source = Path("audioknigi_qt.py").read_text(encoding="utf-8")
    sound_shutdown = 'window.event_sound_manager.shutdown()'
    deferred_delete = 'QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)'
    assert sound_shutdown in source
    assert deferred_delete in source
    assert 'shiboken_delete(app)' not in source
    assert source.index(sound_shutdown) < source.index(deferred_delete)
    assert 'app.quit()' in source


def test_event_sound_shutdown_uses_bounded_worker_join():
    source = Path("audioknigi/qt/event_sounds.py").read_text(encoding="utf-8")
    assert "thread.join(timeout=0.75)" in source
