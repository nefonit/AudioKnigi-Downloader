from pathlib import Path


def test_event_bus_has_no_return_in_finally_reschedule_block():
    source = (Path(__file__).resolve().parents[1] / "audioknigi" / "event_bus.py").read_text(encoding="utf-8")
    assert "if self.closed:\n                self._after_id = None\n                return" not in source
    assert "if self.closed:\n                self._after_id = None\n            else:" in source


def test_windows_build_batch_files_have_no_utf8_bom():
    root = Path(__file__).resolve().parents[1]
    for name in ("build_exe.bat", "build_exe_fixed.bat"):
        data = (root / name).read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf"), name
        assert data.startswith(b"@echo off"), name
