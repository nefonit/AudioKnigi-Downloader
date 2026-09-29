from __future__ import annotations

import json
from pathlib import Path

from audioknigi.brand import (
    AUTHOR_EMAIL, AUTHOR_GITHUB_URL, AUTHOR_NAME, COPYRIGHT_YEAR, PROJECT_URL,
)
from tools.windows_version_info import render_version_info

ROOT = Path(__file__).resolve().parents[2]


def test_creator_identity_constants_are_canonical():
    assert AUTHOR_NAME == "Едуард Саратовцев"
    assert AUTHOR_EMAIL == "serioussem39@gmail.com"
    assert AUTHOR_GITHUB_URL == "https://github.com/nefonit"
    assert PROJECT_URL == "https://github.com/nefonit/AudioKnigi-Downloader"
    assert COPYRIGHT_YEAR == 2026


def test_about_dialog_exposes_creator_and_keyboard_actions():
    source = (ROOT / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    block = source[source.index("def _show_about"):source.index("__all__", source.index("def _show_about"))]
    assert "QDialog(self)" in block
    assert "QTextBrowser(dialog)" in block
    assert "AUTHOR_NAME" in block
    assert "AUTHOR_EMAIL" in block
    assert "AUTHOR_GITHUB_URL" in block
    assert "PROJECT_URL" in block
    assert "QDesktopServices.openUrl" in block
    assert "QApplication.clipboard().setText(AUTHOR_EMAIL)" in block
    assert "text.setFocus" in block


def test_about_localization_exists_in_all_languages():
    data = json.loads((ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8"))
    keys = {
        "about_window_title", "about_summary", "about_author_role",
        "about_accessibility_note", "about_email_label", "about_github_label",
        "about_project_label", "about_write_email", "about_copy_email",
        "about_open_github", "about_open_project", "about_email_copied",
        "about_info_accessible",
    }
    for language in ("ru", "en", "de", "uk"):
        assert keys <= set(data[language])
        assert all(str(data[language][key]).strip() for key in keys)


def test_windows_version_info_contains_creator_and_product_identity():
    text = render_version_info()
    assert "Едуард Саратовцев" in text
    assert "Автор и разработчик: Едуард Саратовцев" in text
    assert "AudioKnigi Downloader" in text
    assert "AudioKnigiDownloader_Qt.exe" in text
    assert "© 2026 Едуард Саратовцев" in text
    assert "filevers=(4, 12, 42, 0)" in text


def test_qt_build_supplies_generated_version_resource_to_pyinstaller():
    source = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    assert 'tools\\windows_version_info.py' in source
    assert '"--version-file", $versionInfoFile' in source
