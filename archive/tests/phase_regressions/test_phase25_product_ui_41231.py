from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "\n".join((ROOT / "audioknigi" / "qt" / name).read_text(encoding="utf-8") for name in ("main_window.py", "main_window_pages.py"))
PLAYER = (ROOT / "audioknigi" / "qt" / "player_mixin.py").read_text(encoding="utf-8")
THEME = (ROOT / "audioknigi" / "qt" / "theme.py").read_text(encoding="utf-8")
SPEED = (ROOT / "audioknigi" / "qt" / "speed_graph.py").read_text(encoding="utf-8")


def test_developer_phase_labels_are_not_user_facing():
    for marker in ("Phase 19", "Qt full parity phase 13", "Qt-only runtime", "61/61"):
        assert marker not in MAIN


def test_easy_mode_is_centered_card_with_primary_download_and_cover():
    assert 'card.setObjectName("easyCard")' in MAIN
    assert 'card.setMaximumWidth(900)' in MAIN
    assert 'self.easy_download_button.setProperty("role", "primary")' in MAIN
    assert 'self.easy_cover_label = QLabel(self._l("Нет обложки"))' in MAIN
    assert 'self.easy_book_card.setVisible(False)' in MAIN


def test_book_tab_uses_dynamic_analysis_download_menu_and_collapsed_log():
    assert 'self.analyze_button.clicked.connect(self._analysis_primary_action)' in MAIN
    assert 'self.analyze_button.setText(self._l("Отмена…") if cancelling else self._l("Отмена"))' in MAIN
    assert 'self.download_menu_button.setMenu(download_menu)' in MAIN
    assert 'self.download_full_mp3_action = download_menu.addAction(self._l("Скачать одним MP3"))' in MAIN
    assert 'self.session_log_group.setVisible(False)' in MAIN
    assert 'self.recovery_panel.setVisible(count > 0)' in MAIN


def test_queue_toolbar_is_compact_and_has_group_actions_context_menu():
    assert 'self.queue_actions_button = QPushButton(self._l("Действия ▾"))' in MAIN
    assert 'self.queue_clear_completed_action = actions_menu.addAction(self._l("Очистить завершённые"))' in MAIN
    assert 'self.queue_table.customContextMenuRequested.connect(self._show_queue_context_menu)' in MAIN
    assert 'self.queue_start_button.setText(self._l("Пауза") if active_queue_download else self._l("Запустить очередь"))' in MAIN


def test_history_export_is_dropdown_and_has_context_menu():
    assert 'self.history_export_button = QPushButton(self._l("Экспорт библиотеки ▾"))' in MAIN
    assert 'self.history_table.customContextMenuRequested.connect(self._show_history_context_menu)' in MAIN


def test_settings_are_split_into_four_sections():
    assert 'self.settings_nav = QListWidget(page)' in MAIN
    assert '("Основные", "Загрузка и сеть", "Внешний вид и звук", "Интеграции и резервная копия")' in MAIN
    assert 'self.settings_stack = QStackedWidget(page)' in MAIN


def test_player_has_cover_compact_transport_and_chapter_list():
    assert 'self.player_cover_label.setFixedSize(260, 260)' in PLAYER
    assert 'self.player_chapter_list = QListWidget()' in PLAYER
    assert 'self.player_back_button = QPushButton(self._l("−30 с"))' in PLAYER
    assert 'self.player_forward_button = QPushButton(self._l("+30 с"))' in PLAYER
    assert 'card.setMaximumWidth(980)' in PLAYER


def test_modern_qss_has_accent_rounding_and_segmented_mode():
    assert 'QPushButton[role="primary"]' in THEME
    assert 'background: #0066cc' in THEME
    assert 'border-radius: 6px' in THEME
    assert 'QPushButton[role="segment"]:checked' in THEME
    assert 'QListWidget#settingsNav::item:selected' in THEME


def test_speed_graph_does_not_duplicate_current_speed_placeholder():
    paint = SPEED[SPEED.index("    def paintEvent"):]
    assert 'drawText(self.rect().adjusted' not in paint
