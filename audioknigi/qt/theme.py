from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


THEMES = ("system", "light", "dark")
_SYSTEM_STYLE_NAME: str | None = None
_SYSTEM_PALETTE: QPalette | None = None
_APPLIED_STYLE_KEY: str | None = None


def _capture_system_appearance(app: QApplication) -> None:
    global _SYSTEM_STYLE_NAME, _SYSTEM_PALETTE
    if _SYSTEM_STYLE_NAME is None:
        try:
            _SYSTEM_STYLE_NAME = str(app.style().objectName() or "")
        except Exception:
            _SYSTEM_STYLE_NAME = ""
    if _SYSTEM_PALETTE is None:
        _SYSTEM_PALETTE = QPalette(app.palette())


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#181a1f"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f2f4f8"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111318"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#20232a"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#f2f4f8"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#111318"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f2f4f8"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#252932"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f2f4f8"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0a6ed1"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#7f8794"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#7f8794"))
    return palette


def _light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f7fa"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#17202a"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f1f4f8"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#17202a"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#17202a"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#17202a"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0066cc"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#8a94a3"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#8a94a3"))
    return palette


def _stylesheet(mode: str, palette: QPalette | None = None) -> str:
    if mode == "dark":
        surface = "#22262e"
        surface2 = "#292e38"
        border = "#3a414d"
        text = "#f2f4f8"
        muted = "#aab2bf"
        onboarding_muted = "#aab2bf"
        input_bg = "#15181e"
        disabled_bg = "#232730"
        disabled_text = "#727b88"
        nav_hover = "#303641"
    elif mode == "light":
        surface = "#ffffff"
        surface2 = "#f8fafc"
        border = "#d8dee8"
        text = "#17202a"
        muted = "#687386"
        onboarding_muted = "#687386"
        input_bg = "#ffffff"
        disabled_bg = "#eef1f5"
        disabled_text = "#98a1ae"
        nav_hover = "#edf4fb"
    else:
        # Keep native/system colors where possible.  Detect whether Windows is
        # currently light or dark before choosing the onboarding subtitle color;
        # a fixed #aab2bf is readable on dark Windows but too pale on white.
        system_palette = palette or QPalette()
        try:
            system_dark = system_palette.color(QPalette.ColorRole.Window).lightness() < 128
        except Exception:
            system_dark = False
        surface = "palette(base)"
        surface2 = "palette(alternate-base)"
        border = "palette(mid)"
        text = "palette(text)"
        muted = "palette(mid)"
        onboarding_muted = "#aab2bf" if system_dark else "#566273"
        input_bg = "palette(base)"
        disabled_bg = "palette(button)"
        disabled_text = "palette(mid)"
        nav_hover = "palette(alternate-base)"

    return f"""
QPushButton {{
    min-height: 26px;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid {border};
}}
QPushButton:hover {{ border-color: #0a6ed1; }}
/* Keyboard focus must remain obvious even on blue primary buttons.
   A thick amber border provides both color and shape contrast in light, dark
   and native/system themes. */
QPushButton:focus {{ border: 3px solid #ffb000; padding: 4px 10px; }}
QPushButton:disabled {{ background: {disabled_bg}; color: {disabled_text}; border-color: {border}; }}
QPushButton[role="primary"] {{
    background: #0066cc;
    color: white;
    border: 1px solid #0066cc;
    font-weight: 600;
}}
QPushButton[role="primary"]:hover {{ background: #0875df; border-color: #0875df; }}
QPushButton[role="primary"]:pressed {{ background: #0059b3; }}
QPushButton[role="primary"]:disabled {{
    background: {disabled_bg};
    color: {disabled_text};
    border-color: {border};
    font-weight: 600;
}}
QPushButton[role="danger"] {{ background: #c93c37; color: white; border-color: #c93c37; font-weight: 600; }}
QPushButton[role="dangerGhost"] {{ color: #c93c37; }}
QPushButton[role="flat"] {{ background: transparent; border: none; text-align: left; padding-left: 2px; }}
QPushButton[role="segment"] {{
    border-radius: 12px;
    padding: 5px 14px;
    background: {surface2};
}}
QPushButton[role="segment"]:checked {{ background: #0066cc; color: white; border-color: #0066cc; font-weight: 600; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    min-height: 28px;
    padding: 4px 8px;
    border-radius: 6px;
    border: 1px solid {border};
    background: {input_bg};
    color: {text};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 3px solid #ffb000; }}
QPlainTextEdit:focus, QTextEdit:focus, QTableView:focus, QTableWidget:focus,
QListWidget:focus, QTreeView:focus {{ border: 3px solid #ffb000; }}
QCheckBox:focus, QRadioButton:focus {{ border: 2px solid #ffb000; border-radius: 4px; }}
QSlider:focus {{ border: 2px solid #ffb000; border-radius: 4px; }}
QTabBar:focus {{ border: 2px solid #ffb000; border-radius: 4px; }}
QTabBar::tab:selected {{ border: 2px solid #ffb000; font-weight: 600; }}
QProgressBar {{ border: 1px solid {border}; border-radius: 6px; min-height: 12px; text-align: center; }}
QProgressBar::chunk {{ background: #0a6ed1; border-radius: 5px; }}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 10px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
QWidget#easyCard, QWidget#playerCard {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 12px;
}}
QWidget#bookCard, QWidget#noticeCard {{
    background: {surface2};
    border: 1px solid {border};
    border-radius: 8px;
}}
QWidget#settingsFooter {{
    background: {surface2};
    border-top: 1px solid {border};
}}
QLabel#pageTitle {{ font-size: 20px; font-weight: 700; }}
QLabel#playerTitle {{ font-size: 22px; font-weight: 700; }}
QLabel#sectionTitle {{ font-size: 14px; font-weight: 600; margin-top: 6px; }}
QLabel#secondaryText {{ color: {muted}; }}
QLabel#onboardingSubtitle {{ color: {onboarding_muted}; }}
QLabel#emptyState {{ color: {muted}; padding: 18px; border: 1px dashed {border}; border-radius: 8px; }}
QLabel#coverPlaceholder {{
    color: {muted};
    background: {surface2};
    border: 1px dashed {border};
    border-radius: 8px;
    padding: 8px;
}}
QListWidget#playerChapters {{ background: {surface2}; }}
QLabel#bookMetadata {{ font-size: 14px; }}
QListWidget#settingsNav {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px;
}}
QListWidget#settingsNav::item {{ padding: 10px 12px; margin: 2px; border-radius: 6px; }}
QListWidget#settingsNav::item:hover {{ background: {nav_hover}; }}
QListWidget#settingsNav::item:selected {{ background: #0066cc; color: white; }}
QTableView, QTableWidget, QListWidget {{ border-radius: 6px; border: 1px solid {border}; }}
QTabWidget::pane {{ border: 1px solid {border}; border-radius: 6px; }}
"""


def apply_theme(app: QApplication, theme: str) -> str:
    """Apply an explicit high-contrast theme or restore the native system one."""
    global _APPLIED_STYLE_KEY
    _capture_system_appearance(app)
    mode = str(theme or "system").strip().lower()
    if mode not in THEMES:
        mode = "system"

    preserved_font = app.font()
    if mode in {"dark", "light"}:
        if _APPLIED_STYLE_KEY != "fusion":
            fusion = QStyleFactory.create("Fusion")
            if fusion is not None:
                try:
                    fusion.setObjectName("fusion")
                except Exception:
                    pass
                QApplication.setStyle(fusion)
                _APPLIED_STYLE_KEY = "fusion"
        app.setFont(preserved_font)
        app.setPalette(_dark_palette() if mode == "dark" else _light_palette())
        app.setStyleSheet(_stylesheet(mode))
        return mode

    if _SYSTEM_STYLE_NAME:
        try:
            current_style = str(app.style().objectName() or "")
        except Exception:
            current_style = ""
        if current_style.casefold() != _SYSTEM_STYLE_NAME.casefold():
            restored = QStyleFactory.create(_SYSTEM_STYLE_NAME)
            if restored is not None:
                QApplication.setStyle(restored)
    _APPLIED_STYLE_KEY = "system"
    app.setFont(preserved_font)
    if _SYSTEM_PALETTE is not None:
        app.setPalette(QPalette(_SYSTEM_PALETTE))
    else:
        app.setPalette(app.style().standardPalette())
    app.setStyleSheet(_stylesheet("system", app.palette()))
    return "system"


__all__ = ["THEMES", "apply_theme"]
