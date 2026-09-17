# Audit — Qt Migration Phase 13 Qt-only retirement

Дата: 2026-09-06  
Версия: 4.12.31  
Stage: `phase-13`

## Решение

Старый Tk frontend удалён из Phase 13 release tree **только после полного сравнения функций**.

## Доказательства до удаления

- Full capability inventory: **61/61 PASS**.
- Полный pytest regression: **613/613 PASS**.
- Phase 1–13 migration regression: **101/101 PASS** на основном этапе проверки.
- Найденные в Phase 13 accessibility-регрессии были исправлены до retirement: deterministic first search row focus, Enter/Return search activation, F1 accessibility/help surface, queue/history accessible row text.

## Retirement

Удалены runtime/launcher/build поверхности старой версии и пять дополнительных недостижимых из Qt legacy-support модулей. Общий backend, реально достижимый из `audioknigi_qt.py`, оставлен.

Старый regression suite сохранён как reference evidence: `archive/tests/pre_qt_retirement/`. Это тестовый архив, а не исполняемый Tk runtime.

## Доказательства после удаления

- Strict audit with `--require-legacy-retired`: **61/61 PASS**.
- Legacy runtime paths present: **0**.
- Qt import audit: **39 reachable project modules / 0 legacy frontend paths**.
- Qt-only active release tests: **5/5 PASS**.
- `compileall`: **PASS**.
- Standard installation dependencies: Qt/common only; no ttkbootstrap/pygame/pystray/tkinterdnd2/Prism/tk-uia.
- Default `run.bat`: Qt only; no `audioknigi_gui.py` or legacy EXE fallback.

## Ограничение среды

Linux CI/container не может подтвердить фактическое чтение конкретными Windows NVDA/JAWS builds или собрать/запустить Windows EXE. Поэтому Windows acceptance scripts сохранены и обязательны для финального EXE sign-off.
