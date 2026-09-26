from __future__ import annotations

"""Machine-readable Windows acceptance contract for the Qt release candidate.

The Qt-only source is complete, but a concrete frozen Windows EXE is not
release-signoff ready until its exact SHA-256 has passed all frozen self-tests
and the complete manual matrix with both NVDA and JAWS.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ACCEPTANCE_SCHEMA = 1
REQUIRED_AUTOMATED_GATES = ("runtime", "accessibility", "playwright_edge")
REQUIRED_SCREEN_READERS = ("nvda", "jaws")


@dataclass(frozen=True, slots=True)
class ManualCheck:
    key: str
    title: str
    instruction: str
    required: bool = True


MANUAL_CHECKS: tuple[ManualCheck, ...] = (
    ManualCheck("startup", "Запуск и первый фокус", "Запусти Qt EXE. Окно должно открыться один раз, без зависания и без потери фокуса."),
    ManualCheck("tabs", "Tab и Shift+Tab", "Пройди элементы Tab и Shift+Tab на всех вкладках. Фокус не должен исчезать, зацикливаться или уходить за окно."),
    ManualCheck("book_url", "Поле ссылки", "В поле ссылки введи и отредактируй текст. Скринридер должен читать ввод, курсор и выделение штатными командами."),
    ManualCheck("analysis_tracks", "Анализ и таблица частей", "Проанализируй книгу. После анализа должна быть выбрана первая часть; стрелки читают строки, Пробел переключает выбор."),
    ManualCheck("search", "Поиск и результаты", "Выполни поиск. После результата фокус должен перейти на первую строку; стрелки читают строки, Enter выбирает книгу."),
    ManualCheck("combobox", "ComboBox", "Проверь озвучку и несколько списков настроек. Открытие, стрелки, выбранное значение и закрытие должны озвучиваться корректно."),
    ManualCheck("queue", "Очередь", "Добавь книгу в очередь и пройди таблицу/кнопки. Статус, приоритет и действия должны быть понятны без мыши."),
    ManualCheck("history", "История", "Открой историю и пройди строки/действия. Название, путь/статус и кнопки должны читаться предсказуемо."),
    ManualCheck("settings", "Настройки", "Проверь поля, флажки, списки и кнопки настроек. Имена и состояния должны быть однозначными."),
    ManualCheck("player", "Плеер", "Открой локальный MP3. Проверь Play/Pause/Stop, громкость, скорость и позицию: позиция должна читаться в секундах, а не миллисекундах."),
    ManualCheck("modal", "Модальные окна", "Открой вопрос/предупреждение. Tab остаётся внутри диалога, фон не активируется, Escape выполняет безопасное действие/закрытие."),
    ManualCheck("tray", "Системный трей", "Скрой окно в трей и восстанови его. После восстановления фокус должен вернуться в рабочее окно без второго экземпляра."),
    ManualCheck("announcements", "Статусы и ошибки", "Запусти анализ/скачивание. Обычные статусы не должны перебивать речь непрерывно; важная ошибка должна быть объявлена сразу."),
    ManualCheck("focus_stress", "Стресс фокуса", "Не менее двух минут быстро перемещайся Tab/Shift+Tab, стрелками и между вкладками. Не должно быть RecursionError, зависания или самопроизвольного прыганья."),
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _status(value: Any) -> str:
    if isinstance(value, Mapping):
        value = value.get("status", "")
    return str(value or "").strip().lower()


def acceptance_issues(
    report: Mapping[str, Any],
    *,
    app_version: str | None = None,
    exe_sha256: str | None = None,
    require_windows: bool = True,
) -> list[str]:
    issues: list[str] = []
    try:
        schema = int(report.get("schema", 0) or 0)
    except (TypeError, ValueError, OverflowError):
        schema = 0
    if schema != ACCEPTANCE_SCHEMA:
        issues.append("unsupported acceptance schema")
    if app_version is not None and str(report.get("app_version", "")) != str(app_version):
        issues.append("app version mismatch")
    if exe_sha256 is not None and str(report.get("exe_sha256", "")).lower() != str(exe_sha256).lower():
        issues.append("EXE SHA-256 mismatch")
    if require_windows and str(report.get("platform", "")).lower() != "windows":
        issues.append("acceptance was not performed on Windows")

    automated = report.get("automated", {})
    if not isinstance(automated, Mapping):
        automated = {}
    for gate in REQUIRED_AUTOMATED_GATES:
        if _status(automated.get(gate)) != "pass":
            issues.append(f"automated gate not passed: {gate}")

    readers = report.get("screen_readers", {})
    if not isinstance(readers, Mapping):
        readers = {}
    required_check_keys = {check.key for check in MANUAL_CHECKS if check.required}
    for reader in REQUIRED_SCREEN_READERS:
        block = readers.get(reader, {})
        if not isinstance(block, Mapping):
            issues.append(f"screen reader not tested: {reader}")
            continue
        checks = block.get("checks", {})
        if not isinstance(checks, Mapping):
            checks = {}
        for key in sorted(required_check_keys):
            if _status(checks.get(key)) != "pass":
                issues.append(f"{reader} check not passed: {key}")
    return issues


def acceptance_complete(report: Mapping[str, Any], **kwargs: Any) -> bool:
    return not acceptance_issues(report, **kwargs)




def summarize_focus_trace(path: str | Path) -> dict[str, Any]:
    """Summarize privacy-minimized JSONL focus diagnostics without Qt imports."""
    source = Path(path)
    summary: dict[str, Any] = {
        "focus_events": 0,
        "unique_ids": 0,
        "lost_focus": 0,
        "anonymous_destinations": 0,
        "disabled_destinations": 0,
        "hidden_destinations": 0,
        "rapid_oscillation_windows": 0,
        "parse_errors": 0,
    }
    ids: set[str] = set()
    recent: list[str] = []
    if not source.exists():
        summary["missing"] = True
        return summary
    for raw in source.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(raw)
        except Exception:
            summary["parse_errors"] += 1
            continue
        if not isinstance(row, dict) or row.get("event") != "focus_changed":
            continue
        summary["focus_events"] += 1
        new = row.get("new")
        if not isinstance(new, dict):
            summary["lost_focus"] += 1
            recent.append("<none>")
        else:
            ident = str(new.get("id", "") or "").strip()
            token = ident or f"<{new.get('class', 'anonymous')}>"
            if ident:
                ids.add(ident)
            else:
                summary["anonymous_destinations"] += 1
            if new.get("enabled") is False:
                summary["disabled_destinations"] += 1
            if new.get("visible") is False:
                summary["hidden_destinations"] += 1
            recent.append(token)
        if len(recent) > 8:
            recent.pop(0)
        # Detect a sustained two-widget ABABAB pattern.  This is diagnostic only;
        # manual NVDA/JAWS focus-stress remains a release-signoff gate.
        if len(recent) >= 6:
            tail = recent[-6:]
            if tail[0] == tail[2] == tail[4] and tail[1] == tail[3] == tail[5] and tail[0] != tail[1]:
                summary["rapid_oscillation_windows"] += 1
    summary["unique_ids"] = len(ids)
    summary["missing"] = False
    return summary


def load_report(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Acceptance report root must be an object")
    return data


def save_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)
    return target


__all__ = [
    "ACCEPTANCE_SCHEMA",
    "REQUIRED_AUTOMATED_GATES",
    "REQUIRED_SCREEN_READERS",
    "MANUAL_CHECKS",
    "ManualCheck",
    "sha256_file",
    "acceptance_issues",
    "acceptance_complete",
    "summarize_focus_trace",
    "load_report",
    "save_report",
]
