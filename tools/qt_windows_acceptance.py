from __future__ import annotations

"""Interactive Windows acceptance runner for the exact frozen Qt EXE.

The tool re-runs the automated frozen gates, launches the EXE with the passive
focus tracer, records NVDA/JAWS checklist results incrementally, and ties the
report to the executable's SHA-256.  It never changes application settings; it only records release-signoff evidence for the exact EXE.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audioknigi.metadata import APP_VERSION  # noqa: E402
from audioknigi.qt import QT_MIGRATION_STAGE  # noqa: E402
from audioknigi.qt.acceptance_contract import (  # noqa: E402
    ACCEPTANCE_SCHEMA,
    MANUAL_CHECKS,
    REQUIRED_SCREEN_READERS,
    acceptance_complete,
    acceptance_issues,
    load_report,
    save_report,
    sha256_file,
    summarize_focus_trace,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_candidate_manifest(path: Path, exe: Path, *, require_windows: bool = True) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Release-candidate manifest not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Release-candidate manifest root must be an object")
    expected_hash = sha256_file(exe)
    problems: list[str] = []
    if int(data.get("schema", 0) or 0) != ACCEPTANCE_SCHEMA:
        problems.append("schema")
    if str(data.get("app_version", "")) != APP_VERSION:
        problems.append("app_version")
    if str(data.get("migration_stage", "")) != QT_MIGRATION_STAGE:
        problems.append("migration_stage")
    if require_windows and str(data.get("platform", "")).lower() != "windows":
        problems.append("platform")
    if str(data.get("exe_sha256", "")).lower() != expected_hash.lower():
        problems.append("exe_sha256")
    automated = data.get("automated", {})
    if not isinstance(automated, dict):
        automated = {}
    for gate in ("runtime", "accessibility", "playwright_edge", "import_boundary", "frozen_module_boundary"):
        value = automated.get(gate, "")
        status = value.get("status", "") if isinstance(value, dict) else value
        if str(status or "").strip().lower() != "pass":
            problems.append(f"automated.{gate}")
    if problems:
        raise ValueError("Release-candidate manifest mismatch: " + ", ".join(problems))
    return data


def _new_report(exe: Path) -> dict[str, Any]:
    return {
        "schema": ACCEPTANCE_SCHEMA,
        "app_version": APP_VERSION,
        "migration_stage": QT_MIGRATION_STAGE,
        "platform": "windows" if os.name == "nt" else platform.system().lower(),
        "exe": exe.name,
        "exe_sha256": sha256_file(exe),
        "created_utc": _utc_now(),
        "updated_utc": _utc_now(),
        "automated": {},
        "screen_readers": {},
        "status": "incomplete",
    }


def _refresh_status(report: dict[str, Any], *, require_windows: bool = True) -> None:
    report["updated_utc"] = _utc_now()
    report["status"] = "pass" if acceptance_complete(
        report,
        app_version=APP_VERSION,
        exe_sha256=str(report.get("exe_sha256", "")),
        require_windows=require_windows,
    ) else "incomplete"


def _load_or_create(report_path: Path, exe: Path) -> dict[str, Any]:
    current_hash = sha256_file(exe)
    if report_path.exists():
        try:
            report = load_report(report_path)
        except Exception:
            report = _new_report(exe)
        if (
            str(report.get("app_version", "")) != APP_VERSION
            or str(report.get("exe_sha256", "")).lower() != current_hash.lower()
        ):
            # Never carry manual approval from a different binary forward.
            report = _new_report(exe)
    else:
        report = _new_report(exe)
    return report


def _run_gate(exe: Path, flag: str, report_env: str, output_file: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env[report_env] = str(output_file)
    output_file.unlink(missing_ok=True)
    started = _utc_now()
    try:
        completed = subprocess.run([str(exe), flag], env=env, timeout=180, check=False)
        exit_code = int(completed.returncode)
    except subprocess.TimeoutExpired:
        return {"status": "fail", "exit_code": None, "started_utc": started, "detail": "timeout"}
    except OSError as exc:
        return {"status": "fail", "exit_code": None, "started_utc": started, "detail": str(exc)}
    text = ""
    if output_file.exists():
        try:
            text = output_file.read_text(encoding="utf-8-sig", errors="replace")
        except Exception:
            text = ""
    ok = exit_code == 0 and text.startswith("OK")
    return {
        "status": "pass" if ok else "fail",
        "exit_code": exit_code,
        "started_utc": started,
        "report_file": output_file.name,
        "report_ok": text.startswith("OK"),
    }


def run_automated_gates(
    exe: Path, report: dict[str, Any], report_path: Path, *, require_windows: bool = True
) -> None:
    out_dir = report_path.parent
    gates = (
        ("runtime", "--qt-runtime-selftest", "AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT", out_dir / "acceptance_runtime.txt"),
        ("accessibility", "--qt-accessibility-selftest", "AUDIOKNIGI_QT_ACCESSIBILITY_SELFTEST_REPORT", out_dir / "acceptance_accessibility.txt"),
        ("playwright_edge", "--playwright-edge-selftest", "AUDIOKNIGI_PLAYWRIGHT_SELFTEST_REPORT", out_dir / "acceptance_playwright_edge.txt"),
    )
    for name, flag, env_name, output in gates:
        print(f"Автоматическая проверка: {name} ...")
        report.setdefault("automated", {})[name] = _run_gate(exe, flag, env_name, output)
        _refresh_status(report, require_windows=require_windows)
        save_report(report_path, report)
        print(f"  {report['automated'][name]['status']}")


def _answer(prompt: str) -> str:
    while True:
        value = input(prompt).strip().lower()
        if value in {"y", "yes", "д", "да"}:
            return "pass"
        if value in {"n", "no", "н", "нет"}:
            return "fail"
        if value in {"s", "skip", "п", "пропустить"}:
            return "skip"
        print("Введите y/д = прошло, n/н = ошибка, s/п = пропустить.")


def _manual_status(checks: dict[str, Any], key: str) -> str:
    value = checks.get(key, {})
    if isinstance(value, dict):
        value = value.get("status", "")
    return str(value or "").strip().lower()


def run_manual_reader(
    exe: Path,
    report: dict[str, Any],
    report_path: Path,
    reader: str,
    *,
    retest_all: bool = False,
    require_windows: bool = True,
) -> None:
    reader = reader.lower()
    if reader not in REQUIRED_SCREEN_READERS:
        raise ValueError(reader)

    readers = report.setdefault("screen_readers", {})
    existing = readers.get(reader, {})
    if not isinstance(existing, dict):
        existing = {}
    checks = existing.get("checks", {})
    if not isinstance(checks, dict) or retest_all:
        checks = {}

    pending = [
        check for check in MANUAL_CHECKS
        if retest_all or _manual_status(checks, check.key) != "pass"
    ]
    if not pending:
        print()
        print(f"=== Ручная проверка {reader.upper()} ===")
        print("Все обязательные пункты этого скринридера уже отмечены как пройденные для текущего EXE.")
        return

    trace = report_path.parent / f"focus_trace_{reader}.jsonl"
    trace.unlink(missing_ok=True)
    print()
    print(f"=== Ручная проверка {reader.upper()} ===")
    if checks and not retest_all:
        print(f"Повторяем только непройденные пункты: {len(pending)} из {len(MANUAL_CHECKS)}.")
    print("Убедитесь, что нужный скринридер запущен. Программа сейчас откроется с пассивной записью фокуса.")
    print("Для каждого пункта: Alt+Tab в программу, выполните действие, затем Alt+Tab обратно и ответьте.")

    block: dict[str, Any] = dict(existing)
    block["started_utc"] = _utc_now()
    block["trace_file"] = trace.name
    block["checks"] = checks
    readers[reader] = block
    save_report(report_path, report)

    input("Нажмите Enter для запуска Qt EXE...")
    process = subprocess.Popen([str(exe), f"--qt-focus-trace={trace}"])
    try:
        pending_keys = {check.key for check in pending}
        for index, check in enumerate(MANUAL_CHECKS, 1):
            if check.key not in pending_keys:
                print(f"[{index}/{len(MANUAL_CHECKS)}] {check.title}: уже прошло, пропускаю.")
                continue
            print()
            print(f"[{index}/{len(MANUAL_CHECKS)}] {check.title}")
            print(check.instruction)
            status = _answer("Результат [y=прошло / n=ошибка / s=пропустить]: ")
            row: dict[str, Any] = {
                "status": status,
                "required": bool(check.required),
                "checked_utc": _utc_now(),
            }
            if status == "fail":
                detail = input("Кратко опишите проблему (или Enter без комментария): ").strip()
                if detail:
                    row["detail"] = detail
            checks[check.key] = row
            _refresh_status(report, require_windows=require_windows)
            save_report(report_path, report)
    finally:
        block["finished_utc"] = _utc_now()
        if process.poll() is None:
            print("Закройте окно AudioKnigi Downloader Qt. Если оно уже скрыто в трее, выберите Выход.")
            try:
                process.wait(timeout=90)
            except subprocess.TimeoutExpired:
                print("Qt EXE всё ещё работает; acceptance runner завершает только тестовый экземпляр.")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        block["app_exit_code"] = process.returncode
        block["trace_summary"] = summarize_focus_trace(trace)
        _refresh_status(report, require_windows=require_windows)
        save_report(report_path, report)


def print_status(
    report: dict[str, Any], exe: Path | None = None, *, require_windows: bool = True
) -> int:
    expected_hash = sha256_file(exe) if exe is not None and exe.exists() else None
    issues = acceptance_issues(
        report,
        app_version=APP_VERSION,
        exe_sha256=expected_hash,
        require_windows=require_windows,
    )
    print(f"Qt acceptance status: {'PASS' if not issues else 'INCOMPLETE'}")
    print(f"App: {report.get('app_version', '')}; stage: {report.get('migration_stage', '')}")
    print(f"EXE SHA-256: {report.get('exe_sha256', '')}")
    if issues:
        print("Не пройдено:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Все автоматические + NVDA + JAWS gates пройдены для этого точного EXE.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Windows NVDA/JAWS acceptance runner for the Qt EXE")
    parser.add_argument("--exe", default=str(ROOT / "dist" / "AudioKnigiDownloader_Qt.exe"))
    parser.add_argument("--report", default=str(ROOT / "dist" / "qt_windows_acceptance.json"))
    parser.add_argument("--candidate-manifest", default=str(ROOT / "dist" / "qt_release_candidate.json"))
    parser.add_argument("--automated-only", action="store_true")
    parser.add_argument("--reader", choices=("nvda", "jaws", "both"), default="both")
    parser.add_argument("--retest-all", action="store_true", help="Повторить также уже пройденные ручные пункты")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--allow-non-windows", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    exe = Path(args.exe).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    candidate_path = Path(args.candidate_manifest).expanduser().resolve()
    if not exe.exists():
        print(f"Qt EXE не найден: {exe}", file=sys.stderr)
        return 41
    if os.name != "nt" and not args.allow_non_windows:
        print("Финальная NVDA/JAWS acceptance допускается только на Windows.", file=sys.stderr)
        return 42
    require_windows = not args.allow_non_windows
    try:
        validate_candidate_manifest(candidate_path, exe, require_windows=require_windows)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Release-candidate manifest rejected: {exc}", file=sys.stderr)
        return 43

    report = _load_or_create(report_path, exe)
    report["candidate_manifest"] = candidate_path.name
    if args.status:
        return print_status(report, exe, require_windows=require_windows)

    try:
        run_automated_gates(exe, report, report_path, require_windows=require_windows)
        if not args.automated_only:
            readers = REQUIRED_SCREEN_READERS if args.reader == "both" else (args.reader,)
            for reader in readers:
                run_manual_reader(
                    exe, report, report_path, reader,
                    retest_all=args.retest_all, require_windows=require_windows,
                )
    except KeyboardInterrupt:
        _refresh_status(report, require_windows=require_windows)
        save_report(report_path, report)
        print("\nAcceptance прерван пользователем. Уже введённые результаты сохранены; traceback не требуется.")
        print(f"Отчёт сохранён: {report_path}")
        return 130

    _refresh_status(report, require_windows=require_windows)
    save_report(report_path, report)
    print()
    print(f"Отчёт сохранён: {report_path}")
    return print_status(report, exe, require_windows=require_windows)


if __name__ == "__main__":
    raise SystemExit(main())
