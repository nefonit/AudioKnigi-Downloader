"""Qt/PySide6 production application entry point.

The active runtime is Qt-only. Tk retirement happened in the earlier Phase 13
migration. Historical compatibility note: Phase 39 is Qt-only; archived checks
retain that later-development marker without attributing Tk retirement to it.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import traceback

from audioknigi.metadata import APP_VERSION


def _report_path(env_name: str, frozen_name: str) -> Path | None:
    configured = str(os.environ.get(env_name, "") or "").strip()
    if configured:
        return Path(configured)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / frozen_name
    return None


def _write_report(env_name: str, frozen_name: str, text: str) -> None:
    path = _report_path(env_name, frozen_name)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(text), encoding="utf-8")
    except Exception as exc:
        print(f"SELFTEST REPORT WRITE FAILED: {exc}", file=sys.stderr)


def _safe_distribution_version(package_name: str, fallback: str = "unknown") -> str:
    """Return package metadata version without making frozen self-tests depend on dist-info."""
    try:
        import importlib.metadata as metadata

        return str(metadata.version(package_name))
    except Exception:
        value = str(fallback or "").strip()
        return value or "unknown"


def _qt_runtime_selftest() -> int:
    """Verify the frozen/source Qt runtime without creating a GUI window."""
    env_name = "AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT"
    filename = "qt_runtime_frozen_selftest.txt"
    try:
        import PySide6
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
        from PySide6.QtWidgets import QSystemTrayIcon

        from audioknigi.download_engine import DownloadService
        from audioknigi.qt import QT_MIGRATION_STAGE, QT_RUNTIME_STAGE
        from audioknigi.qt.main_window import AudioKnigiQtWindow
        from audioknigi.qt_runtime_audit import assert_qt_runtime_clean
        from audioknigi.services.book_analysis_service import BookAnalysisService
        from audioknigi.services.download_request import DownloadRequest
        from audioknigi.services.search_service import SearchOutcome

        if SearchOutcome("abc").query != "abc":
            raise RuntimeError("SearchOutcome runtime contract failed")
        required_objects = {
            "BookAnalysisService": BookAnalysisService,
            "DownloadRequest": DownloadRequest,
            "DownloadService": DownloadService,
            "AudioKnigiQtWindow": AudioKnigiQtWindow,
            "QMediaPlayer": QMediaPlayer,
            "QAudioOutput": QAudioOutput,
            "QSystemTrayIcon": QSystemTrayIcon,
        }
        missing = [name for name, value in required_objects.items() if value is None]
        if missing:
            raise RuntimeError("Qt runtime imports are unavailable: " + ", ".join(missing))
        assert_qt_runtime_clean()

        report = (
            f"OK\napp={APP_VERSION}\n"
            f"stage={QT_RUNTIME_STAGE}\n"
            f"migration_stage={QT_MIGRATION_STAGE}\n"
            f"pyside6={PySide6.__version__}\n"
            f"pyside6_distribution={_safe_distribution_version('PySide6', getattr(PySide6, '__version__', 'unknown'))}\n"
            "legacy_runtime_modules=none\n"
            "qt_multimedia=OK\n"
            "qt_system_tray=OK\n"
        )
        _write_report(env_name, filename, report)
        print(f"QT RUNTIME SELFTEST: OK (PySide6 {PySide6.__version__}, {QT_RUNTIME_STAGE})")
        return 0
    except Exception:
        details = "FAILED\n" + traceback.format_exc()
        _write_report(env_name, filename, details)
        print(details, file=sys.stderr, end="" if details.endswith("\n") else "\n")
        print("QT RUNTIME SELFTEST: FAILED", file=sys.stderr)
        return 25


def _qt_accessibility_selftest() -> int:
    """Instantiate the Qt window offscreen and verify the accessibility contract."""
    env_name = "AUDIOKNIGI_QT_ACCESSIBILITY_SELFTEST_REPORT"
    filename = "qt_accessibility_frozen_selftest.txt"
    window = None
    app = None
    owns_app = False
    had_qpa_platform = "QT_QPA_PLATFORM" in os.environ
    previous_qpa_platform = os.environ.get("QT_QPA_PLATFORM")
    try:
        # If a QApplication already exists (for example in an in-process test
        # runner), reuse it rather than attempting to construct a forbidden
        # second singleton.  Only a selftest-owned application needs the
        # offscreen platform override.
        from PySide6.QtWidgets import QApplication

        existing_app = QApplication.instance()
        if existing_app is None:
            # This command is explicitly an offscreen self-test. Override even
            # a caller-provided platform value while we own QApplication, then
            # restore the original environment exactly in finally.
            os.environ["QT_QPA_PLATFORM"] = "offscreen"

        from audioknigi.qt import QT_MIGRATION_STAGE, QT_RUNTIME_STAGE
        from audioknigi.qt.accessibility_audit import audit_accessibility_window
        from audioknigi.qt.application import create_application
        from audioknigi.qt.main_window import AudioKnigiQtWindow

        if existing_app is None:
            app = create_application([sys.argv[0], "-platform", "offscreen"])
            owns_app = True
        else:
            app = existing_app
        window = AudioKnigiQtWindow()
        result = audit_accessibility_window(window)
        audit_text = result.report().rstrip("\n") + "\n"
        report = (
            audit_text
            + f"app={APP_VERSION}\n"
            + f"stage={QT_RUNTIME_STAGE}\n"
            + f"migration_stage={QT_MIGRATION_STAGE}\n"
            + "screen_reader=manual_acceptance_required\n"
        )
        _write_report(env_name, filename, report)
        if not result.ok:
            print(report, file=sys.stderr, end="" if report.endswith("\n") else "\n")
            print("QT ACCESSIBILITY SELFTEST: FAILED", file=sys.stderr)
            return 26
        print(f"QT ACCESSIBILITY SELFTEST: OK ({result.checked} controls, {QT_RUNTIME_STAGE})")
        return 0
    except Exception:
        details = "FAILED\n" + traceback.format_exc()
        _write_report(env_name, filename, details)
        print(details, file=sys.stderr, end="" if details.endswith("\n") else "\n")
        print("QT ACCESSIBILITY SELFTEST: FAILED", file=sys.stderr)
        return 26
    finally:
        try:
            if window is not None:
                # Exercise closeEvent first, but a persistence failure must not
                # prevent native multimedia/tray resources from being released.
                try:
                    window.close()
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                if getattr(window, "player_controller", None) is not None:
                    try:
                        window.player_controller.shutdown()
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                if getattr(window, "event_sound_manager", None) is not None:
                    try:
                        window.event_sound_manager.shutdown()
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                if getattr(window, "tray_controller", None) is not None:
                    try:
                        window.tray_controller.shutdown()
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                try:
                    window.deleteLater()
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                window = None
            if app is not None:
                # Flush DeferredDelete/native cleanup before touching QApplication.
                from PySide6.QtCore import QCoreApplication, QEvent

                send_posted_events = QCoreApplication.sendPostedEvents
                try:
                    send_posted_events(None, QEvent.Type.DeferredDelete)
                except TypeError:
                    try:
                        send_posted_events(event_type=QEvent.Type.DeferredDelete)
                    except TypeError:
                        send_posted_events()
                app.processEvents()
            if owns_app and app is not None:
                # Qt documents QApplication as a process-wide singleton.  Forcing
                # its C++ destruction through shiboken while style/clipboard/
                # accessibility singletons still exist can cause access violations
                # in in-process test runners. Quit cleanly and let process teardown
                # own the singleton lifetime instead.
                app.quit()
                app.processEvents()
        except Exception:
            traceback.print_exc(file=sys.stderr)
        finally:
            window = None
            app = None
            # Restore the caller's environment exactly; never leak "offscreen"
            # into a later normal GUI launch.
            if had_qpa_platform:
                os.environ["QT_QPA_PLATFORM"] = previous_qpa_platform or ""
            else:
                os.environ.pop("QT_QPA_PLATFORM", None)


def _playwright_edge_selftest() -> int:
    """Prove packaged Playwright can control installed Microsoft Edge."""
    env_name = "AUDIOKNIGI_PLAYWRIGHT_SELFTEST_REPORT"
    filename = "playwright_edge_qt_frozen_selftest.txt"
    try:
        import playwright
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=True)
            try:
                browser_version = str(browser.version or "")
            finally:
                browser.close()
        report = (
            f"OK\napp={APP_VERSION}\n"
            f"playwright={_safe_distribution_version('playwright', getattr(playwright, '__version__', 'unknown'))}\n"
            f"playwright_path={getattr(playwright, '__file__', '')}\n"
            "browser_channel=msedge\n"
            f"browser_version={browser_version}\n"
        )
        _write_report(env_name, filename, report)
        print(f"PLAYWRIGHT EDGE SELFTEST: OK (Edge {browser_version})")
        return 0
    except Exception:
        details = "FAILED\n" + traceback.format_exc()
        _write_report(env_name, filename, details)
        print(details, file=sys.stderr, end="" if details.endswith("\n") else "\n")
        print("PLAYWRIGHT EDGE SELFTEST: FAILED", file=sys.stderr)
        return 24


def main() -> int:
    if "--version" in sys.argv:
        print(f"AudioKnigi Downloader {APP_VERSION}")
        return 0
    if "--qt-selftest" in sys.argv or "--qt-runtime-selftest" in sys.argv:
        return _qt_runtime_selftest()
    if "--qt-accessibility-selftest" in sys.argv:
        return _qt_accessibility_selftest()
    if "--playwright-edge-selftest" in sys.argv:
        return _playwright_edge_selftest()

    from audioknigi.qt.application import run_qt

    return run_qt(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
