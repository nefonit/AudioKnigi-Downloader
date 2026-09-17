from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def test_release_hash_does_not_depend_on_get_filehash_cmdlet():
    build = text("build_qt_ci.ps1")
    assert "function Get-Sha256Hex" in build
    assert "[System.Security.Cryptography.SHA256]::Create()" in build
    assert "[System.IO.File]::OpenRead($Path)" in build
    assert "$exeHash = (Get-Sha256Hex -Path $exe).ToLowerInvariant()" in build
    assert "Get-FileHash -LiteralPath $exe" not in build


def test_queued_ui_mode_focus_is_safe_during_window_teardown():
    source = text("audioknigi/qt/main_window.py")
    block = source[source.index("    def set_ui_mode("):source.index("    def current_ui_mode", source.index("    def set_ui_mode("))]
    assert "target_ref = weakref.ref(target)" in block
    assert "def focus_target_if_alive()" in block
    assert "except RuntimeError:" in block
    assert "QTimer.singleShot(0, focus_target_if_alive)" in block
    assert "lambda: target.setFocus" not in block
