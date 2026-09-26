# Audit notes — Round 34 (2026-09-19)

Round 34 validates the 2026-09-19 pasted audit against the current Round 33 source and fixes confirmed defects. The user-observed PoleKnig annotation problem is treated as the primary regression.

## Confirmed and fixed

- **PoleKnig annotation:** detail-page metadata no longer blindly uses SEO `description`/`og:description`. The parser now prefers visible description/annotation blocks, substantial synopsis paragraphs, then JSON-LD, and accepts meta description only when it does not look like SEO text such as “скачать/слушать аудиокнигу…”. If only SEO text exists, description remains empty instead of polluting the Easy-mode annotation block.
- **Standalone chapter truncation:** `_split_track()` no longer converts a rounded metadata duration into FFmpeg `-t` when both `start` and `end` are absent. One-file-per-chapter sources are processed to physical EOF; real shared-source slices still use explicit/inferred boundaries.
- **Windows segmented cancellation:** after active network I/O is closed, segmented worker threads get a bounded two-second join window so `.seg`/`.part` handles can close before cleanup. Lingering workers are logged rather than waited on indefinitely.
- **Full-MP3 retained-source extension:** copy/transcode branches now share one suffix resolver using the URL extension, probed container name, and codec. Extensionless MP4/M4A AAC sources retain `.m4a` rather than generic `.audio`.
- **Knigavuhe restricted metadata:** rights-restricted pages consistently return a metadata-only `Book(restricted=True)` even when no alternate narration exists. Download validation still refuses restricted books; no restriction bypass is introduced.
- **Knigavuhe JS parser:** `BookController.enter` must be followed only by whitespace and `(`. Assignments such as `BookController.enter = function(...)` can no longer make the parser scan ahead to an unrelated parenthesis.
- **Fallback recovery:** when a broken audioknigi shared source safely switches to Knigavuhe, the obsolete audioknigi `resume.json` is removed before `request.book` is replaced.
- **Settings booleans:** persisted booleans now normalize strings/numbers explicitly (`"false"`, `"0"`, `"off"`, etc. become `False`; true forms become `True`) rather than relying on Python truthiness.
- **Atomic cover writes:** cover sidecars use a temp file plus retrying atomic replace, matching the safety model already used for JSON/text sidecars.
- **Audioknigi title cleanup:** author prefixes are stripped when the independently parsed author contains the same person-name tokens in a different order/expanded form (for example `Лев Толстой` vs `Толстой Лев Николаевич`) without applying the heuristic to unrelated dashed book titles.
- **Search status:** a provider exception now reports `Ошибка источника …` instead of immediately reporting that the failed source was “processed”.
- **Queue drag/drop:** QAbstractItemView drop coordinates are treated as viewport-relative directly; the Round 33 extra `mapFrom()` offset was removed.
- **Player visibility:** opening a local file/folder from Easy mode switches to Advanced mode before activating the Player tab, so playback controls are visible.
- **Easy-mode stale book action:** free-text/new URL input no longer leaves the large Download button active for the previously analysed book; the older URL-specific stale flag semantics are retained for compatibility.
- **Queue retry-all:** tasks that still require analysis are not changed to `retry`, preventing permanently unrunnable “Ожидает повтор” rows.
- **Shutdown-safe search:** deferred search-result rendering returns immediately once deferred exit is requested, avoiding access to deleted Qt objects.
- **Keyboard track context menu:** Shift+F10 selects the first row when no chapter is current, so screen-reader users get an actionable menu instead of silent no-op.
- **Runtime localization:** dynamic fallback/source-refresh/skip/error messages were added to runtime regex translations; German dynamic `Озвучка N` now uses `Sprecherfassung N` consistently.
- **Help:** token documentation now reflects the Round 33 case-insensitive placeholder behavior.

## Reviewed and intentionally unchanged

- **PoleKnig short-title compatibility:** exact short titles already match; loosening prefix/suffix compatibility below six characters would create broad false positives for titles such as “Мы” or “Оно”. No unverified fuzzy relaxation was added.
- **`{Output_Dir}` folder token:** intentionally remains a relative-template placeholder resolved to empty inside `render_folder()`. Expanding it to the absolute root would duplicate the base output path; this behavior is covered by historical tests and prior audit notes.
- **PoleKnig `_clean_text` punctuation:** book titles use `_clean_title_text`; trimming presentation punctuation from person/metadata helper fields remains intentional.
- **DNS negative caching:** the bounded 30-second empty-address cache is normal negative caching and does not exceed the configured TTL.
- **JSON temp cleanup:** `save_json()` already performs best-effort temp removal; a locked temp file cannot be made reliably deletable while another Windows process owns the lock.
- **Narration-count localization:** the `{count}` entry is called through `ui_text(..., count=...)`, which resolves the exact template key before formatting. It is not a broken runtime-exact lookup in the current call path.
- **Queue cover Base64:** the potential large-queue performance issue is architectural. Replacing inline cover bytes with a persistent cache needs migration/cache-lifecycle work and was not mixed into this correctness round.
- **Audioknigi pagination/provider parallelism:** no verified current Audioknigi pagination contract was supplied, and parallelizing providers would change progress/error ordering; both remain separate performance/features work.
- **`Path("")` validation claim:** once converted to `Path`, an empty string is indistinguishable from an explicitly requested current directory (`Path(".")`). Settings construction already maps an empty configured output to `DEFAULT_OUTPUT`, so the service continues allowing an explicit `.` path.
- **Missing-media timeout dialog:** the current GUI already runs a 100 ms watcher that rejects the dialog whenever `prompt.event` becomes set, including the worker's 30-minute timeout.
- **First-run stereo preset and live scale:** these are policy/UX choices, not reproduced correctness regressions.

## Verification

- Round 34 focused regressions: **20 passed**.
- Current pytest suite excluding the historical wrapper: **482 passed, 0 failed**.
- Historical wrapper test: **1 passed**.
- Effective current pytest contract: **483 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=264`, `known_shape_incompatibilities=119`, `resolved=0`).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI/help/onboarding/accessibility complete).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- `compileall`: **PASS**.
