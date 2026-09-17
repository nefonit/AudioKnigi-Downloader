"""4.12.31 regressions for compact Windows one-file builds."""
from pathlib import Path

from audioknigi import network_dns


ROOT = Path(__file__).resolve().parents[1]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8-sig")


def test_playwright_runtime_uses_installed_edge_channel():
    options = network_dns.cloudflare_playwright_launch_kwargs()
    assert options["channel"] == "msedge"
    assert options["headless"] is True
    assert options["proxy"]["server"].startswith("http://127.0.0.1:")
    assert "--disable-quic" in options["args"]


def test_build_scripts_do_not_install_or_embed_playwright_chromium():
    for name in ("build_ci.ps1", "build_exe.bat", "build_exe_fixed.bat"):
        text = _text(name).lower()
        assert "playwright install chromium" not in text
        assert 'playwright_browsers_path=0' not in text
        assert ".local-browsers" in text
        assert "msedge" in text


def test_build_ci_keeps_playwright_driver_but_drops_broad_collect_all_for_small_packages():
    text = _text("build_ci.ps1")
    assert '"--collect-all", "playwright"' in text
    # The installed browser folder is removed before collect-all runs.
    assert "Removing previously embedded Playwright browsers" in text
    for package in ("PIL", "mutagen", "pygame", "tkinterdnd2", "ttkbootstrap", "pystray"):
        assert f'"--collect-all", "{package}"' not in text
    assert '"--collect-data", "ttkbootstrap"' in text
    assert '"--hidden-import", "pystray._win32"' in text


def test_frozen_exe_selftests_playwright_driver_against_edge():
    gui = _text("audioknigi_gui.py")
    build = _text("build_ci.ps1")
    assert '"--playwright-edge-selftest"' in gui
    assert 'channel="msedge"' in gui
    assert "playwright_edge_frozen_selftest.txt" in gui
    assert "--playwright-edge-selftest" in build
    assert "playwright_edge_frozen_selftest.txt" in build
    assert "Final EXE size:" in build


def test_tkinterdnd2_data_is_still_packaged_by_project_hook():
    hook = _text("hook-tkinterdnd2.py")
    assert 'collect_data_files("tkinterdnd2")' in hook
