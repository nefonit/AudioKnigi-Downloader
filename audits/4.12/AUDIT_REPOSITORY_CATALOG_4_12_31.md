# Repository catalog audit — 4.12.31

**Дата:** 2026-09-05

## Цель

Убрать накопившиеся отчёты и технические заметки из корня проекта, не менять рабочую структуру Python-пакета и не создавать риск для импортов/сборки.

## Новая структура

```text
project/
├── README.md
├── CHANGELOG.md
├── THIRD_PARTY_NOTICES.md
├── audioknigi_gui.py
├── pyproject.toml
├── requirements.txt
├── build_ci.ps1
├── build_exe.bat
├── build_exe_fixed.bat
├── hook-prism.py
├── hook-tkinterdnd2.py
├── make_source_release.py
├── audioknigi/              # рабочий Python-код
├── assets/                  # иконки и ресурсы
├── tests/                   # regression/unit/UI тесты
├── audits/                  # все отчёты аудита
│   ├── INDEX.md
│   ├── 4.7/
│   ├── 4.8/
│   ├── 4.9/
│   └── 4.12/
└── docs/                    # техническая документация
    ├── INDEX.md
    ├── accessibility/
    ├── audio/
    ├── build/
    ├── features/
    ├── reliability/
    ├── sources/
    └── ui/
```

## Что намеренно не переносилось

- `audioknigi/` — изменение пути пакета потребовало бы массовой правки импортов;
- `tests/` — тесты должны оставаться стандартно обнаруживаемыми pytest;
- `assets/` — рабочие пути ресурсов уже стабильны;
- build scripts/hooks — оставлены в корне, потому что это точки входа сборки;
- `README.md`, `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md` — корневые документы проекта.

## Аудиты

Все корневые Markdown-файлы, являвшиеся отчётами аудита (`AUDIT*.md`, `*_AUDIT_*.md`), перенесены в `audits/` и распределены по веткам версий. Тесты вида `tests/test_audit_*.py` не переносились: это код тестирования, а не документы.

## Документация

Документы распределены по назначению, а не только по номеру версии. Для функциональных заметок дополнительно сохранено деление по веткам версий внутри `docs/features/`.

## Навигация

- `audits/INDEX.md` — каталог аудитов;
- `docs/INDEX.md` — каталог технической документации;
- `README.md` — обзор проекта и ссылка на оба каталога.

## Совместимость

Текстовые ссылки на перемещённые документы заменены на новые проектные пути. `tests/test_architecture.py` обновлён для `docs/build/RELEASE_SETUP.md`.

## Пост-каталогизационная проверка

- Python compileall: успешно.
- Полный regression-набор после перемещения документов и добавления catalog regression-тестов: **445/445 прошли**.
- Старый `PytestCollectionWarning` в `tests/test_range.py` устранён переименованием вспомогательного `TestDownloader` в `RangeDownloaderHarness`; отдельный range/resume smoketest проходит.
- В корне осталось только три Markdown-документа: `README.md`, `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md`.
- Audit Markdown вне `audits/`: **0**.
