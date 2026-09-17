from __future__ import annotations

import ast
from pathlib import Path

from audioknigi.models import Book, Track, cover_cache_bytes, normalize_cover_cache
from audioknigi.services.queue_service import _book_from_dict, _book_to_dict

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_cover_cache_normalizes_network_tuple_and_legacy_bytes():
    payload = b"\xff\xd8cover-bytes"
    assert normalize_cover_cache((payload, "image/webp; charset=binary")) == (payload, "image/webp")
    assert normalize_cover_cache(payload) == (payload, "image/jpeg")
    assert cover_cache_bytes((payload, "image/png")) == payload
    assert normalize_cover_cache((b"", "image/png")) is None


def test_queue_cover_roundtrip_preserves_bytes_and_mime():
    payload = b"queue-cover"
    book = Book(url="https://example.test/book", title="Book", tracks=[Track(index=1, title="1", file="x")])
    book.cover_cache = (payload, "image/png")
    data = _book_to_dict(book)
    assert data["cover_cache_b64"]
    assert data["cover_cache_mime"] == "image/png"
    restored = _book_from_dict(data)
    assert restored.cover_cache == (payload, "image/png")


def test_queue_old_b64_snapshot_is_backward_compatible():
    payload = b"old-cover"
    book = Book(url="https://example.test/book", title="Book", tracks=[Track(index=1, title="1", file="x")])
    data = _book_to_dict(book)
    import base64
    data["cover_cache_b64"] = base64.b64encode(payload).decode("ascii")
    data.pop("cover_cache_mime", None)
    restored = _book_from_dict(data)
    assert restored.cover_cache == (payload, "image/jpeg")


def test_package_api_has_no_retired_audioknigi_app_import():
    init = text("audioknigi/__init__.py")
    assert "AudioKnigiApp" not in init
    assert "from .app" not in init
    assert not (ROOT / "audioknigi/app.py").exists()


def test_main_window_has_one_output_dir_chooser_and_no_fake_mime_object():
    main = text("audioknigi/qt/main_window.py")
    assert main.count("def _choose_output_dir(") == 1
    assert 'type("_M"' not in main
    assert "def _normalize_drop_values(" in main
    assert "cover_cache_bytes(" in main


def test_core_has_no_retired_tk_geometry_api():
    core = text("audioknigi/core.py")
    for name in ("maximize_window_for_display", "adaptive_window_min_size", "safe_window_geometry", "winfo_"):
        assert name not in core


def test_accessibility_contract_includes_all_phase13_15_controls():
    audit = text("audioknigi/qt/accessibility_audit.py")
    required = {
        "download_all", "clear_book_input", "queue_item_pause", "queue_retry_all",
        "large_mode", "hide_source", "event_sounds_enabled", "event_sound_volume",
        "preview_event_sound", "preview_system_sound", "language", "ui_mode",
        "ui_mode_easy", "ui_mode_advanced", "ui_mode_stack", "easy_universal_input",
        "easy_paste", "easy_action", "easy_quality", "easy_output_dir", "easy_choose_folder",
        "easy_search_results", "easy_use_result", "easy_copy_url", "easy_book_summary",
        "easy_download", "easy_open_listen", "easy_another_book",
        "book_output_dir", "book_choose_output", "book_open_output", "book_cover",
        "book_description", "session_log",
    }
    for identifier in required:
        assert f'"{identifier}"' in audit
    for identifier in ("modal_message", "modal_ok", "modal_question", "modal_yes", "modal_no"):
        assert f'"{identifier}"' in audit


def test_accessibility_required_contract_has_no_duplicate_ids():
    module = ast.parse(text("audioknigi/qt/accessibility_audit.py"))
    required = None
    for node in module.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "REQUIRED_ACCESSIBLE_IDS" for t in node.targets):
            required = ast.literal_eval(node.value)
            break
    assert required is not None
    assert len(required) == len(set(required))
    assert len(required) >= 120


def test_phase15_or_later_stage_is_advertised_by_qt_entry_contract():
    stage_source = text("audioknigi/qt/__init__.py")
    assert 'QT_MIGRATION_STAGE = "phase-' in stage_source
    assert any(f'QT_MIGRATION_STAGE = "phase-{n}"' in stage_source for n in range(15, 100))
