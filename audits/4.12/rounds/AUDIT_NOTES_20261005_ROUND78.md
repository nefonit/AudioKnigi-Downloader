# Round 78 — external audit follow-up

Applied confirmed findings from the 2026-10-05 review:

- playlist refresh now preserves valid track index `0` in fresh/selected/old mappings, and missing-source collection no longer relies on raw `int(...)` conversion;
- sidecar metadata preserves index `0`, and `book_info.txt` renders unknown timeline boundaries as `—` instead of calling `fmt_time(None)`;
- legacy `AppSettings` reads now mirror the Round 76 write aliases: `auto_chunk_min_kbps` reads the canonical KB/s value and `normalize_audio` exposes a derived boolean from `normalization_mode`;
- automatic KnigaVuhe fallback no longer returns an unknown-narrator candidate after an explicitly conflicting narrator was observed; the same rule is applied in both downloader source analysis and `BookAnalysisService`;
- whitespace-only track titles now fall back to unique `track-XX` names instead of collapsing to the same sanitized filename;
- the KnigaVuhe narration parser accepts an exact visible `Другие озвучки` heading even when it is wrapped in generic markup;
- German help formatting recognizes `Strg`, `Umschalt` and `Leertaste` keyboard notation;
- runtime localization now covers the user-facing shared-source and split failures identified in `book_flow.py`, and Ukrainian `аудіофайлу` wording is consistent;
- the speed graph reserves its text area from the actual font metrics instead of fixed 13-pixel placement.

Reviewed and intentionally unchanged:

- `safe_name()` replaces forbidden filename characters with safe underscores and falls back to `audiobook` when sanitization becomes blank, so non-template book folders and `book_number` filenames cannot collapse to an empty title;
- support-bundle POSIX redaction does not match the slash inside `application/json` or `image/jpeg`; those MIME examples remain unchanged, while standalone `/secret`-style absolute paths stay privacy-redacted;
- `runtime_exact.json` templates such as `Найдено вариантов озвучки: {count}...` and `Озвучка {index}` are intentionally resolved by `ui_text()` before `.format(**kwargs)` and are covered by existing tests; they are not dead runtime-exact entries;
- runtime regex rules are evaluated before prefix rules, as already enforced by regression tests;
- `download_request.py` correctly imports the real `audioknigi.config.settings` package;
- `source_health_service.py` intentionally sets `trust_env = False`, matching `core.build_http_session()` and the application's Cloudflare/DoH proxy-isolation policy;
- the reported KnigaVuhe `groups[key]` crash is stale: Round 77 already uses `grouped[key]` in both duplicate checks;
- the native Windows media-key filter is already shut down and removed from `QApplication` in the normal close path;
- the settings-folder button safely connects directly because `_choose_output_dir(self, _checked=False, *, target=None)` explicitly consumes Qt's `checked` argument;
- event-sound slider values are already normalized with `percent / 100.0` before calling `QtEventSoundManager.configure()`;
- search-table source visibility is a product/UX choice distinct from the technical track-table source column, so no behavior was changed;
- `parts` versus `selected`, locale-catalog deduplication and the redundant author-prefix parse are broader cleanup/migration items rather than correctness defects for this hardening round.
