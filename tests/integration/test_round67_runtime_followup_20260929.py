from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from audioknigi import network_dns
from audioknigi.services import library_service
from audioknigi.services.queue_service import _parse_created_at

ROOT = Path(__file__).resolve().parents[2]


def test_parked_segment_worker_can_exit_after_active_workers_drain_queue():
    source = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    start = source.index("def worker(worker_id)")
    end = source.index("self.log(", start)
    block = source[start:end]
    parked = block.split("if worker_id >= controller.current_workers():", 1)[1].split("try:", 1)[0]
    assert "if jobs.empty():\n                        return" in parked
    assert parked.index("if jobs.empty():") < parked.index("cancel_event.wait(0.10)")


def test_zero_next_start_is_preserved_in_shared_source_error_payload():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    assert '"expected_end": float(next_start if next_start is not None else start)' in source
    assert 'float(next_start or start)' not in source


def test_support_bundle_has_only_initial_whole_path_collapse_guard():
    source = (ROOT / "audioknigi/diagnostics/support_bundle.py").read_text(encoding="utf-8")
    block = source[source.index("def _privacy_path"):source.index("def _sanitize_log_bytes")]
    assert block.count("collapse_whole_path and original_was_absolute_path") == 1
    assert block.count('return "<configured-path>"') == 1


def test_scan_unfinished_splits_string_selected_indices(tmp_path):
    folder = tmp_path / "Book"
    folder.mkdir()
    (folder / "resume.json").write_text(
        json.dumps({
            "url": "https://poleknig.com/books/123",
            "title": "Demo",
            "selected_indices": "1, 2; 3",
        }),
        encoding="utf-8",
    )
    rows = library_service.scan_unfinished(tmp_path)
    assert len(rows) == 1
    assert rows[0].selected_indices == [1, 2, 3]


def test_queue_created_at_preserves_explicit_zero():
    assert _parse_created_at(0.0) == 0.0
    assert _parse_created_at("0") == 0.0


def test_empty_dns_resolution_raises_clear_gaierror(monkeypatch):
    monkeypatch.setattr(network_dns, "_bypass_cloudflare", lambda _host: False)
    monkeypatch.setattr(network_dns, "current_dns_mode", lambda: network_dns.DNS_MODE_CLOUDFLARE)
    monkeypatch.setattr(network_dns, "_is_numeric_host", lambda _host: False)
    monkeypatch.setattr(network_dns, "_resolve_with_policy", lambda _host, _family: ())
    with pytest.raises(socket.gaierror) as exc_info:
        network_dns._connect_target("no-records.invalid", 443, timeout=0.01)
    assert "No DNS records for no-records.invalid" in str(exc_info.value)


def test_qt_worker_callbacks_are_signal_emitters_not_widget_methods():
    source = (ROOT / "audioknigi/qt/workers.py").read_text(encoding="utf-8")
    start = source.index("callbacks = DownloadCallbacks(")
    end = source.index(")", start) + 1
    block = source[start:end]
    assert "stage=self.stage.emit" in block
    assert "progress=self.progress.emit" in block
    assert "status=self.status.emit" in block


def test_runtime_regex_still_precedes_prefix_fallback():
    source = (ROOT / "audioknigi/i18n.py").read_text(encoding="utf-8")
    regex_pos = source.index("for pattern, variants in _PHASE29_RUNTIME_REGEX")
    prefix_pos = source.index("for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()")
    assert regex_pos < prefix_pos
