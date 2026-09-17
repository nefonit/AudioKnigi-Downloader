# 4.12.40 Stability and localization hardening

## Confirmed and fixed

- FFmpeg/loudnorm subprocesses no longer inherit application stdin; loudnorm also uses `-nostdin`.
- Parallel SSD split progress is emitted inside the completion lock, preventing out-of-order progress rollback.
- Runtime translation covers detailed `Скачано X из Y • speed • ETA`, duration-probe completion, playlist refresh and source-download stages.
- Legacy `Восстановить` now means Restore/Wiederherstellen, and English file status `есть` is aligned to `present`.
- Diagnostic secret redaction no longer masks unrelated settings that merely contain the substring `token`.
- Knigavuhe/PoleKnig provider `fetch_book()` now goes through the common analysis service so missing durations are enriched consistently.
- History writes/clears/downloader updates share one `HISTORY_LOCK`; backup members are snapshotted into memory with retry before ZIP creation.
- Non-HTTP cover schemes are rejected before network setup.
- Worker-thread accessibility announcements use the queued announcer reference instead of touching `QWidget.window()` outside the GUI thread.
- Player tab receives the symmetric Alt+6 shortcut; event-sound volume tooltip wiring is defensive.

## Reviewed but intentionally unchanged

- Partial-download disk estimation keeps the full `remote_size` when it is known because `BookAnalysisService` only records `remote_size` when all chapters share one source file; extracting even one missing chapter requires that shared source. Multi-file books have `remote_size == 0` and are not charged the whole-book size.
- `MappingDataclass.to_dict()` already exists and queue persistence explicitly serializes `Track`/`NarrationVariant` models; the reported “empty tracks” failure does not apply.
- `{Track_Title}` falling back to the book title is an established compatibility contract covered by archived regression tests, so it was not silently changed in this stability release.
- The hidden `.full-source` path remains for full-MP3 compatibility; ffprobe identifies the media by content and archived resume/repair contracts depend on the path shape.
- Downloader mixins always provide `ui()` through `DownloaderMixin`/`_DownloadEngine`; extra defensive `hasattr(self, "ui")` checks were added only around optional timing refresh hooks.
- Chrome 153 is a real Stable release in September 2026, so the current UA major is not a future/nonexistent browser.

## Verification

- Active pytest: 170 passed.
- Full parity: 61/61.
- Localization audit: OK for ru/uk/de/en.
- Qt import audit: 73 project modules, no legacy frontend path.
- Exception audit: 113 reviewed broad silent handlers.
- Unused-import audit: 32 implementation modules.
- Undefined-global audit: 77 modules.
- Historical regression: 273 passed, 0 unexpected regressions.
- `compileall`: OK.
