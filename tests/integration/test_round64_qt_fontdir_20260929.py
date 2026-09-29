from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_manual_qt_build_sets_windows_fontdir_without_overriding_caller():
    source = (ROOT / "build_qt_exe.bat").read_text(encoding="utf-8")
    assert 'if not defined QT_QPA_FONTDIR if exist "%WINDIR%\\Fonts"' in source
    assert 'set "QT_QPA_FONTDIR=%WINDIR%\\Fonts"' in source


def test_ci_qt_build_initializes_windows_fontdir_for_direct_invocation():
    source = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    assert "function Initialize-QtFontDirectory" in source
    assert '$env:QT_QPA_FONTDIR' in source
    assert 'Join-Path $env:WINDIR "Fonts"' in source
    assert "Initialize-QtFontDirectory" in source
    assert 'if (-not [string]::IsNullOrWhiteSpace($env:QT_QPA_FONTDIR))' in source


def test_round64_does_not_bundle_font_files():
    build_bat = (ROOT / "build_qt_exe.bat").read_text(encoding="utf-8").casefold()
    build_ps1 = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8").casefold()
    assert "dejavu" not in build_bat + build_ps1
    assert "copy" not in "\n".join(
        line for line in (build_bat + "\n" + build_ps1).splitlines() if "font" in line
    )
