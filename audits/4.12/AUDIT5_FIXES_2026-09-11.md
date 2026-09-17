# Audit 5 follow-up fixes — 2026-09-11

This pass was applied to the Phase 39 Qt-only source after AUDIT4.

## Fixed

- Full MP3 naming: when templates are enabled but the default per-track template is still `{Track_Number}.mp3`, the one-file download now uses the book title instead of `01.mp3`.
- Full MP3 retained sources: when transcoding succeeds and `delete_source=False`, the downloaded source is renamed to a visible/playable `Book (исходник).ext` file instead of remaining as hidden `.full-source`.
- Full MP3 preflight disk space: known transcoding/normalization modes reserve peak room for both the source and output before the download starts; the existing post-download exact check remains in place.
- HTTP 416 recovery accepts common/non-standard total forms such as `bytes */N`, `bytes 0-(N-1)/N`, and `/N` before deciding whether a `.part` is already complete.
- Loudnorm complex-filter measurement normalizes `map_label` to FFmpeg bracket notation, so both `a0` and `[a0]` are safe inputs.
- Qt download workers now deep-copy the request before entering the background thread, isolating worker-side fallback mutations from GUI/queue-owned request objects. Updated requests still return explicitly through signals/results.
- Runtime localization now matches the current audioknigi short-source/timeline fallback message and the skipped-unavailable-parts completion status.
- System-tray notifications for completed download, user decision required, and continued tray operation are now translated through the runtime localization layer.
- Knigavuhe search cards can capture author/reader text from semantic containers and `/author(s)/`, `/reader(s)/`, `/narrator/` links that follow icon elements.
- Knigavuhe narration-variant section detection now considers the full current ancestor stack, so nested `<span>` text inside structural headings/containers is recognized.
- Knigavuhe legacy script fallback accepts em-dash/en-dash/hyphen before `автор`.
- Cloudflare DoH follows CNAME-only answers recursively with loop protection and TTL combination instead of treating an alias-only answer as an empty A/AAAA result.
- Audiobookshelf library discovery reports a clear error when an HTTP 200 response is HTML/non-JSON (reverse proxy/login page) instead of exposing a raw JSON decoder exception.
- Accessibility announcement import is defensive even though the declared runtime is already `PySide6>=6.8`.
- Player metadata labels (`Автор`, `Чтец`, `Аудиокнига`, local chapter count) are localized.
- Duration probing pool cancellation now cancels queued futures and uses `shutdown(wait=False, cancel_futures=True)` on exit.
- Corrupt queue narration variants without a required `url` field deserialize safely with an empty URL.

## Reviewed but intentionally not changed

- Track status localization collision: the current `TrackTableModel` already maps raw local status `нет` through the context-specific `нет (файл)` key, so the UI displays Missing/Fehlt/Немає correctly.
- `QPlainTextEdit`/`QTextEdit` custom context menu: the existing implementation deliberately maps menu coordinates through `viewport()` for scroll-area editors. Without a failing Qt interaction test, changing the signal owner to the viewport would risk duplicate/broken menu handling.
- Last compact PoleKnig chapter duration: there is no trustworthy end timestamp in the compact playlist itself. Leaving `end/duration=None` lets downstream probing or end-of-file splitting determine the real tail instead of inventing a duration.
- Author initials vs full names in `_person_key`: aggressive fuzzy equivalence can merge different people; no change was made without a stronger identity source.
- Double focus-trace argument cleanup is redundant but harmless and preserves the useful guarantee that `create_application()` is safe when called directly.
- Localized `Без автора` in template paths is a product tradeoff. Replacing it with a language-independent sentinel would avoid language-dependent folder names but regress localized user templates; no silent behavior change was made in this audit.
- `QAccessibleAnnouncementEvent` compatibility below Qt 6.6 is outside the declared `PySide6>=6.8` support floor, but a defensive import was still added at negligible cost.
- The reported physical `text/x-python` filenames do not exist in the archive; `audioknigi/services/search_service.py` and other modules retain their correct package filenames.

## Regression coverage added

`tests/test_audit5_followup_20260911.py` covers Full MP3 naming/source retention, HTTP 416 Content-Range variants, loudnorm label normalization, Knigavuhe card/variant/dash parsing, Audiobookshelf non-JSON responses, damaged queue variants, current runtime/player translations, DoH CNAME following, and source-level Qt/pool hardening contracts.

## Validation

- `python -m pytest -q`: 335 passed
- Full Parity Audit: PASS 61/61
- Qt Localization Audit: OK for ru/uk/de/en
- Qt Import Audit: OK, 46 project modules reachable and no legacy frontend path
- `python -m compileall -q audioknigi tests`: PASS
- `qt/main_window.py`: 3997 lines
