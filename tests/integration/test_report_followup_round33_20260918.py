from __future__ import annotations

import json
from pathlib import Path

from audioknigi import core
from audioknigi.core import fmt_size
from audioknigi.models import Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.templates import render_text_template

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_easy_search_card_is_wider_and_long_titles_wrap() -> None:
    source = src("audioknigi/qt/main_window.py")
    assert "card.setMaximumWidth(1180)" in source
    assert "self.easy_search_table.setWordWrap(True)" in source
    assert "self.easy_search_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)" in source
    assert "self.easy_search_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)" in source


def test_knigavuhe_grouped_search_collects_all_unique_narrators() -> None:
    source = src("audioknigi/knigavuhe.py")
    block = source[source.index("# Collapse separate recording pages"):source.index("__all__", source.index("# Collapse separate recording pages"))]
    assert "narrators = []" in block
    assert "if narrator and narrator not in narrators:" in block
    assert 'narrator=", ".join(narrators)' in block


def test_zero_bytes_are_formatted_as_real_size() -> None:
    assert fmt_size(0) == "0.0 B"
    assert fmt_size(-1) == "—"


def test_template_tokens_are_case_insensitive() -> None:
    values = {"Author": "Author", "Book_Title": "Book"}
    assert render_text_template("{author} - {BOOK_TITLE}", values) == "Author - Book"


def test_download_request_track_index_already_accepts_objects_and_scalars() -> None:
    track = Track(index=7, title="x", file="u")
    assert DownloadRequest.track_index(track) == 7
    assert DownloadRequest.track_index(7) == 7
    assert DownloadRequest.track_index("7") == 7


def test_empty_playwright_cookie_list_preserves_existing_cookie_file(monkeypatch) -> None:
    writes = []
    monkeypatch.setattr(core, "_load_persisted_profile", lambda: {"headers": {}, "cookies_saved": 4})
    monkeypatch.setattr(core, "save_json", lambda path, payload: writes.append((path, payload)) or True)
    monkeypatch.setattr(core, "refresh_http_session_profile", lambda: None)
    core.persist_browser_session([], {"User-Agent": "UA"})
    assert not any(path == core.COOKIE_FILE for path, _payload in writes)
    profile = [payload for path, payload in writes if path == core.SESSION_PROFILE_FILE][-1]
    assert profile["cookies_saved"] == 4


def test_track_filename_extension_handling_is_already_space_safe() -> None:
    core_source = src("audioknigi/core.py")
    templates = src("audioknigi/templates.py")
    assert 'name = re.sub(r"\\s+", " ", name).strip(". ")' in core_source
    assert '".ogg"' in templates and '".opus"' in templates


def test_loudnorm_scan_window_is_large_enough_for_noisy_inputs() -> None:
    source = src("audioknigi/download/media.py")
    assert 'loudnorm_tail = str(stderr or "")[-524_288:]' in source


def test_fallback_log_labels_non_primary_failure_correctly() -> None:
    source = src("audioknigi/download/network.py")
    assert 'source_label = (' in source
    assert 'if pos == 1' in source
    assert 'f"Резервный источник ({source_name(url)})"' in source


def test_cover_format_switch_removes_stale_alternate_sidecars() -> None:
    source = src("audioknigi/download/media.py")
    assert 'for old_ext in (".jpg", ".jpeg", ".png", ".webp"):' in source
    assert '(folder / ("cover" + old_ext)).unlink(missing_ok=True)' in source


def test_middle_shared_track_without_end_boundary_is_diagnosed() -> None:
    source = src("audioknigi/download/media.py")
    assert "event=split_missing_middle_boundary" in source


def test_audioknigi_search_normalizes_query_and_decodes_bom() -> None:
    source = src("audioknigi/providers/audioknigi_search.py")
    block = source[source.index("def search_audioknigi"):source.index("__all__")]
    assert 'query_text = str(query or "").strip()' in block
    assert 'if not query_text:' in block
    assert 'params={"text": query_text}' in block
    assert '.decode("utf-8-sig", errors="replace")' in block


def test_book_analysis_bounds_fallback_and_always_cancels_probe_children() -> None:
    source = src("audioknigi/services/book_analysis_service.py")
    assert "for _score, candidate_url in sorted(candidates, reverse=True)[:8]:" in source
    finally_block = source[source.index("finally:", source.index("def _populate_missing_track_durations")):
                           source.index("@staticmethod", source.index("def _populate_missing_track_durations"))]
    assert "self._cancel_duration_probe_processes()" in finally_block
    assert "pool.shutdown(wait=False, cancel_futures=True)" in finally_block


def test_root_library_recovery_depth_and_queue_drop_coordinate_are_hardened() -> None:
    library = src("audioknigi/services/library_service.py")
    workers = src("audioknigi/qt/workers.py")
    assert "if depth >= 8:" in library
    assert "target_row = self.rowAt(int(event.position().y()))" in workers
    drop_block = workers[workers.index("def dropEvent"):workers.index("super().dropEvent", workers.index("def dropEvent"))]
    assert "mapFrom" not in drop_block


def test_ctrl_d_respects_selected_tracks_and_batch_errors_do_not_stack_dialogs() -> None:
    accessibility = src("audioknigi/qt/mixins/accessibility_ui.py")
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    assert 'QShortcut(QKeySequence("Ctrl+D"), self, activated=self._start_primary_download)' in accessibility
    error_block = analysis[analysis.index('if kind == "error":'):analysis.index("book = payload")]
    assert "batch_pending = bool(getattr(self, \"_pending_queue_urls\", None))" in error_block
    assert 'self._append_log("Ошибка анализа при пакетном добавлении: " + str(payload))' in error_block


def test_duplicate_open_folder_updates_book_state_and_audit_timeout_is_relaxed() -> None:
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    assert analysis.count("self.last_completed_book = self.current_book") >= 3
    audit = src("tools/historical_regression_audit.py")
    assert "timeout=240" in audit


def test_release_dates_are_finalized_to_2026_09_18() -> None:
    changelog = src("CHANGELOG.md")
    requirements = src("requirements-release.txt")
    assert "## 4.12.42 — Acceptance parser, cancellation and diagnostics hardening (2026-09-18)" in changelog
    assert "Verified published release baseline for 2026-09-18" in requirements


def test_runtime_catalog_static_literal_duplicate_is_removed_but_prefix_fallback_is_retained() -> None:
    exact = json.loads((ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8"))
    prefixes = json.loads((ROOT / "audioknigi/locales/runtime_prefixes.json").read_text(encoding="utf-8"))
    assert "ID библиотеки Audiobookshelf" not in exact
    assert "Скачивание завершено. Пропущены недоступные части: " in prefixes


def test_disk_space_proportional_recommendation_is_intentionally_not_applied_to_shared_source() -> None:
    source = src("audioknigi/services/book_analysis_service.py")
    probe = src("audioknigi/download/probe.py")
    assert "if self.options.fetch_remote_size and len(unique_files) == 1:" in source
    assert "remote_size * (missing_duration / total_duration)" not in probe[probe.index("source_remaining = 0"):probe.index("outputs = 0")]


def test_unverified_or_risky_architecture_recommendations_remain_out_of_bugfix_round() -> None:
    search = src("audioknigi/services/search_service.py")
    bootstrap = src("tools/pyinstaller_bootstrap.py")
    assert "for provider_index, provider in enumerate(providers):" in search
    assert 'hasattr(platform, "_wmi")' in bootstrap
