from __future__ import annotations

from pathlib import Path

from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.services import search_service

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_system_theme_keeps_onboarding_subtitle_readable():
    onboarding = text("audioknigi/qt/onboarding.py")
    theme = text("audioknigi/qt/theme.py")
    assert 'self.subtitle_label.setObjectName("onboardingSubtitle")' in onboarding
    assert 'onboarding_muted = "#aab2bf"' in theme
    assert 'QLabel#onboardingSubtitle {{ color: {onboarding_muted}; }}' in theme


def test_volume_controls_show_numeric_percent_and_drag_tooltip():
    main = text("audioknigi/qt/main_window.py")
    player = text("audioknigi/qt/player_mixin.py")
    pages = text("audioknigi/qt/main_window_pages.py")
    combined = main + "\n" + pages + "\n" + player
    for ident in ("player_volume_value", "event_sound_volume_value"):
        assert f'identifier="{ident}"' in combined
    assert 'QToolTip.showText(QCursor.pos(), text, slider)' in main
    assert 'self.player_volume_value_label.setText(f"{percent}%")' in player
    assert 'self.event_sound_volume_value_label.setText(f"{percent}%")' in main
    for language in ("uk", "de", "en"):
        assert ui_text(language, "Текущая громкость: {value}%", value=66) != "Текущая громкость: 66%"


def test_search_service_reports_monotonic_provider_stage_percentages(monkeypatch):
    monkeypatch.setattr(search_service, "search_audioknigi", lambda query, cancel_event=None: [])
    monkeypatch.setattr(search_service, "search_knigavuhe", lambda query, cancel_event=None: [])
    monkeypatch.setattr(search_service, "enrich_knigavuhe_search_variants", lambda values, cancel_event=None: values)
    monkeypatch.setattr(search_service, "search_poleknig", lambda query, cancel_event=None: [])

    events: list[tuple[int, str]] = []
    outcome = search_service.search_all_sources("тест", progress=lambda percent, message: events.append((percent, message)))

    assert outcome.errors == []
    percents = [percent for percent, _message in events]
    assert percents[0] == 5
    assert percents[-1] == 100
    assert percents == sorted(percents)
    assert any("audioknigi.com.ua" in message for _percent, message in events)
    assert any("knigavuhe.org" in message for _percent, message in events)
    assert any("poleknig.com" in message for _percent, message in events)


def test_qt_search_ui_has_circular_progress_in_both_modes_and_localized_status():
    main = text("audioknigi/qt/main_window.py")
    progress = text("audioknigi/qt/search_progress.py")
    audit = text("audioknigi/qt/accessibility_audit.py")
    assert "class CircularSearchProgress(QWidget):" in progress
    assert 'identifier="search_progress"' in main
    assert 'identifier="easy_search_progress"' in main
    assert 'worker.progress.connect(self._search_progress_changed)' in main
    assert 'self._set_search_progress(5, "Поиск запущен", visible=True)' in main
    assert 'QTimer.singleShot(650, self._hide_search_progress_if_idle)' in main
    assert '"search_progress"' in audit and '"easy_search_progress"' in audit
    for language in ("uk", "de", "en"):
        assert localize_runtime_text(language, "Поиск запущен") != "Поиск запущен"
        assert localize_runtime_text(language, "Ищу на poleknig.com") != "Ищу на poleknig.com"
