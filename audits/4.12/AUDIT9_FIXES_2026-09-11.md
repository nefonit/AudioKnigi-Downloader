# Audit 9 fixes — 2026-09-11

Base: `AudioKnigi_Downloader_v4_12_31_PHASE39_AUDIT8_FIXED_20260911`.

## Applied

- Replaced the duplicated/contradictory README with current Qt-only startup, build, accessibility, network, and architecture instructions.
- Normalized CHANGELOG structure (one `# Changelog`, one `4.9.3`) and removed late duplicate migration inserts; detailed migration history remains in `docs/migration/` and `audits/`.
- Removed retired `tk-uia` from third-party notices and marked `PHASE13_QT_ONLY.txt` as historical evidence.
- Updated `audioknigi_qt.py` Phase 19 / “Qt migration” user-facing leftovers to the current Phase 39 Qt-only state.
- `_clear_stale_source_downloads()` resolves the book folder with `create=False` and exits when it does not exist.
- `_measure_loudnorm()` now validates FFmpeg itself and raises the same controlled user-facing error expected by the rest of the downloader.
- `persist_browser_session()` distinguishes an explicit empty cookie snapshot from “cookies not supplied” and clears persisted cookies accordingly.
- `_read_http_head()` has a total deadline, preventing a byte-at-a-time local proxy client from keeping a handler alive indefinitely.
- `MappingDataclass.to_dict()` is safe when called on the non-dataclass base; iterator naming no longer shadows `dataclasses.field`.
- Removed the unused `ui_text` import from `templates.py`.
- Removed obsolete pre-context translations of bare `нет`; file status remains `нет (файл)`, while bare `нет` remains the logical No. Renamed the premature `_PHASE40_LITERAL_TRANSLATIONS` symbol to a Phase 39 accessibility block.
- PoleKnig variant discovery accepts harmless normalized title prefix/suffix additions before detail hydration, while detailed title + author checks remain mandatory.
- Track/Search context menus select the row under the right-click pointer before resolving the selected object.
- Removed stale “both desktop frontends / phase 1” service docstrings and de-duplicated player language lookup.
- Added `tests/test_audit9_followup_20260911.py`.

## Already fixed in the input archive

- `AccessibilityFocusTracer._write()` already catches `OSError`/`ValueError` and cannot crash the UI on a logging I/O failure.
- `QtEventSoundManager.play()` already assigns the newly created `(player, output)` pair to the local `pair` variable, and pending media callbacks are disconnected during retirement/stop.
- Track status localization already routes `local_status == "нет"` through `нет (файл)`.
- Accessibility has an import fallback for `QAccessibleAnnouncementEvent` and the supported dependency floor is PySide6 6.8+.
- The application font baseline is already stored as a Python `QFont` copy, avoiding cumulative scaling.

## Not changed intentionally

- `--playwright-edge-selftest` remains a Windows/Edge acceptance test. It is not a generic cross-platform CI browser test; README now says so explicitly.
- Source-mode `_report_path()` still returns no default file unless the report environment variable is set. This is intentional developer behavior, not a runtime failure.
- `core.APP_VERSION` remains a compatibility alias to the single source of truth in `version.py`; removing the alias has no runtime benefit.
- Full-MP3 `copy_mode` still produces one result file even when `delete_source=False`, because source and result are byte-identical in copy mode; duplicating the file would waste disk space.
- Knigavuhe `_query_matches_metadata()` is retained as a compatibility helper because multiple historical regression tests import it directly, even though production ranking no longer depends on it.
- Search/track model creation order is currently deterministic (`_build_search_tab()` and `_build_book_tab()` run before `_build_easy_page()`). Moving model ownership is an architectural refactor, not required to fix a runtime defect in this release.
