# AudioKnigi Downloader 4.12.42 — Round 20 audit follow-up (2026-09-17)

Base: Round 19.

## Confirmed fixes

- Knigavuhe `BookController.enter(...)` argument extraction now decrements nested round-parenthesis depth regardless of surrounding `{}`/`[]`, so function calls or grouping expressions inside the JS object no longer swallow the outer call terminator.
- `fmt_eta()` accepts numeric float strings such as `"120.5"`; `parse_time_seconds()` rejects `NaN`/`Infinity` and overflowed clock totals instead of allowing non-finite values to reach time formatting/FFmpeg logic.
- PoleKnig search grouping now falls back to URL identity unless both logical title and author keys are non-empty, preventing unrelated punctuation-only titles by the same author from being merged as narration variants.
- PoleKnig external playlist discovery now scans script object properties for public `.json`/`.txt` playlist/file URLs when `new Playerjs(...)` receives a config variable, avoiding unnecessary Playwright fallback when the playlist is already present in HTML.
- Partial chapter downloads now write `metadata.json`, `book_info.txt` and NFO chapter metadata from the full `book.tracks` list, keeping duplicate-preflight metadata stable across partial repair/download sessions.
- Parallel multi-source downloads no longer let several source-local progress percentages overwrite the one global progress bar. Per-worker transfer UI is suppressed during the parallel source phase; visible progress advances monotonically by completed source count while network metrics continue to be recorded.
- `ProbeMixin._track_filename()` accepts Mapping/dict-style legacy track data as well as Track objects.
- Dynamic labels `Озвучка N` now have a runtime-regex translation for DE/EN/UK.
- Audioknigi search decodes `response.content` as UTF-8 first, matching the analysis path and avoiding Requests' possible ISO-8859-1 fallback/mojibake when a charset header is missing.
- Legacy queue `selected_indices` strings such as `"1, 2; 3 4"` are split on comma/semicolon/whitespace; an explicit empty list remains distinct from `None` and still means “nothing selected”.
- `history_listen()` switches to Advanced mode before selecting the Player tab, so programmatic History → Listen calls cannot leave the player hidden behind the Easy-mode stack.

## Reviewed but not changed

- `{Track_Title}` fallback to the book title is an existing explicit compatibility contract. Current tests deliberately reject `01 - 01.mp3` for an unnamed track; changing it would alter user filenames and historical behavior, so the audit suggestion was not applied.
- Range support with `Content-Range: bytes 0-0/*` safely falls back to ordinary single-stream download because the total size is unknown; segmented scheduling requires a concrete final byte count.
- The full-MP3 copy path does not relabel arbitrary codecs as MP3: `_effective_mp3_profile()` only chooses stream-copy for an MP3 source when the target is the MP3 output path.
- `_PROXY_ATEXIT_REGISTERED` intentionally registers process-exit cleanup once; restarting the proxy inside the same process does not require duplicate `atexit.register()` calls.
- The external-player `playlist_response is None` guard remains for historical mock compatibility; Requests itself does not normally return `None`.
- Hidden compatibility buttons remain non-focusable placeholders for accessibility/source contracts; the visible download menu is the user-facing control.
- Event-sound shutdown already uses a daemon worker, queue sentinel and bounded join, so no unbounded process-exit deadlock was demonstrated.
- `winId()` eager native-handle creation is a startup nuance, not a reproduced functional failure.
- Runtime regex is evaluated before runtime prefixes, so the duplicated skipped-parts translation does not create a race; wording cleanup can be handled separately without runtime risk.

## Verification

- Focused Round 20 regressions: 10/10 passed.
- Full pytest: 370/370 passed.
- Historical regression audit: PASS — 268 passed, 115 known source-shape incompatibilities, 0 newly unresolved failures.
- Exception audit: PASS — 109 reviewed broad exception passes.
- Undefined global audit: OK — 77 modules.
- Unused import audit: OK — 32 implementation modules.
- Qt localization audit: OK — ru/uk/de/en, help topics complete, onboarding complete, accessible names translated.
- Full parity: PASS — 61/61.
- Qt import audit: OK — 73 project modules reachable, no legacy frontend path.

Windows/PySide6/PyInstaller frozen build was not executed in this Linux environment.
