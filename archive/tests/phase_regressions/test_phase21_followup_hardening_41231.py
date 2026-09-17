from __future__ import annotations

from pathlib import Path

from audioknigi.sources import is_supported_url, normalize_supported_url

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_poleknig_slug_urls_are_supported_and_canonicalized():
    samples = [
        "https://poleknig.com/books/17392-skazka-o-tsare-saltane",
        "https://poleknig.com/books/17392-skazka-o-tsare-saltane/",
        "https://www.poleknig.com/books/17392-%D1%81%D0%BA%D0%B0%D0%B7%D0%BA%D0%B0/?utm_source=test#chapter",
        "poleknig.com/books/17392-master-i-margarita",
    ]
    for value in samples:
        assert is_supported_url(value) is True
        assert normalize_supported_url(value) == "https://poleknig.com/books/17392"


def test_poleknig_nested_non_book_paths_are_not_accepted():
    assert not is_supported_url("https://poleknig.com/books/17392/part-1/")
    assert not is_supported_url("https://poleknig.com/books/17392-")


def test_knigavuhe_cancel_event_and_duplicate_preflight_fix_are_still_present():
    downloader = text("audioknigi/downloader.py")
    engine = text("audioknigi/download_engine.py")
    assert "fetch_knigavuhe_book(url, cancel_event=self.cancel_event)" in downloader
    assert "def _book_folder(self, book, *, create=True):" in downloader
    assert "create=create" in downloader
    assert "self._book_folder(book, create=False)" in engine


def test_deferred_exit_has_bounded_grace_period_and_emergency_fallback():
    source = text("audioknigi/qt/main_window.py")
    body = source[source.index("def _running_exit_threads"):source.index("__all__", source.index("def closeEvent"))]
    assert "_EXIT_GRACE_SECONDS = 5.0" in source
    assert "self._exit_deadline = time.monotonic() + _EXIT_GRACE_SECONDS" in body
    assert "thread.terminate()" not in body
    assert "thread.wait(_EXIT_FINAL_WAIT_MS)" in body
    assert "os._exit(0)" in body
    assert "self._schedule_exit_poll()" in body
    assert "QTimer.singleShot(_EXIT_POLL_MS, self._poll_deferred_exit)" in body


def test_accessibility_selftest_restores_qpa_environment_and_reuses_existing_qapplication():
    source = text("audioknigi_qt.py")
    body = source[source.index("def _qt_accessibility_selftest"):source.index("def _playwright_edge_selftest")]
    assert 'had_qpa_platform = "QT_QPA_PLATFORM" in os.environ' in body
    assert "existing_app = QApplication.instance()" in body
    assert 'os.environ["QT_QPA_PLATFORM"] = "offscreen"' in body
    assert 'os.environ.pop("QT_QPA_PLATFORM", None)' in body
    assert "owns_app" in body
    assert "shiboken_delete(app)" not in body
    assert "app.quit()" in body
