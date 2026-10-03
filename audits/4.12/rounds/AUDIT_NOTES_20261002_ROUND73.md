# Round 73 — Round 72 audit follow-up

Applied confirmed findings from the 2026-10-02 review:

- `AppSettings.replace_all()` now mirrors direct-constructor semantics for partial mappings and does not accidentally mark an omitted `first_run_complete` as completed;
- shared-source timeline validation falls back to remote duration probing when a provided `local_map` does not contain a particular source;
- `_split_track()` uses `unlink_with_retry()` before FFmpeg overwrite, so transient Windows file locks are retried instead of silently ignored;
- duplicate `.common` imports in `book_flow.py` were consolidated;
- backup validation restores all history rows instead of truncating an archive to 500 entries;
- AudioKnigi shared-source recovery now uses chapter `start` markers as a lower-bound timeline when `end` markers are absent;
- the parallel-source search progress line has EN/DE/UK runtime localization;
- persisted queue booleans parse textual `false/0/off` and `true/1/on` values semantically;
- generated chapter numbers scale to the total part count (`001` for 100+ chapters);
- full-MP3 mode reuses a completed hidden `.full-source` after an interrupted processing/tagging stage, adjusts its initial disk-space requirement accordingly, and removes stale `TRCK` metadata from the final whole-book MP3;
- sidecar duplicate duration comparison uses the same adaptive 5–15 second tolerance as track verification;
- runtime exact translations are checked before regex patterns; two constant regex entries were moved into `runtime_exact.json`;
- Knigavuhe title validation accepts Unicode letters such as `Ґ/ґ` and `Ў/ў` instead of relying on a hand-written Cyrillic subset;
- Easy mode recognizes supported schemeless URLs consistently and reset clears the pending post-analysis download-focus flag;
- player file loading now has a single status/announcement path, avoiding duplicate NVDA/JAWS speech;
- the download options button relies on Qt's native menu indicator instead of rendering a second text arrow;
- batch URL queue import continues with the next URL after one analysis error while explicit Cancel still cancels the whole batch;
- one-track context download keeps its temporary selection visible until the worker finishes, then restores the previous selection without overwriting the completion status announcement;
- missing-media decision boxes call `deleteLater()` after the modal loop;
- history reload only auto-sizes service columns and preserves the intended Title/Author/Narrator widths;
- extended Help Center guidance is now available in RU/EN/DE/UK, German help wording was normalized to polite `Sie`, German media terminology was normalized to `Playlist`, and the Ukrainian connection-resume translation uses the standard typographic apostrophe.

Reviewed and intentionally unchanged:

- Windows directory-like path masking in support bundles remains privacy-first. A whitespace-delimited diagnostic tail can be indistinguishable from a private folder name, so over-redaction is preferred to leaking path fragments; the misleading comment was corrected and a regression documents the contract;
- the literal `Озвучка {index}` exact translation remains valid because `ui_text()` formats that template before display, while already-rendered runtime strings such as `Озвучка 3` continue to use the regex translation;
- `source_health_service` and the main HTTP session intentionally use `trust_env=False` so health probes and normal requests share the same proxy-isolation policy.
