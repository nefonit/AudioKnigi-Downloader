from __future__ import annotations

import json
from pathlib import Path

import pytest

from audioknigi.diagnostics.support_bundle import _sanitize_log_bytes, _tail
from audioknigi.download.probe import ProbeMixin
from audioknigi.models import Book, Track
from audioknigi.qt.acceptance_contract import ACCEPTANCE_SCHEMA, acceptance_issues
from tools import qt_localization_audit, qt_windows_acceptance


def test_support_tail_drops_partial_line_that_can_hide_windows_path_prefix(tmp_path):
    path = tmp_path / "app.log"
    path.write_bytes(
        ("prefix " + "X" * 80 + r"C:\Users\Alice\Private\Book\chapter.mp3" + "\r\n").encode("utf-8")
    )
    payload = _tail(path, max_bytes=24, privacy_safe=True)
    assert payload == b"[truncated]\n"
    sanitized = _sanitize_log_bytes(payload).decode("utf-8")
    assert "Alice" not in sanitized
    assert "Private" not in sanitized


def test_support_tail_keeps_complete_following_line_after_truncated_prefix(tmp_path):
    path = tmp_path / "app.log"
    path.write_bytes(
        ("X" * 80 + "\r\n" + "safe final diagnostic\r\n").encode("utf-8")
    )
    payload = _tail(path, max_bytes=30)
    assert payload.decode("utf-8") == "safe final diagnostic\r\n"


@pytest.mark.parametrize("selection", [[1.5], [float("nan")], [float("inf")], 1.5, True])
def test_space_estimation_rejects_fractional_nonfinite_and_boolean_indices(selection):
    book = Book(url="https://example.invalid/book", title="Book")
    with pytest.raises(ValueError, match="Invalid selected track index"):
        ProbeMixin()._estimate_required_space(book, selection)


def test_space_estimation_accepts_scalar_integer_index(tmp_path):
    class Probe(ProbeMixin):
        def _book_folder(self, *args, **kwargs):
            return tmp_path

    book = Book(url="https://example.invalid/book", title="Book", tracks=[
        Track(index=0, title="Zero", file="https://example.invalid/0.mp3", duration=10),
        Track(index=1, title="One", file="https://example.invalid/1.mp3", duration=20),
    ])
    probe = Probe()
    assert probe._estimate_required_space(book, 1) == probe._estimate_required_space(book, [1])


def test_localization_detects_icon_text_overloads_and_constructor_fstring(tmp_path, monkeypatch):
    monkeypatch.setattr(qt_localization_audit, "ROOT", tmp_path)
    sample = tmp_path / "sample.py"
    sample.write_text(
        'QAction(icon, "Открыть", parent)\n'
        'QPushButton(icon, "Пуск", parent)\n'
        'menu.addAction(icon, "Действие")\n'
        'combo.addItem(icon, "Выбор", data)\n'
        'QLabel(text=f"Глав: {count}")\n',
        encoding="utf-8",
    )
    direct = qt_localization_audit._direct_visible_russian(sample)
    dynamic = qt_localization_audit._unwrapped_dynamic_visible_russian(sample)
    assert len(direct) == 4
    assert len(dynamic) == 1


def test_acceptance_issues_treat_malformed_schema_as_incomplete():
    report = {
        "schema": [],
        "app_version": "",
        "platform": "windows",
        "automated": {},
        "screen_readers": {},
    }
    issues = acceptance_issues(report, app_version="", require_windows=True)
    assert "unsupported acceptance schema" in issues


def test_candidate_manifest_malformed_schema_is_rejected_cleanly(tmp_path):
    exe = tmp_path / "app.exe"
    exe.write_bytes(b"binary")
    manifest = tmp_path / "candidate.json"
    manifest.write_text(json.dumps({
        "schema": [],
        "app_version": "",
        "migration_stage": "",
        "platform": "windows",
        "exe_sha256": "",
        "automated": {},
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        qt_windows_acceptance.validate_candidate_manifest(
            manifest, exe, require_windows=False
        )


def test_acceptance_main_returns_43_for_malformed_candidate_schema(tmp_path, monkeypatch):
    exe = tmp_path / "app.exe"
    exe.write_bytes(b"binary")
    manifest = tmp_path / "candidate.json"
    manifest.write_text(json.dumps({"schema": []}), encoding="utf-8")
    report = tmp_path / "report.json"
    result = qt_windows_acceptance.main([
        "--exe", str(exe),
        "--report", str(report),
        "--candidate-manifest", str(manifest),
        "--allow-non-windows",
        "--automated-only",
    ])
    assert result == 43
