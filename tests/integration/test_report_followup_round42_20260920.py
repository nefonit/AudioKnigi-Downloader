from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_settings_no_longer_duplicate_ui_mode_selector() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    settings = src("audioknigi/qt/mixins/settings.py")
    sync = src("audioknigi/qt/settings_sync.py")
    assert "self.ui_mode_combo = QComboBox()" not in pages
    assert 'ui.addRow(self._l("Режим:"), self.ui_mode_combo)' not in pages
    assert '"ui_mode": self.current_ui_mode()' in settings
    assert 'hasattr(self, "ui_mode_combo")' not in sync


def test_event_and_windows_system_sound_preview_are_distinct() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    settings = src("audioknigi/qt/mixins/settings.py")
    events = src("audioknigi/qt/event_sounds.py")
    assert 'QPushButton(self._l("Проверить звук события"))' in pages
    assert 'QPushButton(self._l("Проверить системный звук"))' in pages
    assert "self.preview_voice_button.clicked.connect(self.preview_event_sound)" in pages
    assert "self.preview_system_button.clicked.connect(self.preview_system_sound)" in pages
    assert 'self.event_sound_manager.play_media_only("search_complete", force=True)' in settings
    assert 'self.event_sound_manager.play_system("app_ready")' in settings
    assert "def play_media_only(self, event: str, *, force=False) -> bool:" in events
    assert "allow_system_fallback=False" in events
    assert "return self.play_system(event) if allow_system_fallback else False" in events
    assert "if media_status == QMediaPlayer.MediaStatus.InvalidMedia:" in events
    assert '"search_complete": "search_complete.mp3"' in events
    assert (ROOT / "assets/sounds/search_complete.mp3").is_file()


def test_keyboard_focus_uses_external_qfocusframe() -> None:
    accessibility = src("audioknigi/qt/accessibility.py")
    theme = src("audioknigi/qt/theme.py")
    window = src("audioknigi/qt/main_window.py")
    assert "class KeyboardFocusFrameManager(QObject)" in accessibility
    assert "QFocusFrame(window)" in accessibility
    assert 'setObjectName("keyboardFocusFrame")' in accessibility
    assert "self._frame.setWidget(target)" in accessibility
    assert "def _discard_frame(self) -> None:" in accessibility
    assert "self._frame = None" in accessibility
    assert "Never touch the stale wrapper a second time" in accessibility
    assert "QFocusFrame#keyboardFocusFrame" in theme
    assert "QPushButton:focus" not in theme
    assert "QLineEdit:focus" not in theme
    assert "install_keyboard_focus_frame(app, self)" in window


def test_system_theme_uses_qt_color_scheme_and_stable_tokens() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert "app.styleHints().colorScheme()" in theme
    assert "scheme == Qt.ColorScheme.Dark" in theme
    assert "scheme == Qt.ColorScheme.Light" in theme
    assert "colorSchemeChanged.connect" in theme
    assert "native_palette = app.style().standardPalette()" in theme
    assert "app.setPalette(_dark_palette() if system_dark else _light_palette())" in theme
    assert "system_palette.color(QPalette.ColorRole.Window).lightness() < 128" in theme
    assert 'if system_dark:' in theme
    assert 'window = "#171a1f"' in theme
    assert 'surface = "#22262d"' in theme
    assert 'window = "#f3f5f8"' in theme
    assert 'surface = "#ffffff"' in theme
    system_block = theme.split("    else:\n        system_palette = palette or QPalette()", 1)[1].split("\n    return f", 1)[0]
    assert 'surface = "palette(base)"' not in system_block
    assert 'border = "palette(mid)"' not in system_block


def test_system_theme_never_mixes_native_palette_with_custom_dark_or_light_qss() -> None:
    theme = src("audioknigi/qt/theme.py")
    refresh = theme.split("def _refresh_system_theme", 1)[1].split("def _ensure_system_scheme_listener", 1)[0]
    apply_block = theme.split("def apply_theme", 1)[1]
    assert "app.setPalette(_dark_palette() if system_dark else _light_palette())" in refresh
    assert "app.setPalette(_dark_palette() if system_dark else _light_palette())" in apply_block
    assert "app.setPalette(app.style().standardPalette())" not in refresh
    assert "System theme" in theme or "System mode" in theme


def test_settings_card_expands_instead_of_becoming_one_third_width() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    assert "settings_card.setMinimumWidth(820)" in pages
    assert "settings_card.setMaximumWidth(1180)" in pages
    assert "settings_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)" in pages
    assert "center.addWidget(settings_card, 4)" in pages
    assert "center.addWidget(settings_card, 1)" not in pages


def test_preview_buttons_report_success_or_failure_to_status_bar() -> None:
    settings = src("audioknigi/qt/mixins/settings.py")
    assert "def preview_event_sound(self):" in settings
    assert "def preview_system_sound(self):" in settings
    assert "Не удалось воспроизвести встроенный звук события." in settings
    assert "Системный звук Windows недоступен." in settings

def test_accessibility_audit_tracks_segmented_mode_buttons_not_removed_combo() -> None:
    audit = src("audioknigi/qt/accessibility_audit.py")
    assert '"ui_mode_easy"' in audit
    assert '"ui_mode_advanced"' in audit
    assert '"ui_mode_stack"' in audit
    assert '    "ui_mode",' not in audit



def test_light_theme_uses_accessible_blue_focus_stronger_cards_and_soft_table_hover() -> None:
    theme = src("audioknigi/qt/theme.py")
    assert 'focus = "#0066cc"' in theme
    assert 'card_border = "#d1d9e2"' in theme
    assert 'table_selection = "#0d74de"' in theme
    assert 'table_hover = "#edf4fc"' in theme
    assert "border: 1px solid {card_border};" in theme
    assert "selection-background-color: {table_selection};" in theme
    assert "QTableView::item:hover, QTableWidget::item:hover" in theme
    # Dark/system-dark keep the established amber ring instead of becoming blue.
    assert 'focus = "#e5a93c"' in theme
