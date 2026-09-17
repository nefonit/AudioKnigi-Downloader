# Test catalog

`tests/` остаётся единым pytest-каталогом, чтобы не менять discovery/import semantics. Каталогизация выполняется через соглашения имён, а не физическое дробление тестов по подпапкам.

## Основные группы

- `test_accessibility*`, `test_screenreader*`, `test_full_screen_reader*` — доступность и NVDA/JAWS;
- `test_screenreader_editor_layout_focus_41231.py` — Windows UIA для редактора, Insert+Up fallback, раскладко-независимые Ctrl+L/D/F/Q/H, фокус и речевой анонс результатов поиска, frozen tk-uia packaging;
- `test_screenreader_all_elements_recursion_41231.py` — low-level Windows Insert+Up observer, подсказки всех control roles, narration Combobox open/close/navigation, runtime-инвентаризация Easy/Advanced/Help и Tcl/Tk-free recursion emergency path;
- `test_cloudflare_dns_accessibility_diagnostics_41231.py` — расширенные NVDA/JAWS редакторы/диагностика, подтверждение фокуса поиска, строгий Cloudflare DoH и proxy-маршрутизация Playwright/remote FFprobe;
- `test_compact_exe_build_41231.py` — system Microsoft Edge вместо встроенного Playwright Chromium, очистка `.local-browsers`, сокращённый PyInstaller collect-набор и frozen Edge self-test;
- `test_audioknigi_shared_source_recovery_41231.py` — проверка shared-MP3 timeline, packet-scan против ложной полной VBR/Xing-длительности, автоматический fallback `audioknigi.com.ua → knigavuhe.org` как до скачивания, так и внутри текущей загрузки, и безопасный pre-split guard от обрезанных глав;
- `test_theme*`, `test_ttkbootstrap*`, `test_visual_ui*`, `test_modern_accessible_ui*` — темы и UI;
- `test_modal_ownership_41231.py` — модальность и владение диалогами;
- `test_deep_audit_hardening_41231.py` — конкурентность операций, stale-result/cover protection, shutdown, subprocess/persistence, import-time hardening, source-cleanup и i18n placeholder validation;
- `test_event_bus*`, `test_threading.py`, `test_shutdown*` — потоки/event bus/shutdown;
- `test_knigavuhe*`, `test_poleknig*`, `test_search*` — источники и поиск;
- `test_audio*`, `test_event_sounds*` — аудио и звуки событий;
- `test_ffmpeg*`, `test_frozen_prism*`, `test_prism_cffi*` — сборка/frozen dependencies;
- `test_queue*`, `test_duplicate*`, `test_range.py` — загрузка/очередь/докачка;
- `test_audit_*` — regression-код, созданный по историческим аудитам. Это не audit-документы и поэтому они остаются в `tests/`.

- `test_qt_migration_phase10_41231.py` — hash-bound Qt release-candidate contract, passive focus tracing, Windows NVDA/JAWS acceptance runner and status gate;

## Примечание по `test_range.py`

Вспомогательный класс назван `RangeDownloaderHarness`, чтобы pytest не пытался собирать его как test class и не создавал `PytestCollectionWarning`.
