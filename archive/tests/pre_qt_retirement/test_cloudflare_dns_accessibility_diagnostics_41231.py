"""4.12.31 regressions for screen-reader diagnostics and Cloudflare-only DNS."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import socket
import tkinter as tk

import pytest

from audioknigi import AudioKnigiApp
from audioknigi import accessibility as accessibility_module
from audioknigi import actions as actions_module
from audioknigi import network_dns
from audioknigi import downloader as downloader_module
from audioknigi import search as search_module
from audioknigi.models import SearchResult


@pytest.fixture
def app():
    instance = AudioKnigiApp()
    instance.update_idletasks()
    yield instance
    try:
        instance.destroy()
    except Exception:
        pass


def test_advanced_book_editor_matches_simple_screenreader_contract(app):
    assert app.url_entry.accessible_name == "Название, автор или ссылка"
    assert "Insert+стрелка вверх" in app.url_entry.accessible_description

    spoken = []
    app.url_var.set("Филатов")
    app.open_advanced_tab("book")
    app.url_entry.focus_force()
    app.update()
    app.accessibility.bridge.announce = lambda text, interrupt=False: (spoken.append(text) or True)

    assert app.accessibility.announce_focused_editable_text() is True
    assert spoken and "Филатов" in spoken[-1]
    assert "Название, автор или ссылка" in spoken[-1]


def test_advanced_search_and_queue_editors_advertise_insert_up(app):
    assert app.search_query_entry.accessible_name == "Поисковый запрос"
    assert "Insert+стрелка вверх" in app.search_query_entry.accessible_description
    assert app.queue_url_entry.accessible_name == "Ссылка для очереди"
    assert "Insert+стрелка вверх" in app.queue_url_entry.accessible_description


def test_insert_up_speech_emits_diagnostic_log(app, monkeypatch):
    logs = []
    monkeypatch.setattr(accessibility_module.app_logger, "info", lambda fmt, *args, **kwargs: logs.append(fmt % args if args else fmt))
    monkeypatch.setattr(app.accessibility.bridge, "announce", lambda text, interrupt=False: True)
    app.url_var.set("Крысиные гонки")
    app.url_entry.focus_force()
    app.update()

    assert app.accessibility.announce_focused_editable_text() is True
    assert any("SCREEN READER READ LINE" in line and "Крысиные гонки" in line for line in logs)
    assert any("SCREEN READER READ LINE | delivered=True" in line for line in logs)


def test_layout_independent_vk_hotkey_emits_diagnostic(app, monkeypatch):
    logs = []
    monkeypatch.setattr(actions_module.app_logger, "info", lambda fmt, *args, **kwargs: logs.append(fmt % args if args else fmt))
    monkeypatch.setattr(actions_module.sys, "platform", "win32")
    monkeypatch.setattr(app, "_focus_url", lambda: None)

    result = app._physical_global_shortcut(SimpleNamespace(state=0x0004, keycode=76, keysym="Cyrillic_de"))
    assert result == "break"
    assert any("HOTKEY | shortcut=Ctrl+L" in line and "vk=76" in line and "windows_vk" in line for line in logs)


def test_search_focus_and_announcement_are_diagnosable(app, monkeypatch):
    spoken = []
    logs = []
    monkeypatch.setattr(app.accessibility, "announce", lambda text, interrupt=False: (spoken.append(text) or True))
    monkeypatch.setattr(search_module.app_logger, "info", lambda fmt, *args, **kwargs: logs.append(fmt % args if args else fmt))
    app.open_advanced_tab("search")
    app.search_results = [
        SearchResult(title="Книга", author="Автор", url="https://poleknig.com/books/1", source="poleknig.com")
    ]
    app._refresh_search_results()
    app.update()

    assert app.focus_get() == app.search_tree
    assert app.search_tree.selection() == ("0",)
    assert any("SEARCH ACCESSIBILITY | focus_moved=True" in line for line in logs)
    assert any("announcement_delivered=True" in line for line in logs)
    assert any("Фокус переведён в таблицу" in text for text in spoken)


def test_cloudflare_public_resolution_never_uses_system_dns_for_hostname(monkeypatch):
    original_calls = []
    monkeypatch.setattr(network_dns, "_resolve", lambda host, family: ("203.0.113.7",))

    def fake_original(host, port, family=0, type=0, proto=0, flags=0):
        original_calls.append(str(host))
        # The only permitted original-getaddrinfo call is on the already
        # Cloudflare-resolved numeric address, never on example.com itself.
        assert str(host) == "203.0.113.7"
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("203.0.113.7", port))]

    monkeypatch.setattr(network_dns, "_ORIGINAL_GETADDRINFO", fake_original)
    result = network_dns.cloudflare_getaddrinfo("example.com", 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    assert result[0][4] == ("203.0.113.7", 443)
    assert original_calls == ["203.0.113.7"]


def test_cloudflare_local_and_numeric_hosts_do_not_need_public_doh(monkeypatch):
    sentinel = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 80))]
    monkeypatch.setattr(network_dns, "_ORIGINAL_GETADDRINFO", lambda *args, **kwargs: sentinel)
    monkeypatch.setattr(network_dns, "_resolve", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("DoH should not run")))
    assert network_dns.cloudflare_getaddrinfo("localhost", 80) is sentinel
    assert network_dns.cloudflare_getaddrinfo("127.0.0.1", 80) is sentinel


def test_cloudflare_target_connection_resolves_before_connect(monkeypatch):
    seen = []
    fake_socket = object()
    monkeypatch.setattr(network_dns, "_resolve", lambda host, family: ("198.51.100.9",))
    monkeypatch.setattr(
        network_dns,
        "_ORIGINAL_CREATE_CONNECTION",
        lambda address, timeout=0, **kwargs: (seen.append((address, timeout)) or fake_socket),
    )
    assert network_dns._connect_target("example.com", 443, timeout=7.5) is fake_socket
    assert seen == [(('198.51.100.9', 443), 7.5)]


def test_playwright_launch_uses_local_cloudflare_proxy_and_disables_quic(monkeypatch):
    monkeypatch.setattr(network_dns, "ensure_cloudflare_playwright_proxy", lambda: "http://127.0.0.1:45678")
    options = network_dns.cloudflare_playwright_launch_kwargs()
    assert options["proxy"]["server"] == "http://127.0.0.1:45678"
    assert "--disable-quic" in options["args"]
    assert any("cloudflare-dns.com/dns-query" in arg for arg in options["args"])
    assert any("dns-over-https-mode=secure" in arg for arg in options["args"])


def test_every_playwright_launch_uses_cloudflare_proxy_options():
    project = Path(__file__).resolve().parents[1]
    for rel in ("audioknigi/poleknig.py", "audioknigi/downloader.py"):
        text = (project / rel).read_text(encoding="utf-8")
        launches = [line for line in text.splitlines() if ".chromium.launch(" in line]
        assert launches
        assert all("cloudflare_playwright_launch_kwargs" in line for line in launches)



def test_advanced_book_editor_text_query_opens_search_and_runs_it(app, monkeypatch):
    calls = []
    app.open_advanced_tab("book")
    app.url_var.set("Дик Фрэнсис")
    monkeypatch.setattr(app, "search_books", lambda: (calls.append("search") or True))

    assert app.analyze() is True
    assert app.search_query_var.get() == "Дик Фрэнсис"
    assert calls == ["search"]
    assert app._active_advanced_tab_key() == "search"


def test_http_session_ignores_environment_proxy_to_preserve_cloudflare_dns():
    from audioknigi.core import build_http_session
    session = build_http_session()
    try:
        assert session.trust_env is False
    finally:
        session.close()

def test_python_http_code_has_no_direct_requests_shortcut_around_session():
    project = Path(__file__).resolve().parents[1] / "audioknigi"
    offenders = []
    for path in project.glob("*.py"):
        if path.name == "network_dns.py":
            continue
        text = path.read_text(encoding="utf-8")
        for token in ("requests.get(", "requests.post(", "requests.head(", "requests.request("):
            if token in text:
                offenders.append((path.name, token))
    assert offenders == []


def test_remote_ffprobe_uses_cloudflare_resolving_proxy(app, monkeypatch):
    captured = {}
    url = "https://media.example.invalid/audio-41231.mp3"
    monkeypatch.setattr(downloader_module, "resolve_executable", lambda name: "ffprobe" if name == "ffprobe" else None)
    monkeypatch.setattr(
        downloader_module,
        "cloudflare_ffmpeg_input_args",
        lambda: ["-http_proxy", "http://127.0.0.1:45678"],
    )

    def fake_run(cmd, timeout):
        captured["cmd"] = list(cmd)
        captured["timeout"] = timeout
        return 123.5

    monkeypatch.setattr(app, "_run_ffprobe_duration_command", fake_run)
    assert app._probe_remote_duration(url, "https://poleknig.com/books/1") == 123.5
    cmd = captured["cmd"]
    assert "-http_proxy" in cmd
    proxy_index = cmd.index("-http_proxy")
    assert cmd[proxy_index + 1] == "http://127.0.0.1:45678"
    assert proxy_index < cmd.index(url)


def test_destroy_after_mode_tab_cycle_clears_default_root_and_keeps_next_editor_bound():
    first = AudioKnigiApp()
    second = None
    try:
        first.update_idletasks()
        first.ui_mode_var.set("Расширенный")
        first._apply_ui_mode()
        for tab in ("book", "search", "queue"):
            first._select_advanced_tab(tab)
        first.destroy()
        assert getattr(tk, "_default_root", None) is None

        second = AudioKnigiApp()
        second.update_idletasks()
        second.ui_mode_var.set("Простой")
        second._apply_ui_mode()
        second.url_var.set("Толстой Война и мир")
        second.update_idletasks()
        assert second.easy_url_entry.get() == "Толстой Война и мир"
        assert second.url_entry.get() == "Толстой Война и мир"
        assert second.url_var._tk is second.tk
    finally:
        try:
            first.destroy()
        except Exception:
            pass
        if second is not None:
            try:
                second.destroy()
            except Exception:
                pass

