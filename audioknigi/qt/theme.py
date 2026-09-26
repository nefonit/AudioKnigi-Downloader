from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


THEMES = ("system", "light", "dark")
_SYSTEM_STYLE_NAME: str | None = None
_SYSTEM_PALETTE: QPalette | None = None
_APPLIED_STYLE_KEY: str | None = None
_CURRENT_THEME = "system"
_SYSTEM_SCHEME_SIGNAL_CONNECTED = False


def _capture_system_appearance(app: QApplication) -> None:
    global _SYSTEM_STYLE_NAME, _SYSTEM_PALETTE
    if _SYSTEM_STYLE_NAME is None:
        try:
            _SYSTEM_STYLE_NAME = str(app.style().objectName() or "")
        except Exception:
            _SYSTEM_STYLE_NAME = ""
    if _SYSTEM_PALETTE is None:
        _SYSTEM_PALETTE = QPalette(app.palette())



def _system_is_dark(app: QApplication, palette: QPalette | None = None) -> bool:
    """Prefer Qt's platform color-scheme signal; fall back to palette luminance."""
    try:
        scheme = app.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return True
        if scheme == Qt.ColorScheme.Light:
            return False
    except (AttributeError, RuntimeError):
        pass
    system_palette = palette or app.palette()
    try:
        return system_palette.color(QPalette.ColorRole.Window).lightness() < 128
    except Exception:
        return False


def _refresh_system_theme(app: QApplication, scheme=None) -> None:
    if _CURRENT_THEME != "system":
        return
    try:
        if scheme == Qt.ColorScheme.Dark:
            system_dark = True
        elif scheme == Qt.ColorScheme.Light:
            system_dark = False
        else:
            system_dark = _system_is_dark(app, app.palette())
        # Do not combine a dark/light QSS with the native style's opposite
        # palette.  On Windows this produced light QScrollArea viewports inside
        # an otherwise dark System theme.  System mode follows the OS scheme,
        # then applies one coherent palette for every styled and unstyled widget.
        app.setPalette(_dark_palette() if system_dark else _light_palette())
        app.setStyleSheet(_stylesheet("system", app.palette(), system_dark=system_dark))
    except RuntimeError:
        pass


def _ensure_system_scheme_listener(app: QApplication) -> None:
    global _SYSTEM_SCHEME_SIGNAL_CONNECTED
    if _SYSTEM_SCHEME_SIGNAL_CONNECTED:
        return
    try:
        app.styleHints().colorSchemeChanged.connect(lambda scheme: _refresh_system_theme(app, scheme))
        _SYSTEM_SCHEME_SIGNAL_CONNECTED = True
    except (AttributeError, RuntimeError, TypeError):
        pass

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


def _stylesheet(mode: str, palette: QPalette | None = None, *, system_dark: bool | None = None) -> str:
    """Return one restrained production stylesheet for all supported themes.

    The stylesheet deliberately keeps focus treatment stronger than decorative
    borders so keyboard users never lose the active control while the rest of
    the interface gains a consistent production visual hierarchy.
    """
    accent = "#0a6ed1"
    accent_hover = "#117ee8"
    accent_pressed = "#075aa9"
    focus = "#e5a93c"
    danger = "#c43d38"
    card_border = None
    table_selection = accent
    table_hover = None

    if mode == "dark":
        window = "#171a1f"
        surface = "#22262d"
        surface2 = "#292e36"
        surface3 = "#303640"
        border = "#3b424d"
        text = "#f3f6fa"
        muted = "#a8b1bd"
        secondary = "#9ba3af"
        onboarding_muted = "#aeb6c2"
        input_bg = "#191d23"
        disabled_bg = "#242931"
        disabled_text = "#737d8a"
        hover = "#303741"
        table_bg = "#181a1f"
        table_alt = "#20242c"
        table_grid = "#2d333f"
        selection_text = "#ffffff"
        card_border = border
        table_selection = accent
        table_hover = "#252b34"
    elif mode == "light":
        window = "#f3f5f8"
        surface = "#ffffff"
        surface2 = "#f7f9fc"
        surface3 = "#eef2f7"
        border = "#d7dde7"
        text = "#17202a"
        muted = "#667085"
        secondary = "#596579"
        onboarding_muted = "#596579"
        input_bg = "#ffffff"
        disabled_bg = "#edf1f5"
        disabled_text = "#98a1ae"
        hover = "#edf4fb"
        table_bg = "#ffffff"
        table_alt = "#f3f6fa"
        table_grid = "#e2e7ef"
        selection_text = "#ffffff"
        focus = "#0066cc"
        card_border = "#d1d9e2"
        table_selection = "#0d74de"
        table_hover = "#edf4fc"
    else:
        system_palette = palette or QPalette()
        if system_dark is None:
            try:
                system_dark = system_palette.color(QPalette.ColorRole.Window).lightness() < 128
            except Exception:
                system_dark = False
        # Follow Windows light/dark automatically, but use stable application
        # tokens instead of mixing custom QSS with unpredictable native
        # Base/Mid/Button roles (notably inconsistent on Windows 10).
        if system_dark:
            window = "#171a1f"
            surface = "#22262d"
            surface2 = "#292e36"
            surface3 = "#303640"
            border = "#3b424d"
            text = "#f3f6fa"
            muted = "#a8b1bd"
            secondary = "#9ba3af"
            onboarding_muted = "#aeb6c2"
            input_bg = "#191d23"
            disabled_bg = "#242931"
            disabled_text = "#737d8a"
            hover = "#303741"
            table_bg = "#181a1f"
            table_alt = "#20242c"
            table_grid = "#2d333f"
            selection_text = "#ffffff"
            card_border = border
            table_selection = accent
            table_hover = "#252b34"
        else:
            window = "#f3f5f8"
            surface = "#ffffff"
            surface2 = "#f7f9fc"
            surface3 = "#eef2f7"
            border = "#d7dde7"
            text = "#17202a"
            muted = "#667085"
            secondary = "#596579"
            onboarding_muted = "#596579"
            input_bg = "#ffffff"
            disabled_bg = "#edf1f5"
            disabled_text = "#98a1ae"
            hover = "#edf4fb"
            table_bg = "#ffffff"
            table_alt = "#f3f6fa"
            table_grid = "#e2e7ef"
            selection_text = "#ffffff"
            focus = "#0066cc"
            card_border = "#d1d9e2"
            table_selection = "#0d74de"
            table_hover = "#edf4fc"

    card_border = card_border or border
    table_hover = table_hover or hover

    return f"""
QMainWindow {{
    background: {window};
}}
QWidget#appHeader {{
    background: transparent;
    border-bottom: 1px solid {border};
}}
QLabel#appBrand {{
    color: {text};
    font-size: 22px;
    font-weight: 700;
}}
QLabel#appSubtitle {{
    color: {muted};
    font-size: 13px;
}}
QMenuBar {{
    background: transparent;
    color: {text};
    spacing: 6px;
    padding: 3px 6px 3px 10px;
}}
QMenuBar::item {{
    padding: 6px 10px;
    border-radius: 6px;
}}
QMenuBar::item:selected {{ background: {hover}; }}
QMenu {{
    background: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 28px 7px 10px;
    border-radius: 5px;
}}
QMenu::item:selected {{ background: {accent}; color: white; }}
QMenu::separator {{
    height: 1px;
    background: {border};
    margin: 5px 8px;
}}
QPushButton {{
    min-height: 30px;
    padding: 7px 14px;
    border-radius: 8px;
    border: 1px solid {border};
    background: {surface2};
    color: {text};
}}
QPushButton:hover {{ background: {hover}; border-color: {accent}; }}
QPushButton:pressed {{ background: {surface3}; }}
/* Keyboard focus is painted externally by QFocusFrame. */
QFocusFrame#keyboardFocusFrame {{
    background: transparent;
    border: 2px solid {focus};
    border-radius: 9px;
}}
QPushButton:disabled {{ background: {disabled_bg}; color: {disabled_text}; border-color: {border}; }}
QPushButton[role="primary"] {{
    background: {accent};
    color: white;
    border: 1px solid {accent};
    font-weight: 600;
}}
QPushButton[role="primary"]:hover {{ background: {accent_hover}; border-color: {accent_hover}; }}
QPushButton[role="primary"]:pressed {{ background: {accent_pressed}; border-color: {accent_pressed}; }}
QPushButton[role="primary"]:disabled {{
    background: {disabled_bg};
    color: {disabled_text};
    border-color: {border};
    font-weight: 600;
}}
QPushButton[role="danger"] {{ background: {danger}; color: white; border-color: {danger}; font-weight: 600; }}
QPushButton[role="dangerGhost"] {{ color: {danger}; background: transparent; }}
QPushButton[role="flat"] {{ background: transparent; border: none; text-align: left; padding-left: 4px; }}
QWidget#modeSegmentHolder {{
    background: {surface2};
    border: 1px solid {border};
    border-radius: 10px;
}}
QPushButton[role="segment"] {{
    min-height: 28px;
    border: none;
    border-radius: 8px;
    padding: 6px 16px;
    background: transparent;
    color: {muted};
    font-weight: 500;
}}
QPushButton[role="segment"]:hover {{ background: {hover}; color: {text}; border: none; }}
QPushButton[role="segment"]:checked {{ background: {accent}; color: white; border: none; font-weight: 600; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    min-height: 32px;
    padding: 5px 9px;
    border-radius: 8px;
    border: 1px solid {border};
    background: {input_bg};
    color: {text};
    selection-background-color: {accent};
    selection-color: white;
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {accent}; }}
QLineEdit:read-only {{ background: {surface2}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QPlainTextEdit, QTextEdit {{
    background: {input_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px;
    selection-background-color: {accent};
    selection-color: white;
}}
QCheckBox {{ spacing: 7px; color: {text}; }}
QProgressBar {{
    border: 1px solid {border};
    border-radius: 6px;
    min-height: 11px;
    max-height: 16px;
    text-align: center;
    background: {surface2};
    color: {text};
}}
QProgressBar::chunk {{ background: {accent}; border-radius: 5px; }}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 10px;
    margin-top: 14px;
    padding: 15px 12px 12px 12px;
    font-weight: 600;
    background: {surface};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
QWidget#easyCard, QWidget#playerCard, QWidget#settingsCard {{
    background: {surface};
    border: 1px solid {card_border};
    border-radius: 16px;
}}
QWidget#bookCard, QWidget#noticeCard {{
    background: {surface2};
    border: 1px solid {card_border};
    border-radius: 12px;
}}
QWidget#settingsFooter {{
    background: {surface};
    border-top: 1px solid {border};
}}
QLabel#pageTitle {{ color: {text}; font-size: 22px; font-weight: 700; }}
QLabel#playerTitle {{ color: {text}; font-size: 24px; font-weight: 700; }}
QLabel#sectionTitle {{ color: {text}; font-size: 14px; font-weight: 700; margin-top: 7px; }}
QLabel#secondaryText {{ color: {secondary}; }}
QLabel#onboardingSubtitle {{ color: {onboarding_muted}; }}
QLabel#emptyState {{
    color: {secondary};
    padding: 20px;
    background: {surface2};
    border: 1px dashed {border};
    border-radius: 10px;
}}
QLabel#coverPlaceholder {{
    color: {muted};
    background: {surface2};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 8px;
}}
QLabel#bookMetadata {{ color: {text}; font-size: 14px; line-height: 1.35; }}
QListWidget#settingsNav {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 6px;
}}
QListWidget#settingsNav::item {{ padding: 10px 12px; margin: 2px; border-radius: 7px; }}
QListWidget#settingsNav::item:hover {{ background: {hover}; }}
QListWidget#settingsNav::item:selected {{ background: {accent}; color: white; }}
QTableView, QTableWidget {{
    background: {table_bg};
    alternate-background-color: {table_alt};
    color: {text};
    border: 1px solid {border};
    border-radius: 10px;
    gridline-color: {table_grid};
    selection-background-color: {table_selection};
    selection-color: {selection_text};
}}
QTableView::item:hover, QTableWidget::item:hover {{
    background: {table_hover};
}}
QListWidget, QTreeView {{
    background: {surface};
    alternate-background-color: {surface2};
    color: {text};
    border: 1px solid {border};
    border-radius: 10px;
    selection-background-color: {accent};
    selection-color: {selection_text};
}}
QTableView::item, QTableWidget::item {{ padding: 6px 10px; border: none; }}
QListWidget::item {{ padding: 7px 9px; border-radius: 6px; }}
QListWidget::item:hover {{ background: {hover}; }}
QListWidget::item:selected {{ background: {accent}; color: white; }}
QHeaderView {{ background: {surface2}; }}
QHeaderView::section {{
    background: {surface2};
    color: {text};
    padding: 8px 9px;
    border: none;
    border-right: 1px solid {border};
    border-bottom: 1px solid {border};
    font-weight: 600;
}}
QHeaderView::section:last {{ border-right: none; }}
QListWidget#playerChapters {{ background: {surface2}; }}
QTabWidget::pane {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 10px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {muted};
    padding: 8px 14px;
    margin-right: 2px;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:hover {{ background: {hover}; color: {text}; border-radius: 7px; }}
QTabBar::tab:selected {{
    color: {text};
    border: 1px solid {border};
    border-bottom: 3px solid {accent};
    background: {surface};
    font-weight: 600;
}}
QStatusBar {{
    background: {surface};
    color: {muted};
    border-top: 1px solid {border};
    padding: 3px 8px;
}}
QStatusBar::item {{ border: none; }}
QScrollBar:vertical {{
    background: transparent;
    width: 14px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{ background: {border}; min-height: 28px; border-radius: 6px; }}
QScrollBar::handle:vertical:hover {{ background: {muted}; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 14px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{ background: {border}; min-width: 28px; border-radius: 6px; }}
QScrollBar::handle:horizontal:hover {{ background: {muted}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
QToolTip {{
    background: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 5px 7px;
}}
"""


def apply_theme(app: QApplication, theme: str) -> str:
    """Apply an explicit high-contrast theme or restore the native system one."""
    global _APPLIED_STYLE_KEY, _CURRENT_THEME
    _capture_system_appearance(app)
    _ensure_system_scheme_listener(app)
    mode = str(theme or "system").strip().lower()
    if mode not in THEMES:
        mode = "system"
    _CURRENT_THEME = mode

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
    try:
        native_palette = app.style().standardPalette()
    except RuntimeError:
        native_palette = QPalette(_SYSTEM_PALETTE) if _SYSTEM_PALETTE is not None else app.palette()
    system_dark = _system_is_dark(app, native_palette)
    # Keep native controls/style, but make the application palette agree with
    # the system-selected light/dark stylesheet.  This is essential for
    # QScrollArea viewports and other widgets that paint from QPalette roles.
    app.setPalette(_dark_palette() if system_dark else _light_palette())
    app.setStyleSheet(
        _stylesheet("system", app.palette(), system_dark=system_dark)
    )
    return "system"


__all__ = ["THEMES", "apply_theme"]
