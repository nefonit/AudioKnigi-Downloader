from pathlib import Path
from types import SimpleNamespace

import audioknigi.core as core


ROOT = Path(__file__).resolve().parents[1]


def test_build_script_rejects_chocolatey_bin_shims_and_resolves_real_binary():
    text = (ROOT / "build_ci.ps1").read_text(encoding="utf-8-sig")
    assert "Resolve-RealMediaTool" in text
    assert "Test-IsChocolateyBinShim" in text
    assert "Skipping Chocolatey shim" in text
    assert "Real FFmpeg for bundle" in text
    assert '"--add-binary", "$ffmpeg;."' in text
    assert '"--add-binary", "$ffprobe;."' in text


def test_resolve_executable_skips_broken_bundled_media_tool(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    system = tmp_path / "system"
    bundle.mkdir()
    system.mkdir()
    bundled = bundle / "ffmpeg"
    working = system / "ffmpeg"
    bundled.write_bytes(b"shim")
    working.write_bytes(b"real")

    monkeypatch.setattr(core.sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr(core.sys, "executable", str(tmp_path / "app" / "python"))
    monkeypatch.setattr(core.shutil, "which", lambda name: str(working))

    def fake_run(argv, **kwargs):
        return SimpleNamespace(returncode=(-1 if str(argv[0]) == str(bundled) else 0))

    monkeypatch.setattr(core.subprocess, "run", fake_run)
    with core._EXECUTABLE_CACHE_LOCK:
        core._EXECUTABLE_CACHE.clear()

    assert core.resolve_executable("ffmpeg") == str(working)
