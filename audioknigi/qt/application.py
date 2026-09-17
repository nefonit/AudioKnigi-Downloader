from __future__ import annotations

import os
import sys

from PySide6.QtGui import QFont, QFontInfo, QIcon
from PySide6.QtWidgets import QApplication

from ..brand import DISPLAY_NAME
from ..core import resource_path, safe_int
from ..metadata import APP_VERSION
from ..config.settings import load_app_settings, normalize_settings, save_app_settings
from ..crash_report import build_report
from ..network_dns import install_cloudflare_dns, shutdown_cloudflare_playwright_proxy
from .main_window import AudioKnigiQtWindow
from .onboarding import QtFirstRunWizard
from .theme import apply_theme
from .accessibility_trace import extract_focus_trace_argument, install_focus_trace


def apply_ui_scale(app: QApplication, settings: dict) -> None:
    """Apply scale from an unscaled baseline so repeated calls never compound."""
    base_font = getattr(app, "_audioknigi_base_font_py", None)
    if not isinstance(base_font, QFont):
        base_font = QFont(app.font())
        app._audioknigi_base_font_py = QFont(base_font)
        app.setProperty("audioknigi_base_font", QFont(base_font))
    else:
        base_font = QFont(base_font)

    scale = max(80, min(200, safe_int(settings.get("scale", 100), 100)))
    multiplier = scale / 100.0
    if bool(settings.get("large_mode", False)):
        multiplier *= 1.15
    point_size = base_font.pointSizeF()
    if point_size > 0 and abs(multiplier - 1.0) > 0.001:
        base_font.setPointSizeF(point_size * multiplier)
    elif base_font.pixelSize() > 0 and abs(multiplier - 1.0) > 0.001:
        base_font.setPixelSize(max(1, int(round(base_font.pixelSize() * multiplier))))
    elif abs(multiplier - 1.0) > 0.001:
        # Some platform themes expose neither a valid pointSizeF nor pixelSize
        # on the application font. QFontInfo resolves the effective native size.
        effective = float(QFontInfo(base_font).pointSizeF())
        if effective > 0:
            base_font.setPointSizeF(effective * multiplier)
    app.setFont(base_font)


def create_application(argv=None, *, settings: dict | None = None) -> QApplication:
    raw_argv = list(sys.argv if argv is None else argv)
    clean_argv, _trace_path = extract_focus_trace_argument(raw_argv)
    app = QApplication.instance()
    if app is None:
        app = QApplication(clean_argv)
    app.setApplicationName(DISPLAY_NAME)
    app.setApplicationDisplayName(DISPLAY_NAME)
    app.setApplicationVersion(APP_VERSION)
    icon = resource_path("assets", "app_icon.png")
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))

    if settings is None:
        settings = load_app_settings().to_dict()
    else:
        settings = normalize_settings(settings)
    apply_ui_scale(app, settings)
    return app


def run_qt(argv=None) -> int:
    raw_argv = list(sys.argv if argv is None else argv)
    try:
        clean_argv, trace_path = extract_focus_trace_argument(raw_argv)
    except ValueError as exc:
        try:
            build_report(type(exc), exc, exc.__traceback__, component="qt-arguments")
        except Exception:
            pass
        try:
            sys.stderr.write(f"{exc}\n")
        except Exception:
            pass
        return 2
    install_cloudflare_dns()
    settings = load_app_settings().to_dict()
    app = create_application(clean_argv, settings=settings)
    original_excepthook = sys.excepthook

    def _exception_hook(exc_type, exc, tb):
        try:
            build_report(exc_type, exc, tb, component="qt-application")
        finally:
            hook = original_excepthook
            if callable(hook) and hook is not _exception_hook:
                try:
                    hook(exc_type, exc, tb)
                except Exception:
                    pass
    sys.excepthook = _exception_hook
    focus_tracer = install_focus_trace(app, trace_path)
    app.aboutToQuit.connect(shutdown_cloudflare_playwright_proxy)

    # First-run setup happens before the main window is constructed.  This keeps
    # the welcome screen compact and ensures the selected language/theme/mode are
    # already active when the product UI first appears.
    try:
        apply_theme(app, str(settings.get("theme", "system") or "system"))
    except Exception:
        pass
    if not bool(settings.get("first_run_complete", False)):
        onboarding = QtFirstRunWizard(None, settings=settings)
        accepted = bool(onboarding.exec())
        if not accepted:
            # Closing/cancelling the optional first-run wizard means "skip".
            # Persist the choice and continue into the main application.
            settings["first_run_complete"] = True
            save_app_settings(settings)
        else:
            settings = onboarding.result_settings()
            save_app_settings(settings)
            # The onboarding selection must be reflected in the first main-window
            # paint, not only after the next application restart.
            try:
                apply_theme(app, str(settings.get("theme", "system") or "system"))
                apply_ui_scale(app, settings)
            except Exception:
                pass

    app.setProperty("audioknigi_language", str(settings.get("language", "ru") or "ru"))
    window = AudioKnigiQtWindow()
    if os.name == "nt" and not settings.get("geometry"):
        window.showMaximized()
    else:
        window.show()
    try:
        return int(app.exec())
    finally:
        sys.excepthook = original_excepthook
        if focus_tracer is not None:
            focus_tracer.close()


__all__ = ["apply_ui_scale", "create_application", "run_qt"]
