# AudioKnigi Downloader 4.12.42 — Round 86 audit follow-up

Date: 2026-10-10

## Confirmed fixes

- `services/library_service.py`: hold `HISTORY_LOCK` across the complete history snapshot → restore → rollback transaction so a concurrent download completion cannot write between those phases.
- `services/book_analysis_service.py`: always reap/communicate remote-duration `ffprobe` processes during cancellation, including processes already killed by the shared cancellation coordinator.
- `providers/audioknigi_search.py`: add an explicit CP1251/Windows-1251 fallback for legacy Cyrillic pages, and accept explicit comma/semicolon-separated one-word coauthor names without weakening ordinary dashed-title detection.
- `services/source_health_service.py`: HTTP 401 and 451 now count as reachable-but-blocked responses, consistent with 403/429/503 diagnostics.
- `download/network.py`: active subprocess cancellation now claims/removes the shared snapshot under lock before killing, preventing parallel cancel checks from racing over the same `Popen` handles.
- `qt/main_window.py`: Easy-mode operation state now treats a running download queue as active, so editing the search field cannot reset the visible state of an active queued task.
- `qt/event_sounds.py`: shutdown drains/balances a sentinel that may remain when the worker exits after observing the shutdown event before consuming it.
- `qt/accessibility.py`: reduce non-assertive exact-duplicate suppression from 800 ms to 250 ms while retaining the 60 ms flood guard, improving rapid keyboard/screen-reader navigation feedback.
- `qt/help_center.py`: recognize the Russian key name `Пробел` in shortcut markup.
- `qt/localized_context_menu.py`: clamp keyboard-invoked text-editor context-menu placement to the visible viewport.
- `qt/application.py`: resolve and store an explicit immutable base-font size before applying UI scale, avoiding native-font baseline drift on repeated scaling.
- `qt/track_model.py`: emit explicit check/accessibility roles when a track selection changes so UI Automation receives a reliable state-change signal.
- `qt/mixins/queue.py`: restore the moved queue row once, under blocked intermediate selection signals, instead of selecting it twice and producing duplicate screen-reader announcements.
- `qt/mixins/analysis_download.py`: resolve the missing-media decision only after `QMessageBox.exec()` returns and the clicked button is known. The `finished` signal can no longer wake the worker with `stop` before a user's `Skip` choice is applied.
- `templates.py`: when a template already contains `{Track_Number}`, a blank `{Track_Title}` no longer expands to another synthetic `track-XX` number.
- `qt/speed_graph.py`: clamp graph geometry/y positions for very small widget heights.
- `qt/main_window_pages.py`: Settings-page accessibility IDs are now stable language-independent identifiers and Book/Settings accessible names/descriptions are localized through the UI catalog.

## Reviewed findings that did not justify runtime changes

- Empty `book.tracks` continues to mean the queued request requires analysis. New requests are validated before enqueueing, so an empty deserialized track list is incomplete state rather than a runnable full-MP3 shortcut.
- `selected_indices=None` intentionally means all tracks while `[]` intentionally means no selected tracks. Treating a legacy/invalid empty list as all tracks could unexpectedly download an entire book.
- CSV formula protection remains limited to actual spreadsheet formula triggers; the reported `|`/`%` extension was not supported by a reproducible formula-injection case.
- PoleKnig Playwright callbacks, playlist final-duration handling, Knigavuhe JS parsing, DNS relay, thread-local HTTP sessions, Track type annotations, Audiobookshelf cancellation API, media-key pointer handling, local-file main-window drag/drop, and several other items are architectural/feature proposals or hypothetical edge cases without a confirmed current failure.
- Search cancellation emits one completion path per worker run; no duplicate-finished path was found.
- Track index `0` remains intentionally supported throughout the runtime contract.
- The player does not autoplay until resume application has completed; saving earlier could overwrite a valid stored position with zero.

## Regression coverage added

- whole-transaction history locking and explicit empty-selection queue semantics;
- CP1251 decoding and one-word author/coauthor parsing;
- blocked-but-reachable HTTP 401/451 and one-owner subprocess cancellation;
- externally killed remote-duration ffprobe reaping and blank-track-title template behavior;
- missing-media Skip decision ordering;
- stable/localized accessibility IDs and names, keyboard context-menu bounds, F1/help shortcut vocabulary, explicit model accessibility roles, shorter duplicate-announcement suppression, immutable UI-scale baseline, Easy-mode queue preservation, single queue-row focus restoration, balanced event-sound shutdown, and tiny speed-graph bounds.

## Validation baseline

- Total collected tests: **942**.
- Integration cases: **899**.
- Runnable tests in this environment: **940 / 940 passed**.
- The remaining **2** Qt accessibility self-tests fail only because PySide6 is not installed in the validation environment (`ModuleNotFoundError: PySide6`).
- Full Parity: **61 / 61 PASS**.
- Qt import/localization, exception, unused-import, undefined-global and historical-regression audits: **PASS**.
- `compileall`: **PASS**.
- Strict non-archive project JSON parse/duplicate-key check: **11 / 11 PASS**.
