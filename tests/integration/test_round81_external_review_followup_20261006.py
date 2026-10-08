from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.download.common import source_target_assignments
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download.probe import ProbeMixin
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book
from audioknigi.services import source_health_service
from audioknigi.download import network as network_module
from audioknigi.download import source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin

ROOT = Path(__file__).resolve().parents[2]


def test_source_analysis_candidate_unpacking_uses_url_key(monkeypatch):
    seen = []

    result = SimpleNamespace(
        title="Demo Book",
        author="Author Name",
        narrator="Reader Name",
        url="https://knigavuhe.org/book/demo/",
        narration_variants=[],
    )
    fallback = SimpleNamespace(
        title="Demo Book",
        author="Author Name",
        narrator="Reader Name",
        url=result.url,
    )

    monkeypatch.setattr(source_analysis_module, "search_knigavuhe_books", lambda *_a, **_k: [result])

    class Provider:
        def fetch_book(self, url, cancel_event=None):
            seen.append(url)
            return fallback

    monkeypatch.setattr(source_analysis_module, "provider_for_key", lambda _key: Provider())

    class Harness(SourceAnalysisMixin):
        cancel_event = None
        def _check_cancel(self):
            pass
        @staticmethod
        def _identity_tokens(value):
            return [token for token in str(value or "").casefold().split() if token]
        @staticmethod
        def _book_identity_hints(book):
            return book.title, book.author, book.narrator

    book = SimpleNamespace(title="Demo Book", author="Author Name", narrator="Reader Name")
    assert Harness()._knigavuhe_fallback_candidate(book) is fallback
    assert seen == ["https://knigavuhe.org/book/demo/"]


def test_single_stream_does_not_promote_truncated_response(monkeypatch, tmp_path):
    class Response:
        status_code = 200
        headers = {"content-length": "10"}
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def raise_for_status(self):
            pass
        def iter_content(self, chunk_size=0):
            yield b"abc"

    class Session:
        def get(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(network_module, "get_http_session", lambda: Session())

    class Limiter:
        def consume(self, *_args, **_kwargs):
            pass

    class Harness(NetworkDownloadMixin):
        cancel_event = None
        _suppress_source_transfer_ui = True
        def _check_cancel(self):
            pass
        def _get_bandwidth_limiter(self):
            return Limiter()
        def record_transfer_metrics(self, *_args):
            pass
        def set_progress(self, *_args):
            pass
        def set_status(self, *_args):
            pass

    target = tmp_path / "source.mp3"
    with pytest.raises(RuntimeError, match="Загрузка оборвалась"):
        Harness()._download_single("https://cdn.invalid/source.mp3", target, "https://example.invalid/")
    assert not target.exists()
    assert target.with_name(target.name + ".part").read_bytes() == b"abc"


def test_probe_space_estimation_accepts_mapping_selection_and_mapping_tracks(tmp_path):
    class Harness(ProbeMixin):
        def _book_folder(self, *_args, **_kwargs):
            return tmp_path

    book = Book(url="https://example.invalid/book", title="Book", remote_size=20 * 1024 * 1024)
    book.tracks = [
        {"index": 0, "title": "Zero", "file": "https://cdn.invalid/0.mp3", "duration": 10, "local_status": "missing"},
        {"index": 1, "title": "One", "file": "https://cdn.invalid/1.mp3", "duration": 20, "local_status": "missing"},
    ]
    probe = Harness()
    one = probe._estimate_required_space(book, [{"index": 0}])
    all_space = probe._estimate_required_space(book)
    assert one > 0
    assert all_space >= one


def test_source_target_assignments_preserve_mapping_track_slots(tmp_path):
    book = SimpleNamespace(tracks=[
        {"file": "https://cdn.invalid/a.mp3"},
        {"file": "https://cdn.invalid/b.mp3"},
    ])
    rows = source_target_assignments(book, ["https://cdn.invalid/b.mp3"], tmp_path)
    assert rows[0][0] == 2
    assert rows[0][2].name == "_source_02.mp3"


def test_book_flow_only_calls_ui_when_dispatcher_is_callable():
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert source.count('callable(getattr(self, "ui", None))') >= 2
    assert 'hasattr(self, "ui") and hasattr(self, "_refresh_book_timing_ui")' not in source


def test_source_health_503_is_reachable_but_blocked(monkeypatch):
    class Response:
        status_code = 503
        def close(self):
            pass

    class Session:
        def __init__(self):
            self.headers = {}
            self.trust_env = True
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def get(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(source_health_service.requests, "Session", Session)
    item = source_health_service._probe_source("example.invalid", timeout=1.0)
    assert item.reachable is True
    assert item.blocked is True
    assert item.status_code == 503
    assert item.error == ""


def test_round81_runtime_error_localizations_are_available():
    assert localize_runtime_text("en", "После обновления плейлиста эта озвучка стала недоступна.").startswith(
        "After refreshing"
    )
    assert localize_runtime_text(
        "de",
        "Аудиофайл недоступен (HTTP 404/410) даже после обновления плейлиста. Возможно, файл временно удалён на сервере или эта часть книги недоступна.",
    ).startswith("Die Audiodatei")
    assert localize_runtime_text("uk", "Не выбрано ни одной части.") == "Не вибрано жодної частини."
    assert localize_runtime_text(
        "en", "Загрузка оборвалась: получено 3 B из 10 B."
    ) == "Download was interrupted: received 3 B of 10 B."


def test_help_accessibility_polish_is_present():
    messages = (ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8")
    assert "розташовані в розширених налаштуваннях" in messages

    accessibility = (ROOT / "audioknigi/qt/accessibility.py").read_text(encoding="utf-8")
    assert '"install_keyboard_focus_frame"' in accessibility
    assert '"KeyboardFocusFrameManager"' in accessibility

    context_menu = (ROOT / "audioknigi/qt/localized_context_menu.py").read_text(encoding="utf-8")
    assert "widget.viewport().mapToGlobal(widget.cursorRect().bottomLeft())" in context_menu
    assert "widget.mapToGlobal(widget.rect().bottomLeft())" in context_menu

    help_center = (ROOT / "audioknigi/qt/help_center.py").read_text(encoding="utf-8")
    assert "Leertaste|Пробіл|Esc" in help_center


def test_reviewed_i18n_and_proxy_contracts_remain_intentional():
    assert localize_runtime_text(
        "en", "Анализирую audioknigi.com.ua быстрым HTTP-способом…"
    ) == "Analyzing audioknigi.com.ua using the fast HTTP method…"
    assert localize_runtime_text("en", "История обновлена: 12 записей.") == "History refreshed: 12 entries."

    core = (ROOT / "audioknigi/core.py").read_text(encoding="utf-8")
    health = (ROOT / "audioknigi/services/source_health_service.py").read_text(encoding="utf-8")
    assert "session.trust_env = False" in core
    assert "session.trust_env = False" in health
