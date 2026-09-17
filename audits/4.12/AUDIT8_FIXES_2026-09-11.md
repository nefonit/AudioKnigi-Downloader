# AUDIT8 follow-up — 2026-09-11

Base: `PHASE39_AUDIT7_FIXED_20260911`.

## Confirmed and fixed

- `DownloadRequest` now distinguishes omitted template options from explicit values. `_DownloadEngine` inherits `use_templates`, `folder_template`, and `track_template` from persisted settings when the request omits them. Queue snapshots preserve that tri-state contract.
- `DownloaderMixin` headless defaults for `embed_tags` and `delete_source` now match application/engine defaults.
- `run_full_mp3()` recomputes the final target/temp source name after a refreshed playlist changes book metadata.
- Multi-source parallel download failure cancels pending futures and closes active network responses so the executor does not wait for unrelated downloads to finish.
- Cloudflare proxy shutdown only calls blocking `server.shutdown()` while its server thread is alive. Socket forwarding also aborts after 20 seconds without write progress.
- Knigavuhe and PoleKnig parsers assign contiguous user-facing track indices after malformed playlist entries are skipped. PoleKnig list/object/compact forms follow the same rule.
- `AccessibilityFocusTracer._write()` no longer lets diagnostic file I/O errors escape into Qt slots.
- Filesystem template placeholder for a missing author is stable (`Без автора`) across UI languages, preventing duplicate folders after a language change.
- When the original narrator is unknown, automatic Knigavuhe recovery refuses ambiguous candidates with different narrator identities instead of silently selecting one.
- Event-sound first-use cache state is consistent (`pair` is updated immediately).
- Player next/previous navigation resolves the current file inside the downloaded-file list instead of reusing the row index from a chapter list that may include missing chapters.
- Player file/folder dialogs tolerate hosts where `output_edit` has not been constructed.
- `segment_count=null` falls back to `auto` instead of the string `None`.
- QTextEdit/QPlainTextEdit delete-selection uses `insertText("")`, keeping native undo semantics.
- Easy-mode missing-cover text, paste-link sound parity, and history redownload advanced-mode switching are aligned.
- Search-service future iteration now raises typed `Cancelled` immediately, matching analysis/fetch contracts.
- Minor cleanup: dataclass field loop variable no longer shadows `dataclasses.field`.

## Audited but intentionally not changed

- **FFprobe `-read_intervals`:** the report proposed changing `START%+DURATION` to `START+DURATION`. That would be incorrect. In ffprobe interval syntax `%` separates the start expression from the end/duration expression; it is not a percentage operator. The existing `f"{start:.3f}%+{span:.3f}"` is retained and now covered by a regression test.
- **Track status `нет`:** the table already maps model status `нет` to the contextual key `нет (файл)`, so users receive `missing / fehlt / немає`; the generic `нет` remains available for Yes/No UI text.
- **Full-MP3 copy mode with `delete_source=False`:** when no transcoding occurs, the downloaded bytes *are* the final MP3. Keeping a second identical copy would only waste disk space, so the single-file behavior is retained.
- **Narration availability `None`:** the UI intentionally does not advertise an unverified narration as available. This is conservative and avoids false transitions.
- **Very short player-position suppression:** the existing three-second edge policy is intentional for audiobook resume behavior; no change was made.

## Regression coverage

Added `tests/test_audit8_followup_20260911.py` covering the corrected contracts and the ffprobe syntax guard.
