from __future__ import annotations

import ast
import threading
import time
from pathlib import Path

from audioknigi.models import SearchResult
from audioknigi.services import search_service
from audioknigi.services.source_health_service import SourceHealthItem, SourceHealthOutcome


ROOT = Path(__file__).resolve().parents[2]


class _FakeProvider:
    def __init__(self, key: str, display_name: str, barrier: threading.Barrier, delay: float = 0.0):
        self.key = key
        self.display_name = display_name
        self._barrier = barrier
        self._delay = delay

    def search(self, query: str, *, cancel_event=None):
        self._barrier.wait(timeout=1.5)
        if self._delay:
            time.sleep(self._delay)
        return [
            SearchResult(
                title=f"{self.display_name} {query}",
                url=f"https://example.invalid/{self.key}",
                source=self.display_name,
            )
        ]

    def enrich_search_results(self, results, *, cancel_event=None):
        return list(results)


def test_search_sources_run_concurrently_and_keep_registry_order(monkeypatch):
    barrier = threading.Barrier(3)
    providers = (
        _FakeProvider("first", "First", barrier, 0.12),
        _FakeProvider("second", "Second", barrier, 0.01),
        _FakeProvider("third", "Third", barrier, 0.05),
    )
    monkeypatch.setattr(search_service, "registered_providers", lambda: providers)

    outcome = search_service.search_all_sources("book")

    assert [item.source for item in outcome.results] == ["First", "Second", "Third"]
    assert outcome.errors == []


def test_source_health_outcome_reports_blocked_and_unavailable_counts():
    outcome = SourceHealthOutcome([
        SourceHealthItem("one", "https://one/", True, status_code=200),
        SourceHealthItem("two", "https://two/", False, blocked=True, status_code=451),
        SourceHealthItem("three", "https://three/", False, error="timeout"),
    ])
    assert outcome.reachable_count == 1
    assert outcome.unavailable_count == 2
    assert outcome.blocked_count == 1
    assert outcome.all_unavailable is False


def test_hidden_window_skips_startup_source_health_check():
    source = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert "if not self.isVisible()" in source
    assert "threading.Thread(" in source
    assert "daemon=True" in source
    assert "relay.source_health_result.emit(outcome)" in source


def test_all_sources_unavailable_message_includes_vpn_and_warp_guidance():
    source = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert "Proton VPN" in source
    assert "Mullvad VPN" in source
    assert "Cloudflare WARP" in source
    assert "не позволяет выбрать другую страну" in source
    assert "self._show_message(QMessageBox.Icon.Warning" in source
    assert "announce_now=True" in source


def test_player_controls_have_explicit_screenreader_instructions_and_enter_shortcuts():
    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    access = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert "Enter или пробел" in player
    assert 'for sequence in ("Return", "Enter")' in access
    assert "Qt.ShortcutContext.WidgetShortcut" in access
    assert "Space remains the native QPushButton action" in access


def test_global_hotkeys_use_window_context_and_cover_all_six_tabs():
    source = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert "Qt.ShortcutContext.WindowShortcut" in source
    for sequence in ("Ctrl+L", "Ctrl+F", "Ctrl+D", "Ctrl+Q", "Ctrl+H", "Escape"):
        assert f'_add_window_shortcut("{sequence}"' in source
    assert 'f"Alt+{number}"' in source
    assert 'f"Ctrl+{number}"' in source
    assert "self.TAB_PLAYER" in source


def test_accessibility_audit_checks_every_visible_focusable_button():
    source = (ROOT / "audioknigi/qt/accessibility_audit.py").read_text(encoding="utf-8")
    assert "window.findChildren(QAbstractButton)" in source
    assert "empty accessible button name" in source
    assert "empty accessible button description" in source
    assert '"player_back_30"' in source
    assert '"player_forward_30"' in source


def test_narration_selection_auto_analyzes_and_focuses_download_after_analysis():
    search = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert "def _easy_narration_selected" in search
    assert "QTimer.singleShot(0, self.use_selected_result)" in search
    assert "self._focus_download_after_analysis = True" in search
    assert "self._focus_download_after_analysis = True" in analysis
    assert 'target = self.easy_download_button if self.current_ui_mode() == "easy" else self.download_all_button' in analysis
    assert "Нажмите Enter или пробел, чтобы начать скачивание" in analysis


def test_help_center_uses_splitter_and_non_overlapping_topic_rows():
    source = (ROOT / "audioknigi/qt/help_center.py").read_text(encoding="utf-8")
    assert "QSplitter" in source
    assert "self.topics.setWordWrap(True)" in source
    assert "self.topics.setSpacing(4)" in source
    assert "item.setSizeHint(QSize(0, 42))" in source
    assert "splitter.setChildrenCollapsible(False)" in source
    tree = ast.parse(source)
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"TOPICS", "ROUND55_TOPIC_DETAILS_RU"}:
                    values[target.id] = ast.literal_eval(node.value)
    expected = {key for key, _title, _body in values["TOPICS"]["ru"]}
    details = values["ROUND55_TOPIC_DETAILS_RU"]
    assert set(details) == expected
    assert all(len(text) >= 120 for text in details.values())


def test_current_step_guidance_is_visible_and_accessible():
    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    access = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert 'identifier="current_guidance"' in main
    assert "def _guidance_for_tab" in access
    for label in ("Книга:", "Поиск:", "Очередь:", "История:", "Настройки:", "Плеер:"):
        assert label in access
