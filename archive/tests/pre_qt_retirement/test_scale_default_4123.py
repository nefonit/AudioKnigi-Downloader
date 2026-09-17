"""Regression coverage for the 100% default and one-time legacy migration."""
from __future__ import annotations

import audioknigi.app as app_module
from audioknigi.core import DEFAULT_UI_SCALE, UI_SCALE_MIGRATION_KEY


def _settings_loader(scale_marker=None, *, migrated=False):
    def fake_load(path, default):
        if path == app_module.SETTINGS_FILE:
            data = {"first_run_complete": True}
            if scale_marker is not None:
                data["scale"] = scale_marker
            if migrated:
                data[UI_SCALE_MIGRATION_KEY] = True
            return data
        if path == app_module.HISTORY_FILE:
            return []
        return default
    return fake_load


def test_default_ui_scale_constant_is_100():
    assert DEFAULT_UI_SCALE == 100


def test_clean_profile_starts_at_100_percent(monkeypatch):
    monkeypatch.setattr(app_module, "load_json", _settings_loader())
    monkeypatch.setattr(app_module, "save_json", lambda *args, **kwargs: None)
    app = app_module.AudioKnigiApp()
    try:
        assert app.scale_var.get() == "100"
        # Applying the clean-profile scale must keep Tk at its captured native
        # DPI baseline rather than multiplying that baseline by 1.25.
        app._apply_scale(silent=True)
        current = float(app.tk.call("tk", "scaling"))
        assert abs(current - app._tk_base_scaling) < 0.05
    finally:
        app.destroy()


def test_legacy_saved_125_percent_is_migrated_once_to_100(monkeypatch):
    saved = []
    monkeypatch.setattr(app_module, "load_json", _settings_loader(125))
    monkeypatch.setattr(app_module, "save_json", lambda path, data: saved.append((path, dict(data))))
    app = app_module.AudioKnigiApp()
    try:
        assert app.scale_var.get() == "100"
        assert app.settings[UI_SCALE_MIGRATION_KEY] is True
        assert any(data.get("scale") == 100 for _path, data in saved)
    finally:
        app.destroy()


def test_user_selected_125_is_preserved_after_migration_marker(monkeypatch):
    monkeypatch.setattr(app_module, "load_json", _settings_loader(125, migrated=True))
    monkeypatch.setattr(app_module, "save_json", lambda *args, **kwargs: None)
    app = app_module.AudioKnigiApp()
    try:
        assert app.scale_var.get() == "125"
    finally:
        app.destroy()
