from __future__ import annotations

from pathlib import Path
import socket

import pytest

from audioknigi import network_dns
from audioknigi.config.settings import normalize_settings

ROOT = Path(__file__).resolve().parents[2]


def _system_fake(host, port, family=0, type=0, proto=0, flags=0):
    host = str(host)
    if host == "example.com" or host.endswith(".example"):
        address = "203.0.113.44"
    else:
        address = host
    fam = socket.AF_INET6 if ":" in address else socket.AF_INET
    return [(fam, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))]


def setup_function(_function):
    network_dns.configure_dns_mode("auto")
    network_dns._reset_dns_runtime_state()


def teardown_function(_function):
    network_dns.configure_dns_mode("auto")
    network_dns._reset_dns_runtime_state()


def test_dns_setting_defaults_to_auto_and_invalid_value_is_normalized():
    assert normalize_settings({})["dns_mode"] == "auto"
    assert normalize_settings({"dns_mode": "garbage"})["dns_mode"] == "auto"
    assert normalize_settings({"dns_mode": "cloudflare"})["dns_mode"] == "cloudflare"
    assert normalize_settings({"dns_mode": "system"})["dns_mode"] == "system"


def test_auto_mode_falls_back_to_system_on_cloudflare_transport_failure(monkeypatch):
    def fail_cloudflare(host, family):
        raise socket.gaierror(socket.EAI_AGAIN, "Cloudflare TLS handshake timed out")

    monkeypatch.setattr(network_dns, "_resolve", fail_cloudflare)
    monkeypatch.setattr(network_dns, "_ORIGINAL_GETADDRINFO", _system_fake)
    network_dns.configure_dns_mode("auto")

    rows = network_dns.cloudflare_getaddrinfo(
        "example.com", 443, socket.AF_UNSPEC, socket.SOCK_STREAM
    )

    assert rows[0][4] == ("203.0.113.44", 443)
    status = network_dns.dns_runtime_status()
    assert status["fallback_active"] is True
    assert status["fallback_event"] >= 1
    assert status["failures"] == 1


def test_auto_mode_opens_circuit_and_skips_cloudflare_until_cooldown(monkeypatch):
    calls = []

    def fail_cloudflare(host, family):
        calls.append(host)
        raise socket.gaierror(socket.EAI_AGAIN, "DoH unavailable")

    monkeypatch.setattr(network_dns, "_resolve", fail_cloudflare)
    monkeypatch.setattr(network_dns, "_ORIGINAL_GETADDRINFO", _system_fake)
    network_dns.configure_dns_mode("auto")

    for host in ("one.example", "two.example", "three.example"):
        network_dns.cloudflare_getaddrinfo(host, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)

    status = network_dns.dns_runtime_status()
    assert status["circuit_open"] is True
    assert status["retry_after_seconds"] > 0
    assert len(calls) == network_dns.CLOUDFLARE_FAILURE_THRESHOLD

    network_dns.cloudflare_getaddrinfo("four.example", 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    assert len(calls) == network_dns.CLOUDFLARE_FAILURE_THRESHOLD


def test_cloudflare_only_mode_never_uses_system_fallback(monkeypatch):
    original_calls = []

    def fail_cloudflare(host, family):
        raise socket.gaierror(socket.EAI_AGAIN, "DoH unavailable")

    def original(*args, **kwargs):
        original_calls.append(args[0])
        return _system_fake(*args, **kwargs)

    monkeypatch.setattr(network_dns, "_resolve", fail_cloudflare)
    monkeypatch.setattr(network_dns, "_ORIGINAL_GETADDRINFO", original)
    network_dns.configure_dns_mode("cloudflare")

    with pytest.raises(socket.gaierror):
        network_dns.cloudflare_getaddrinfo("example.com", 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    assert original_calls == []


def test_system_mode_bypasses_cloudflare_for_python_playwright_and_ffmpeg(monkeypatch):
    monkeypatch.setattr(network_dns, "_ORIGINAL_GETADDRINFO", _system_fake)
    monkeypatch.setattr(
        network_dns,
        "_resolve",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("DoH must not run")),
    )
    monkeypatch.setattr(
        network_dns,
        "ensure_cloudflare_playwright_proxy",
        lambda: (_ for _ in ()).throw(AssertionError("proxy must not run")),
    )
    network_dns.configure_dns_mode("system")

    assert network_dns.cloudflare_getaddrinfo("example.com", 443)[0][4][0] == "203.0.113.44"
    assert network_dns.cloudflare_ffmpeg_input_args() == []
    options = network_dns.cloudflare_playwright_launch_kwargs()
    assert "proxy" not in options
    assert "--dns-over-https-mode=off" in options["args"]


def test_auto_mode_keeps_shared_proxy_for_playwright_and_ffmpeg(monkeypatch):
    monkeypatch.setattr(network_dns, "ensure_cloudflare_playwright_proxy", lambda: "http://127.0.0.1:45555")
    network_dns.configure_dns_mode("auto")

    assert network_dns.cloudflare_ffmpeg_input_args() == ["-http_proxy", "http://127.0.0.1:45555"]
    options = network_dns.cloudflare_playwright_launch_kwargs()
    assert options["proxy"]["server"] == "http://127.0.0.1:45555"
    assert "--disable-quic" in options["args"]
    assert any("dns-over-https-mode=secure" in arg for arg in options["args"])


def test_round58_timeout_and_circuit_are_bounded():
    assert 0.5 <= network_dns.CLOUDFLARE_DOH_TIMEOUT <= 2.0
    assert network_dns.CLOUDFLARE_FAILURE_THRESHOLD == 3
    assert network_dns.CLOUDFLARE_CIRCUIT_COOLDOWN_SECONDS == 300.0


def test_cached_cloudflare_answer_does_not_fake_recovery(monkeypatch):
    network_dns.configure_dns_mode("auto")
    network_dns._record_cloudflare_failure(socket.gaierror(socket.EAI_AGAIN, "DoH unavailable"))
    key = ("cached.example", 1)
    with network_dns._CACHE_LOCK:
        network_dns._CACHE[key] = (network_dns.time.monotonic() + 60.0, ("203.0.113.8",))

    monkeypatch.setattr(
        network_dns,
        "_query_cloudflare_json",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("live DoH must not run")),
    )
    assert network_dns._resolve_with_policy("cached.example", socket.AF_INET) == ("203.0.113.8",)
    assert network_dns.dns_runtime_status()["fallback_active"] is True


def test_live_cloudflare_success_announces_recovery(monkeypatch):
    network_dns.configure_dns_mode("auto")
    network_dns._record_cloudflare_failure(socket.gaierror(socket.EAI_AGAIN, "DoH unavailable"))
    before = int(network_dns.dns_runtime_status()["recovery_event"])
    with network_dns._CACHE_LOCK:
        network_dns._CACHE.pop(("fresh.example", 1), None)
    monkeypatch.setattr(
        network_dns,
        "_query_cloudflare_json",
        lambda *args, **kwargs: (("203.0.113.9",), 60, "1.1.1.1"),
    )

    assert network_dns._resolve_with_policy("fresh.example", socket.AF_INET) == ("203.0.113.9",)
    status = network_dns.dns_runtime_status()
    assert status["fallback_active"] is False
    assert int(status["recovery_event"]) == before + 1


def test_auto_mode_limits_cloudflare_bootstraps_to_ipv4_pair():
    source = (ROOT / "audioknigi/network_dns.py").read_text(encoding="utf-8")
    assert "CLOUDFLARE_BOOTSTRAP_IPS[:2]" in source


def test_qt_exposes_dns_mode_and_accessible_fallback_feedback():
    pages = (ROOT / "audioknigi/qt/main_window_pages.py").read_text(encoding="utf-8")
    settings = (ROOT / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    sync = (ROOT / "audioknigi/qt/settings_sync.py").read_text(encoding="utf-8")
    accessibility = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    window = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    application = (ROOT / "audioknigi/qt/application.py").read_text(encoding="utf-8")

    assert '"dns_mode_combo"' in pages
    assert '"Автоматически — Cloudflare с резервным системным DNS"' in pages
    assert '"dns_mode": self.dns_mode_combo.currentData() or "auto"' in settings
    assert 'install_cloudflare_dns(mode=str(updated.get("dns_mode", "auto") or "auto"))' in settings
    assert '("dns_mode_combo", data.get("dns_mode", "auto"))' in sync
    assert "def _poll_dns_runtime_status" in accessibility
    assert "автоматически переключилась на системный DNS" in accessibility
    assert "_dns_status_timer.timeout.connect(self._poll_dns_runtime_status)" in window
    assert 'install_cloudflare_dns(mode=str(settings.get("dns_mode", "auto") or "auto"))' in application


def test_help_center_explains_automatic_dns_recovery():
    help_text = (ROOT / "audioknigi/qt/help_center.py").read_text(encoding="utf-8")
    assert "пятиминутная пауза для Cloudflare" in help_text
    assert "Такое переключение видно на экране и объявляется NVDA/JAWS" in help_text
