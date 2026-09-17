# AudioKnigi Downloader 4.12.15 — Full Book Flow Logging

This release makes `app.log` sufficient to reconstruct both successful and failed audiobook processing without flooding the visible UI log.

## Structured lifecycle

Major INFO-level events include:

- `analysis_start` / `analysis_complete`
- `narration_selected`
- `download_start` / `download_plan`
- `source_download_start` / `source_downloads_complete` / `source_reused`
- `media_url_expired` / `playlist_refresh_start` / `playlist_refresh_complete`
- `ffmpeg_split_start` / `ffmpeg_split_complete`
- `verify_start` / `verify_complete`
- `cover_state`
- `id3_start` / `id3_complete` / `id3_skipped`
- `m4b_start` / `m4b_complete`
- `sidecars_saved` / `sidecars_skipped`
- `source_cleanup`
- `history_saved`
- `download_complete`

Per-track FFmpeg, verification and ID3 success events are DEBUG-level. All records still pass through the existing privacy formatter, so URLs and the user's home path are sanitized.

## Error diagnostics

The main download worker and full-MP3 worker now use traceback logging on failure, including title, narrator and selected-part context. Existing FFmpeg failure diagnostics remain unchanged and include return code, sanitized command and stderr.

## Regression coverage

`tests/test_full_book_flow_logging_41215.py` verifies lifecycle sequencing, structured context, history persistence logging and narration-selection logging.
