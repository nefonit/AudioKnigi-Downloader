from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "\n".join((ROOT / "audioknigi" / "qt" / name).read_text(encoding="utf-8") for name in ("main_window.py", "main_window_pages.py"))
PLAYER = (ROOT / "audioknigi" / "qt" / "player_mixin.py").read_text(encoding="utf-8")
AUDIT = (ROOT / "audioknigi" / "qt" / "accessibility_audit.py").read_text(encoding="utf-8")
THEME = (ROOT / "audioknigi" / "qt" / "theme.py").read_text(encoding="utf-8")


def test_accessibility_contract_matches_phase25_widgets():
    for old_id in ("history_export_json", "history_export_csv", "history_clear", "settings_scroll"):
        required = AUDIT[AUDIT.index("REQUIRED_ACCESSIBLE_IDS"):AUDIT.index("DYNAMIC_ACCESSIBLE_IDS")]
        assert f'"{old_id}"' not in required
    for new_id in ("history_export", "settings_sections", "settings_stack"):
        assert f'"{new_id}"' in required
    assert 'identifier="settings_stack"' in MAIN


def test_history_menu_actions_keep_stable_diagnostic_ids():
    assert 'setObjectName("history_export_json")' in MAIN
    assert 'setObjectName("history_export_csv")' in MAIN
    assert 'setObjectName("history_clear")' in MAIN


def test_disabled_primary_cta_has_explicit_muted_qss_override():
    assert 'QPushButton[role="primary"]:disabled' in THEME
    disabled_rule = THEME.split('QPushButton[role="primary"]:disabled', 1)[1].split('}}', 1)[0]
    assert 'background: {disabled_bg}' in disabled_rule
    assert 'color: {disabled_text}' in disabled_rule


def test_player_has_cover_and_chapter_empty_states():
    assert 'QLabel("♫\\n" + self._l("Нет обложки"))' in PLAYER
    assert 'self.player_cover_label.setObjectName("coverPlaceholder")' in PLAYER
    assert 'Список глав появится\\nпосле открытия книги' in PLAYER
    assert 'self._set_player_chapter_placeholder()' in PLAYER


def test_view_menu_uses_exclusive_radio_actions_and_tracks_mode():
    assert 'self.view_mode_group = QActionGroup(self)' in MAIN
    assert 'self.view_mode_group.setExclusive(True)' in MAIN
    assert 'action.setCheckable(True)' in MAIN
    assert 'self.view_easy_action.setChecked(mode == "easy")' in MAIN
    assert 'self.view_advanced_action.setChecked(mode == "advanced")' in MAIN


def test_search_actions_are_disabled_until_a_result_is_selected():
    assert 'self.use_result_button.setEnabled(False)' in MAIN
    assert 'self.copy_result_button.setEnabled(False)' in MAIN
    assert 'self.easy_use_result_button.setEnabled(False)' in MAIN
    assert 'self.easy_copy_url_button.setEnabled(False)' in MAIN
    assert 'selectionChanged.connect(lambda _selected, _deselected: self._update_search_action_states())' in MAIN
    assert 'def _update_search_action_states(self) -> None:' in MAIN
