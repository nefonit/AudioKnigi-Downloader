"""Focused regressions for the verified V37 external-audit findings."""
from __future__ import annotations

import json
import zipfile

import pytest

from audioknigi.diagnostics import create_support_bundle, sanitized_settings
from audioknigi.domain.models import QueueItem
from audioknigi.diagnostics import logging_utils
from audioknigi.engine import cover_fetch
from audioknigi.providers import extra_sources
from audioknigi.services.search_relevance import _latin, _normalize


def test_support_settings_hide_proxy_endpoint_and_host_allowlist(tmp_path):
    proxy = "https://internal-proxy.example.test:9443"
    hosts = "internal.example.test,private.company.test"
    settings = {
        "proxy_url": proxy, "proxy_only_hosts": hosts, "language": "ru",
        "nested": {"proxy_url": proxy},
    }
    sanitized = sanitized_settings(settings)
    assert sanitized["proxy_url"] == "<configured-proxy>"
    assert sanitized["proxy_only_hosts"] == "<configured-hosts>"
    assert sanitized["nested"]["proxy_url"] == "<configured-proxy>"
    assert sanitized["language"] == "ru"
    target = create_support_bundle(tmp_path / "diagnostics.zip", settings=settings)
    with zipfile.ZipFile(target) as archive:
        body = archive.read("diagnostics/settings.sanitized.json").decode("utf-8")
    assert proxy not in body
    assert hosts not in body
    assert "<configured-proxy>" in body


@pytest.mark.parametrize(
    "mode,legacy,expected_mode,expected_legacy",
    [
        ("off", False, "off", False),
        ("off", True, "single", True),
        ("single", False, "single", True),
        ("two_pass", False, "two_pass", True),
        ("unknown", True, "single", True),
    ],
)
def test_queue_item_preserves_legacy_audio_normalization(
    mode, legacy, expected_mode, expected_legacy
):
    item = QueueItem(url="https://example.test/book", normalization_mode=mode, normalize_audio=legacy)
    assert item.normalization_mode == expected_mode
    assert item.normalize_audio is expected_legacy


def test_search_transliteration_keeps_yi_and_y_and_latin_accents():
    assert _latin(_normalize("Толстой")) == "tolstoy"
    assert _latin(_normalize("Йога")) == "yoga"
    assert _latin(_normalize("Їжак")) == "yizhak"
    assert _normalize("Café") == "cafe"


def test_log_tail_preserves_complete_line_at_byte_window_boundary(tmp_path, monkeypatch):
    limit = 512 * 1024
    prefix = b"previous log data\n"
    first = b"FIRST-COMPLETE-LINE\n"
    last = b"LAST-COMPLETE-LINE\n"
    window = first + b"x" * (limit - len(first) - len(last) - 1) + b"\n" + last
    logfile = tmp_path / "errors.log"
    logfile.write_bytes(prefix + window)
    monkeypatch.setattr(logging_utils, "ERROR_LOG_FILE", logfile)
    result = logging_utils.tail_error_log(max_lines=10)
    assert result.startswith("FIRST-COMPLETE-LINE\n")
    assert result.endswith("LAST-COMPLETE-LINE")


def test_log_tail_drops_partial_first_line(tmp_path, monkeypatch):
    limit = 512 * 1024
    prefix = b"previous log data WITHOUT newline"
    first = b"PARTIAL-LINE\n"
    last = b"LAST-LINE\n"
    window = first + b"x" * (limit - len(first) - len(last) - 1) + b"\n" + last
    logfile = tmp_path / "errors.log"
    logfile.write_bytes(prefix + window)
    monkeypatch.setattr(logging_utils, "ERROR_LOG_FILE", logfile)
    result = logging_utils.tail_error_log(max_lines=10)
    assert "PARTIAL-LINE" not in result
    assert result.endswith("LAST-LINE")


class _FakeResponse:
    def __init__(self, mime: str, payload: bytes):
        self.headers = {"content-type": mime}
        self.payload = payload
        self.iterated = False
        self.closed = False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        self.iterated = True
        yield self.payload

    def close(self):
        self.closed = True


@pytest.mark.parametrize(
    "header,payload,expected",
    [
        ("image/jpeg", b"\xff\xd8\xff" + b"image data", "image/jpeg"),
        ("application/octet-stream", b"\x89PNG\r\n\x1a\n" + b"image data", "image/png"),
        ("binary/octet-stream", b"RIFF" + b"\x00" * 4 + b"WEBPimage data", "image/webp"),
        ("application/octet-stream", b"<html>not an image</html>", None),
        ("text/html", b"<html>not an image</html>", None),
    ],
)
def test_cover_header_early_rejection_and_generic_image_sniffing(
    header, payload, expected, monkeypatch
):
    response = _FakeResponse(header, payload)

    class Session:
        def get(self, *_args, **_kwargs):
            return response

    monkeypatch.setattr(cover_fetch, "get_http_session", lambda: Session())
    result = cover_fetch.fetch_cover_bytes("https://example.test/cover")
    if expected is None:
        assert result is None
    else:
        assert result == (payload, expected)
    assert response.iterated is (header != "text/html")
    assert response.closed


def test_akniga_catalog_functions_part_of_public_wildcard_exports():
    exported = set(extra_sources.__all__)
    assert {"parse_akniga_collection", "fetch_akniga_collection", "search_akniga"} <= exported
    assert callable(extra_sources.search_akniga)
