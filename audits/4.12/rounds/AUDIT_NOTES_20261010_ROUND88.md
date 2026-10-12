# Round 88 audit follow-up — 2026-10-10

## Confirmed fixes

1. **Queue optional booleans**
   - Unknown/corrupt persisted strings now deserialize as `None` (unspecified) instead of an explicit `False`.
   - Valid RU/UK/DE/EN true/false spellings remain supported.

2. **Backup restore rollback**
   - Rollback restores the exact pre-restore bytes rather than reparsing them as JSON.
   - Empty or already-corrupt pre-existing JSON is therefore restored byte-for-byte after a later restore failure.

3. **Qt event-sound media reset**
   - Cached cue playback no longer calls `QMediaPlayer.setPosition(0)` while the backend is still `NoMedia`/`LoadingMedia`.
   - Position reset is limited to loaded/buffered/end-of-media states.

4. **Qt session shutdown**
   - `run_qt()` tolerates a deleted Shiboken/C++ main-window wrapper while collecting final settings.
   - `session_state.json` can still be marked `running=false`.

5. **Bulk track accessibility**
   - `set_all_selected()` and `set_selected_indices()` emit explicit CheckState/AccessibleText/AccessibleDescription roles for Windows UIA/NVDA/JAWS.

6. **Queue accessible text**
   - Numeric zero is preserved (`Попытки: 0`) instead of being spoken as `нет`.

7. **Bounded close wait**
   - Final cooperative QThread wait now uses one shared 750 ms deadline rather than up to 750 ms per thread.

8. **Bounded error-log copy**
   - `tail_error_log()` reads only a bounded suffix of a large log before selecting the final lines, avoiding full-file GUI reads.

9. **Single-book runtime regex**
   - Removed the redundant `(1)` capture; the dynamic source count is now the sole capture and uses `{0}`.

## Reviewed findings intentionally left unchanged

- Segmented-download `controller.observe()` is already serialized by the `last_observe` decision under `progress_lock`; a second worker cannot claim the same observation window.
- The Range worker path does not call `jobs.join()`, preserves the first error, and checks `errors` before the incomplete-queue diagnostic.
- FFmpeg cleanup keeps unregister/pipe close outside the guarded kill/communicate block, so a failed `kill()` does not skip cleanup.
- `AppSettings.__setitem__` writes only the requested canonical key after one-key normalization; unknown keys are preserved.
- POSIX privacy redaction already has regression coverage for MIME types, HTTPS URLs, request paths and arithmetic text.
- `scan_unfinished()` treats `None`/`[]` as whole-book selection; the empty-list rejection is inside the explicit-selection branch only.
- DNS state/cache locks are not nested in the claimed AB-BA order.
- `_retained_full_source_path()` explicitly guarantees that a retained source never aliases the final target.
- KnigaVuhe variant `available=None` is not presented as an explicitly available alternative by the UI.
- `MappingDataclass` currently has no datetime/UUID model fields requiring extra conversion.
- Normal close persists player volume through lifecycle settings; immediate per-slider disk writes are intentionally avoided.
- Queue drop coordinates/reordering, short EndOfMedia handling, worker signal ordering and several cosmetic terminology suggestions were not changed without a reproducible defect.

## Regression coverage

New domain-based regression tests cover:
- unknown persisted booleans;
- exact raw rollback of an empty original file;
- bounded error-log tail reads;
- single-book regex capture contract;
- deleted-window session shutdown guard;
- event-sound LoadingMedia seek guard;
- bulk-selection accessibility roles;
- queue zero-value accessible text;
- shared close deadline.

No `test_round88_*.py` file was created.
