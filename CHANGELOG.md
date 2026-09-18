# Changelog

## 4.12.42 — Acceptance parser, cancellation and diagnostics hardening (2026-09-17)

- Round 24 audit (2026-09-18): added application-modal Easy-mode progress for search/analysis/download with cancellation, hardened missing-media decisions, expanded crash/traceback capture for worker threads, and corrected audioknigi.com.ua machine playlist titles such as `king_Rat_1`.
- Hardened Playwright playlist discovery, Knigavuhe JS-comment parsing, local proxy Unicode/select behavior, float-string chapter boundaries, support-bundle privacy/tails, localization, player activation/shutdown, dragged `.url` handling, root-library scans, and legacy normalization settings. Added 12 focused Round 24 regressions; full suite: 402 passed. All localization/static/historical gates green.

- Round 23 audit (2026-09-18): removed the GUI `os._exit(0)` emergency path that could make a stalled close attempt look like a spontaneous crash, restored active-operation close confirmation, and added lifecycle diagnostics. A timed-out close now aborts and restores the live application instead of killing the interpreter.

- Round 22 audit (2026-09-17): isolated Playwright cookie restoration per cookie on PoleKnig/audioknigi fallbacks, removed cancellation exceptions from the PoleKnig request event callback, and preserved full-duplex CONNECT traffic after an upstream half-close.
- Hardened Windows filenames against ASCII control characters, made duplicate-output track selection Mapping-aware, preserved meaningful edge punctuation in PoleKnig book titles, corrected source-cleanup telemetry, and removed two unreachable/redundant HTTP checks. Added 8 focused Round 22 regressions; full suite: 387 passed. Historical regression: 267 passed / 116 known source-shape incompatibilities; all release gates green.

- Round 21 audit (2026-09-17): made duplicate-output deletion, JSON atomic replacement, and all Range temporary-file cleanup retry short Windows sharing violations; rejected empty player-position paths before they can normalize to the process working directory.
- Aligned Knigavuhe script-fallback narration variants with the normal parser, made PoleKnig alternative-author matching tolerate initials/surname forms conservatively, and let explicitly directory-shaped missing support-bundle destinations receive timestamped ZIPs. Added 9 focused Round 21 regressions; full suite: 379 passed. Windows CI now installs pytest and FFmpeg before archived/full test gates and ignores Python 3.14's synthetic `__conditional_annotations__` symtable global. Historical regression remains 268/115 known source-shape incompatibilities; all release gates green.

- Round 20 audit (2026-09-17): fixed Knigavuhe nested-parenthesis argument extraction, float ETA/non-finite playlist time handling, PoleKnig symbol-only-title grouping, external playlist discovery from variable-based PlayerJS configs, and UTF-8 search decoding for audioknigi.com.ua.
- Preserved complete book sidecars after partial downloads, made ProbeMixin filename generation Mapping-safe, localized dynamic “Озвучка N” labels, accepted legacy comma/semicolon/space selected-index strings, exposed the player when History listening is invoked from Easy Mode, and stabilized multi-source parallel download progress so worker-local percentages cannot fight over the global progress bar. Added 10 focused Round 20 regressions; full suite: 370 passed. Historical regression remains 268/115 known source-shape incompatibilities; all release gates green.

- Round 19 audit (2026-09-17): aligned PoleKnig slash-slug URL validation/canonicalization, prevented cross-source chapter-duration inference, used Windows-safe retry for single-download final rename and source cleanup, and made duplicate metadata checks Mapping-safe.
- Improved Knigavuhe fallback narrator selection, Easy-mode stale detection after text search, localized player dialogs, F1 routing to the dedicated shortcuts help topic, and full-MP3 whole-book selection semantics. Added 8 focused Round 19 regressions; full suite: 360 passed. Historical regression: 268 passed / 115 known source-shape incompatibilities; all release gates green.

- Round 18 audit (2026-09-17): cleaned stale Range `.assembling` state on unsupported-Range fallback, made segmented final replace and full-MP3 source moves retry short Windows sharing violations, and made ordinary parallel duration probing poll cancellation every 100 ms while terminating active ffprobe children.
- Hardened state/search behavior: backup restore now rolls back already-written members on a later failure, failed history persistence is no longer logged as success, audioknigi initial matching only uses person-name initials, and deep JSON-LD traversal is iterative.
- Improved Windows/Qt accessibility behavior: event-sound players detach `QAudioOutput` before destruction, search rows expose a full `AccessibleDescriptionRole` summary, media-key registration detects HWND recreation, combo announcements never speak internal object names, Easy-mode saves preserve custom advanced audio settings, and explicit analysis Cancel stops the rest of a dropped-URL batch.
- Tightened support-bundle forward-slash UNC redaction so code/log text such as `// TODO` is not mistaken for a network path. Added 10 focused Round 18 regressions; full suite: 352 passed. Historical regression remains 269/114 known shape incompatibilities; exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates are green.
- Round 17 audit (2026-09-17): made UI-scale migration accept any `Mapping`/`AppSettings`, hardened malformed `runtime_regex.json` rows against import-time crashes, unified the no-search-source error with the localized UI catalog, and cleaned remaining PEP 8 import/assignment rough edges.
- Repaired the 4.12.42 changelog chronology by moving Round 8 Windows build hardening back between Rounds 9 and 7 and updating the release finalization date to 2026-09-17.
- Added 6 focused Round 17 regressions covering Mapping migration, raw/Track index compatibility, malformed runtime-regex catalogs, localized empty-source search behavior, formatting hygiene and changelog structure; full suite: 342 passed. Historical regression gate passes with 269 archived tests and 114 known source-shape incompatibilities; all other release gates are green.
- Round 16 help-center expansion (2026-09-17): replaced one-line/two-sentence Qt Help Center topics with a complete 16-topic built-in guide across RU/UK/DE/EN.
- Added dedicated guidance for the full download lifecycle: Simple/Advanced mode, book analysis and narration variants, search, selected parts/full-MP3/resume, quality/normalization, queue, history, player, settings, templates/files, backup/transfer, NVDA/JAWS, shortcuts, diagnostics and recovery.
- Documented important user-facing edge behavior such as case-sensitive template tokens, Range/`.part` recovery files, safe loudnorm fallback, one-MP3 queue semantics, player-position throttling and privacy-redacted support bundles.
- Updated the Help Center intro so it no longer describes the content as a short guide, while preserving the historical F1 accessibility-help contract and Shift+F1 contextual help.
- Added 4 focused Round 16 regressions; full suite: 336 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates all pass.
- Round 15 audit (2026-09-16): narrowed stale source cleanup to engine-owned artifacts, added bounded Windows `os.replace()` retries for atomic sidecars, made audio-info cache eviction defensive, and downgraded incomplete two-pass loudnorm measurements to a localized safe single-pass fallback.
- Hardened cancellation/recovery: duration-probe ffprobe children are registered and killed before executor shutdown, legacy queue entries recover base64 covers and `normalize_audio`, full-MP3 queue rows report one output file, and history deletion rebuilds accessibility row metadata.
- Made Range progress localization spacing-tolerant and clipboard self-copy suppression compare canonical supported URLs.
- Added 10 focused Round 15 regressions; full suite: 332 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates all pass.
- Round 14 audit (2026-09-16): migrated legacy `normalize_audio=true` to single-pass normalization, redacted embedded Windows/UNC paths in support bundles, made `.segNNN` discovery literal for bracketed names, and made same-source ffprobe single-flight retries iterative rather than recursive.
- Hardened PoleKnig/duplicate handling: circular-safe PlayerJS extraction, trust site-ranked search rows instead of strict all-token metadata filtering, and mapping-safe duplicate sidecar track fields.
- Preserved explicit chapter selections across narration switches, stopped chapter activation from stealing screen-reader focus, retired invalid cached event-sound players, and made global-hotkey unregister pointer-width safe.
- Removed duplicate unfinished-download scans after folder selection and duplicate Queue/History row announcements when `AccessibleDescriptionRole` already supplies the same screen-reader summary.
- Added 13 focused Round 14 regressions; full suite: 322 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates all pass.
- Round 13 audit (2026-09-16): preserved dotted support-bundle names/directories, case-insensitively masked geometry, expanded camelCase secret redaction, and included both display/status-code queue state in diagnostics summaries.
- Hardened media/runtime edges: Mapping-compatible `AppSettings` equality, string-safe ID3 indices, clock-string chapter boundaries, single-flight same-source ffprobe caching without serializing different sources, and throttled player seek persistence.
- Improved search/state safety: ignored generic “аудиокнига/слушать/онлайн” query noise, accepted abbreviated author initials when another token matches, limited HTTP-200 “just a moment” protection detection to the page title, reused persisted duration for resume-end checks, and made track-table indices tolerant of malformed legacy data.
- Added CSV formula-injection neutralization and runtime localization for dynamic `Скачивается X/Y` progress.
- Added 12 focused Round 13 regressions; full suite: 309 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates all pass.
- Round 12 audit (2026-09-16): terminate active peer FFmpeg processes when one parallel split fails, mask forward-slash UNC paths in support bundles, simplify byte-tail UTF-8 recovery, and accept namespace-qualified Schema.org Book/AudioBook/CreativeWork types.
- Added pre-request Knigavuhe cancellation, identity-encoded remote-size probes, collision-safe retained-source naming for whole-book outputs, Mapping-compatible download request typing, pending dropped-URL continuation after malformed analysis results, and supported-site validation for Windows `.url` shortcuts.
- Added 9 focused Round 12 regressions; full suite: 297 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates all pass.
- Round 11 audit (2026-09-16): stopped peer Range workers from retrying after another Range worker has already reported the root failure, and preserved already-downloaded fresh sources when the user skips one unavailable part after a playlist refresh.
- Hardened recovery and parsing: malformed scalar `selected_indices` in `resume.json` no longer crashes unfinished-download scanning, playlist chapter titles decode HTML entities, JSON-LD is parsed before entity decoding, and malformed `.url` drag/drop paths cannot escape the filesystem guard.
- Cancel queued FFmpeg split futures after the first split failure instead of allowing unrelated queued work to start; clarified the migrated Auto-Chunker KB/s compatibility comment.
- Synchronized Help terminology with the visible Search/Phone-quality controls in all four UI languages.
- Added 8 focused Round 11 regressions; full suite: 288 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates all pass.
- Round 10 audit (2026-09-16): stopped Knigavuhe title filtering from hiding legitimate books containing “Отзыв/Комментарии”, preserved narration availability, and taught `BookController.enter(...)` argument parsing about nested parentheses.
- Made PoleKnig browser-fallback narration discovery use the rendered Playwright DOM, propagated pre-existing cancellation consistently, and exposed a public `DownloadRequest.track_index()` while retaining the private compatibility alias.
- Hardened path/index/media boundaries: guarded `Path.resolve()` in duration probing, matched copied/restored tracks by normalized index, normalized legacy string track indices, and made `DownloadWorker` safe against native/non-deepcopyable cover objects.
- Fixed audioknigi comma-delimited narrator metadata and completed narration-selector/search/export localization; `ui_text()` can now reuse exact runtime translations and the localization audit covers `addItem()` plus concatenated visible prefixes.
- Added 9 focused Round 10 regressions; full suite: 280 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary gates all pass.
- Round 9 audit (2026-09-16): hardened Cloudflare proxy authority parsing for IPv6 and preserved deterministic DoH CNAME-loop errors instead of hiding them behind bootstrap retries.
- Added browser-profile reuse for PoleKnig and audioknigi.com.ua Playwright fallbacks, including persisted browser headers and unexpired cookies.
- Bound resumable Range segments to URL/size/range geometry with a sidecar signature so stale chunks from a refreshed CDN object are discarded before assembly.
- Improved chapter/media handling: normalized whole-MP3 default templates without a literal extension, preferred precise start/end playlist boundaries, accepted whitespace before a UTF-8 BOM, inferred non-final chapter duration from the next start marker, and sanitized trailing whitespace/semicolons in loudnorm filter graphs.
- Hardened search/queue/state behavior: conservative audioknigi dash author splitting, preserved global template inheritance for legacy queue tasks, protected history backup/restore with the history lock, kept stopped-player resume positions from being overwritten by zero, refreshed unfinished-download state after manual output-path edits, and invalidated stale Easy-mode book input.
- Strengthened accessibility/Windows integration: weak-reference localized context-menu callbacks, pointer-width-safe media-key HWND conversion, dynamic generic-error localization, and an audit contract that requires visible search-cancel/log-toggle controls while no longer treating hidden compatibility buttons as keyboard-focus targets.
- Added 9 focused Round 9 regressions; full suite: 271 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary audits all pass.
- Round 8 Windows build hardening (2026-09-16): routed the Qt PyInstaller build through a Python 3.14 Windows bootstrap that bypasses the blocking WMI branch of `platform.win32_ver()` while preserving CPython's built-in fallback.
- Added a bootstrap preflight/self-test to `build_qt_ci.ps1`, a prerequisite check to `build_qt_exe.bat`, and regression coverage for the build path that previously stopped inside `platform._wmi_query()` before PyInstaller could start.
- Round 7 audit (2026-09-16): preserved explicit empty queue selections instead of converting them to “all tracks”, added a specific rights-restriction validation error, normalized legacy DE/UK track statuses, and hardened audioknigi title/author separation.
- Serialized two-pass loudnorm away from SSD parallel single-source splitting, bounded loudnorm stderr JSON scanning, reset speed-meter samples across transfer-counter resets, preserved the first Range worker error, and waited for active ffprobe duration workers during analysis cancellation.
- Improved Windows/Qt behavior: explicit HWND typing for media hotkeys, truthful zero-speed graph labels, visible Easy/Advanced search cancellation, inactive-app clipboard prompt deferral, robust ANSI/UTF-16 `.url` decoding, narration-switch accessibility cleanup, and best-effort state persistence before forced exit.
- Made short-track resume guards proportional while retaining the 3-second guard for normal audiobook chapters; changed the Normalize quality preset to an explicit encoding profile instead of contradictory stream-copy settings.
- Added 11 focused Round 7 regressions; full suite: 257 passed. Historical regression, exception, undefined-global, unused-import, Qt-localization, full-parity and Qt import-boundary audits all pass.
- Round 6 audit: fixed PoleKnig `<title>` fallback parsing so `«Book» Author: слушать...` yields only the quoted book title, and made narration-reader hydration clone incoming Knigavuhe variants instead of mutating caller-owned objects.
- Hardened the Windows Qt accessibility self-test by passing `-platform offscreen` directly to QApplication creation in addition to the environment override.
- Added defensive `.get()` access for PoleKnig candidate metadata and 8 focused regressions covering proxy EOF delivery, meta-tag boundaries, title parsing, hydration immutability, template suffix handling, explicit offscreen startup and Cloudflare-proxied remote ffprobe paths.
- Rejected several audit false positives after executable regression checks: CONNECT upstream EOF does not truncate already relayed bytes; `_extract_meta_content` cannot cross a `>` tag boundary; `DownloadRequest._track_index()` exists; spaced literal `.mp3` templates already normalize to one extension; remote ffprobe paths already use the Cloudflare proxy. Full suite: 246 passed, with all quality gates green.
- Round 5 audit: propagated cancellation through Knigavuhe variant enrichment, preserved rights-restricted availability during search hydration, and made empty version labels remain empty instead of rendering a bare `v`.
- Improved full-MP3 source-retention semantics: copy-mode now keeps a visible `(исходник)` file when `delete_source` is disabled and reserves disk space for both copies.
- Added ffprobe container-bitrate fallback for MP3/VBR files, aligned BookFlow `delete_source` defaults, serialized Auto-Chunker target-state logging, and accepted DTS-only packet timing during end-of-file validation.
- Made audioknigi.com.ua playlist parsing BOM-safe, removed the unsafe mixed-language full-file prefix fallback, and localized the remaining reported accessibility descriptions.
- Canonicalized queue duplicate checks and pending-search-result URL matching, synchronized Easy/Advanced URL clearing, and suppressed the redundant duplicate-confirmation dialog after an explicit History → Redownload action.
- Added 8 focused Round 5 regressions; full suite: 238 passed. Exception, historical-regression, undefined-global, unused-import, Qt-localization, full-parity and static Qt import-boundary audits all pass.
- Round 4 build-startup fix: removed the `book_analysis_service -> download.common -> download.__init__ -> source_analysis -> book_analysis_service` circular import by lazily exposing only `SourceAnalysisMixin` from the `audioknigi.download` facade.
- Preserved the public `from audioknigi.download import SourceAnalysisMixin` API and added a clean-interpreter regression test so partially-initialized-package cycles are caught before Windows/PyInstaller builds.
- Verification after the startup fix: 230 pytest tests passed; exception, historical-regression, undefined-global, unused-import, Qt-localization, full-parity and static Qt import-boundary audits all passed.
- Round 3 audit: tightened duplicate validation, browser-profile cookie bookkeeping, protocol-relative cover/playlist URLs, UNC/log privacy masking, bounded proxy half-close behavior and FFmpeg timeout cleanup.
- Added conservative disk-space estimation when Content-Length is unavailable, early peer cancellation after fatal Range errors, contiguous playlist indices and extension-safe default track naming.
- Completed dynamic search/duration/full-MP3 stage localization and strengthened settings/player/duplicate-dialog accessibility contracts without widening the public download-request API.
- Added 12 focused Round 3 regressions; full suite: 228 passed, with exception, historical-regression, undefined-global, unused-import, Qt-localization and full-parity audits all passing.
- Follow-up audit: preserved explicit 125% UI scale on deliberate settings saves and restored the legacy two-argument `persist_browser_cookies(cookies, headers)` compatibility form.
- Hardened malformed track-index handling in download requests/full-MP3 duplicate preflight, accepted BOM-prefixed `resume.json`, and made two-pass loudnorm fall back safely when FFmpeg reports non-finite measurements such as `-inf`.
- Tightened support-bundle privacy for Windows paths outside `%USERPROFILE%` and guaranteed UTF-8-safe log tails.
- Preserved Cyrillic visible text in accessibility fallback names, avoided stale QComboBox wrapper callbacks, returned empty-search focus to the visible Easy-mode input, and routed F1 directly to keyboard/accessibility help.
- Kept application-copied URLs suppressed while they remain in the clipboard, stopped hidden search animation timers defensively, and made single-row history deletion update in place with rollback on save failure.
- Avoided inventing an author from ambiguous dash-separated audiobook titles when independent page metadata does not provide one, and corrected the Ukrainian unresolved-error summary.
- Added 10 focused regression tests for this follow-up; full suite: 216 passed.
- Made Windows candidate-manifest validation accept both compact `"pass"` gate values and full gate result objects with a `status` field while keeping the hash-bound release-candidate requirement intact.
- Hardened unused-import analysis for nested quoted forward references and expanded runtime localization scanning across Qt pages and all main-window mixins.
- Made full-parity evidence use modular source bundles before declaring a facade file missing, and fixed historical pytest node-id parsing for parameter values containing spaces or ` - `.
- Preserved PoleKnig cancellation through author-catalog futures and the Playwright fallback, with cancellation checks around navigation/resource handling.
- Included an existing empty `errors.log` in support bundles so an error-free session is distinguishable from a missing log.
- Made `atomic_write_text()` create parent directories and made track splitting fall back to effective/declared duration when `end` is unavailable.
- Closed the audioknigi.com.ua Playwright browser before the ordinary HTTP playlist request so Chromium is not retained during a potentially slow requests call.
- Added the missing localized queued-full-MP3 multi-source warning discovered by the wider Qt runtime-message scan.
- Added 11 focused regressions for this audit round and updated the runtime marker to `qt-only-4.12.42`.

## 4.12.41 — Quality-gate, queue-mode and diagnostics hardening (2026-09-15)

- Made the accessibility self-test print its detailed audit report to stderr on contract failures, normalized report newlines, and replaced optimization-sensitive runtime `assert` checks with explicit errors.
- Fixed the frozen-module audit so packaged C extensions retain their package path and forbidden roots such as `pygame/...` cannot evade detection.
- Hardened static gates for standard module globals, qualified/direct localization calls and line-anchored pytest collection errors; removed stale tool imports and clarified parity evidence matching.
- Narrowed log credential redaction to complete credential-style keys so harmless fields such as `folder_tokens` remain diagnostic while `oauth_token`/`*_cookie` stay hidden.
- Added `og:title`/`<title>` metadata fallbacks, atomic text sidecars, selective support-bundle URL redaction, untruncated explicit history exports and non-mutating SearchResult URL canonicalization.
- Prefetched covers consistently for Knigavuhe/PoleKnig analysis and initialized the shared search model before page construction, removing hidden UI build-order dependence.
- Kept search edits focus-stable during background searches by switching them to read-only rather than disabling focused controls and restoring focus after empty/error outcomes.
- Added persisted queue download modes plus an `Добавить одним MP3 в очередь` action so batch queue jobs can run full-MP3 downloads instead of always forcing chapter mode.
- Added 16 focused regressions for this audit round and updated the runtime marker to `qt-only-4.12.41`.

## 4.12.40 — Stability, localization and shared-state hardening (2026-09-15)

- Prevented FFmpeg/loudnorm subprocesses from inheriting parent stdin and added explicit `-nostdin` to loudness-analysis commands.
- Serialized SSD-mode split progress updates under the same lock as the completion counter so concurrent FFmpeg workers cannot move UI progress backwards.
- Completed runtime localization for detailed download progress, duration probing and source/playlist stages; corrected Restore/Present terminology in legacy catalogs.
- Replaced substring-based diagnostic secret detection with exact/suffix credential matching so harmless settings such as `folder_tokens` are not over-redacted.
- Unified provider `fetch_book()` enrichment through `BookAnalysisService` for Knigavuhe/PoleKnig, matching the provider contract used by audioknigi.com.ua.
- Shared one history lock between downloader and library services, and snapshot backup members into memory with short Windows sharing-error retries before writing the ZIP.
- Rejected non-HTTP cover URLs before opening a requests session and made worker-thread accessibility announcements route through the queued `AccessibleAnnouncer` without calling `QWidget.window()` off the GUI thread.
- Added Alt+6 for the Player tab and made the event-sound volume tooltip hookup defensive.
- Added 15 focused regressions for this audit round and updated the runtime marker to `qt-only-4.12.40`.

## 4.12.39 — Cancellation, cover and runtime localization hardening (2026-09-14)

- Preserved `Cancelled` through PoleKnig narration discovery and audiobook page analysis worker futures.
- Added a shared cancellation-aware cover fetcher used by both analysis and download/media processing; fixed the missing downloader `_fetch_cover_bytes` path.
- Saved WebP covers with `.webp`, and routed sidecar `metadata.json` through the central locked atomic JSON writer.
- Ended CONNECT proxy relays when the upstream server closes instead of leaving an idle half-open worker.
- Hardened crash-report generation against recursive traceback formatting failures.
- Preserved URL-significant punctuation in PoleKnig meta content.
- Fixed null playlist titles, normalized accepted onboarding settings through `save_app_settings`, and guarded worker snapshots against native non-byte cover objects.
- Completed Ukrainian literals and localized the unresolved-queue summary through stable message IDs; added a full `Скачано X из Y` runtime translation.
- Added regression coverage for this audit round and updated the runtime marker to `qt-only-4.12.39`.

## 4.12.38 — Acceptance diagnostics and localization hardening (2026-09-14)

- Locked the accessibility self-test failure path to report the captured traceback details rather than any partially initialized report object.
- Made Windows acceptance report parsing BOM-safe and the undefined-global audit portable across the Windows-only `WindowsError` alias.
- Added four missing Ukrainian legacy UI literals already present in runtime localization so `ui_text()` cannot fall back to Russian for common search/book prompts.
- Refreshed the verified release-baseline date and clarified the Qt entry-point docstring so Phase 39 is identified as historical migration context, not the current release stage.
- Added focused regressions for accessibility self-test failure reporting, BOM-prefixed acceptance reports, platform-neutral globals and Ukrainian catalog completeness.

> Current release entries are maintained in English; historical entries preserve their original language as release evidence.

## 4.12.37 — Quality-gate and parser hardening (2026-09-13)

- Made the silent-exception gate occurrence-aware so a second broad `except ...: pass` in the same function cannot hide behind an existing allowlist entry; bare `except:` and `except BaseException:` are now audited too.
- Expanded unused-import analysis across module-level `if`/`try`/`except`/`finally` branches and quoted forward type annotations, and removed a no-op package-alias table from the Qt import audit.
- Made `--allow-non-windows` propagate through release-candidate validation/status checks instead of being defeated by hardcoded Windows requirements.
- Hardened localization AST extraction for keyword-form `ui_text(...)` calls and extended the simple-mode/accessibility contract for the cover and Audiobookshelf secret field.
- Made duplicate-sidecar matching fail closed on malformed current track indices, isolated history-refresh callback failures, and added ES6 backtick-string support to the Knigavuhe call parser.
- Improved expired-media recovery by inferring the affected selected track from a plain HTTP 404/410 response URL, and hardened ffprobe stream-shape parsing.
- Unified supported-source host constants across providers/parsers and made legacy queue recovery treat empty/fully-invalid selected-index payloads as whole-book recovery.
- Added 14 focused regressions covering the new quality gates, parser/runtime edge cases, provider constants, localization and accessibility contracts.

## 4.12.36 — Release integrity and compatibility hardening (2026-09-13)

- Made the Windows acceptance runner import version metadata from the canonical metadata facade and reap a process after forced termination before recording its exit code.
- Normalized historical pytest node IDs across Windows/POSIX separators so the archived regression allowlist works identically on all supported developer platforms.
- Hardened quality tooling for annotated localization constants, package `__path__`, sorted/stale exception allowlists, and split-module style regressions.
- Made legacy queue recovery tolerate malformed selected-index entries and explicit `all` markers instead of dropping otherwise recoverable tasks.
- Improved accessibility/localization wording for the main window, Ukrainian Undo/Appearance labels, and German Help/Download terminology.
- Made missing-selected-track errors report how many additional parts were omitted from the displayed list and cleaned remaining post-refactor formatting artifacts.

## 4.12.35 — Recovery, diagnostics and localization hardening (2026-09-12)

- Preserved whole-book resume manifests where `selected_indices` is `null` or an older empty list, instead of silently dropping the interrupted download.
- Made support-bundle path redaction root-safe and platform-consistent (`%USERPROFILE%` on Windows, `~` on Unix-like systems).
- Propagated `Cancelled` from Knigavuhe title hydration and replaced a runtime `assert` around Playwright with an explicit dependency error.
- Avoided no-argument formatting in legacy `ui_text`, made backup runtime localization tolerate CRLF, and added catalog consistency checks for duplicated exact/literal translations.
- Cleaned PEP-8 compression in the Range-controller and PlayerJS parser hot paths; retained `core.APP_VERSION` only as a public compatibility export while new consumers use `audioknigi.metadata`.
- Hardened Qt self-test DeferredDelete flushing for PySide bindings and made README quality-gate commands cross-platform.
- Added PyInstaller bootloader attribution plus an explicit release-licensing checklist; no application license is chosen automatically.

## 4.12.34 — Whole-book selection and runtime contract hardening (2026-09-12)

- Defined `DownloadRequest.selected_indices=None` consistently as “all tracks” across validation, duplicate preflight, result construction, queue persistence and Qt queue/download status rendering.
- Restored typed `AppSettings` handling in Qt settings synchronization, player persistence and backup restore.
- Made audioknigi.com.ua search cancellation propagate as `Cancelled` instead of looking like an empty search result.
- Restored “close first-run wizard = skip onboarding” behavior and persistently marks onboarding complete without terminating the application.
- Hardened source/frozen self-tests: failures print full tracebacks in source/console self-test runs and accessibility teardown continues even when `window.close()` fails.
- Avoided unnecessary stable-ID formatting when no interpolation values were supplied, preventing warning spam for literal brace examples.
- Cleaned split-module leftovers (`source_name` shadowing, search compatibility imports and source-analysis indentation) while preserving archived regression imports through explicit wrappers.
- Made home-directory log redaction use `%USERPROFILE%` on Windows and `~` on Unix-like systems.
- Documented the package-level Qt runtime audit and expanded third-party release/runtime notices for Qt, Playwright and bundled FFmpeg/FFprobe.
- Added focused regression coverage for whole-book queue round-trips, provider cancellation, settings mapping compatibility, onboarding skip behavior and self-test teardown.

## 4.12.33 — Post-refactor runtime integrity hardening (2026-09-12)

- Fixed split-module NameErrors in the track table and lifecycle/history mixins; added an undefined-global quality gate so moved methods cannot silently lose module globals again.
- Made `selected_indices=None` safe across request validation, duplicate preflight and result construction; legacy unfinished downloads retain zero-based track indices.
- Hardened invalid URL ports, empty `%APPDATA%`, disk-space preflight folder creation, frozen dependency diagnostics and settings normalization.
- Corrected runtime-localization precedence/coverage and current Help wording; removed shadowed prefix translations.
- Routed multi-source search through the `SourceProvider` registry and moved audioknigi.com.ua search/hydration into the provider layer; downloader source analysis now delegates PlayerJS/Cloudflare parsing to the shared `BookAnalysisService` instead of maintaining a second copy.
- Made Qt self-tests explicit/offscreen-safe and report the current runtime stage while preserving the historical Phase-39 acceptance marker for compatibility.
- Verified the 2026 release baseline against upstream release pages; Python 3.14.7, Chrome 153, PySide6 6.11.2, Playwright 1.62.0, Pillow 12.3.0 and PyInstaller 6.22.2 are released versions.

## 4.12.32 — Structured refactor hardening (2026-09-12)

- Clarified Python support: source/runtime compatibility remains Python 3.11+, while official Windows CI/release builds are pinned to CPython 3.14.7 x64; CI now checks the minimum Python version too.
- Normalized release notes so each released version has one H2 section; the many 4.12.31 development phases are historical H3 subsections under a single 4.12.31 line.
- Hardened source/provider boundaries, diagnostics privacy, status codes, localization coverage, accessibility contracts, duplicate matching and parser cloning.
- Cleaned dependency aliases/imports and added regression/quality gates for the post-refactor structure.
- Fixed the release-toolchain mismatch: the pinned CPython 3.14.7 build now uses PySide6 6.11.2 (the previous 6.8.3 pin declared Python <3.14), Playwright 1.62.0 and PyInstaller 6.22.2; source/runtime compatibility remains Python 3.11+.
- Hardened support-bundle path redaction/UTF-8 tails/opaque queue IDs, made internal track status codes language-neutral, fixed Knigavuhe variant cloning and fallback imports, accepted provider keys in search filters, and closed Qt accessibility/import-contract gaps.
- Added an unused-import quality gate after the downloader/main-window split and made service/provider dependency direction explicit.

## 4.12.31 — Phase 39 development line

### Structural architecture refactor

- Split the former ~4000-line Qt main window into responsibility mixins; `main_window.py` is now composition/common state.
- Split the former ~3500-line downloader into focused `download/` subsystems while retaining `audioknigi.downloader` as a compatibility facade.
- Added a versioned settings schema/migration layer and renamed the historical KB/s setting key without changing behavior.
- Added a common `SourceProvider` interface/registry for all three supported sources.
- Moved localization catalogs to packaged JSON resources and introduced stable message-ID APIs while preserving legacy literal compatibility.
- Reorganized active tests into unit/integration/architecture suites, moved historical phase tests into `archive/`, and added a historical compatibility gate that detects new regressions without enforcing obsolete monolith file shapes.
- Added privacy-conscious diagnostic support ZIP generation and a Help → Diagnostics UI action.
- Added a reviewed bare-`except Exception: pass` allowlist/audit so new silent exception swallowing fails a quality gate.
- Unified runtime version imports, added pinned release requirements and deterministic provider fixtures, and documented the new repository placement rules.
- Historical migration-only tooling and old release/audit variants are cataloged under `archive/`; active tooling remains under `tools/`.

Verification for this refactor is recorded in `audits/4.12/STRUCTURAL_REFACTOR_2026-09-12.md`.

### Audit 9 documentation/runtime consistency hardening

- Rebuilt README as current Qt-only documentation: fixed the source launcher, removed retired Tk/legacy rollback instructions, and documented the system-Edge Playwright fallback without an unnecessary Chromium download step.
- Removed the retired `tk-uia` notice and normalized CHANGELOG structure to one root header / one 4.9.3 entry; Phase 13 marker is explicitly historical.
- Prevented stale-source cleanup from creating an otherwise absent book folder.
- Made direct loudnorm measurement fail with a controlled FFmpeg-missing error instead of leaking `FileNotFoundError`.
- Explicit empty Playwright cookie snapshots now clear persisted cookies while preserving/refeshing the matching session profile.
- Added a total HTTP-header deadline to the local Cloudflare proxy, safe base `MappingDataclass.to_dict()`, and removed a dead templates localization import.
- Removed obsolete file-status `нет` translations from the pre-context i18n block and renamed the premature Phase 40 accessibility translation block to the current Phase 39 marker.
- Relaxed PoleKnig author-catalog prefiltering only for normalized title prefix/suffix variants while retaining detail-page author/title validation.
- Right-click context menus for tracks/search now select the row under the pointer before resolving the action target.
- Refreshed stale Qt-only/migration docstrings and de-duplicated player language lookup.
- Added Audit 9 regression coverage.

### Phase 39 resume, full-MP3 profiles and search-source fidelity

- Fixed single-stream resume when a previous run already downloaded the complete `.part`: HTTP 416 with `Content-Range: bytes */N` now promotes an exact-size partial to the final file instead of failing permanently.
- Made single-file `run_full_mp3()` honor the same audio preset and normalization contract as chapter downloads. MP3 copy is used only when the selected profile permits it; phone/stereo presets and one/two-pass loudnorm now trigger controlled FFmpeg processing.
- Added a second disk-space preflight after the full source is downloaded so transcoding has room for the output file, while retaining the initial source-download space check.
- Prevented `_remove_resume_manifest()` from creating an otherwise absent book folder by resolving the manifest path with `create=False`.
- Decode external audioknigi.com.ua and PoleKnig text/JSON playlists explicitly as UTF-8 bytes when available, avoiding `requests` ISO-8859-1 fallback for `text/plain` without charset.
- Local Cloudflare proxy connections now bypass public DoH for localhost, single-label NAS names and private suffixes such as `.local`/`.lan`, matching the Python resolver policy.
- Split logical “No” from the track-file missing status in i18n: file status stays `missing/fehlt/немає`, while boolean No remains `no/nein/ні`.
- Knigavuhe now consumes embedded `duration`/`length`/`time` playlist metadata and does not discard site-ranked matches that were found through description/series/genre rather than exposed title/author/reader fields.
- PoleKnig metadata matching includes narrator, direct `/books/<id>-slug/read` links canonicalize correctly inside the PoleKnig parser itself, and external playlists use UTF-8 byte decoding.
- Queue drag-and-drop de-duplicates URL and text MIME flavors emitted together by Chrome/Firefox/Edge.
- Player Previous/Next chapter fallback compares normalized path identities on Windows, preventing drive-letter case or slash differences from resetting navigation to the first chapter.
- Added runtime localization for `Файл загружен: <name>` in UK/DE/EN and removed the duplicated late Ukrainian diagnostics literal.
- Narrowed expired-media detection by removing the generic `not found` substring so unrelated local/tool errors do not trigger playlist refresh.
- Added 12 Phase 39 regression tests and synchronized two older full-MP3 source-contract tests with profile-aware processing.

Verification: 271/271 active tests pass; localization audit RU/UK/DE/EN PASS; full parity 61/61; Qt import audit 43 modules / 0 legacy; compileall PASS.

### Phase 38 runtime contracts, search fidelity and Windows hardening

- Hardened queue deserialization: legacy/edited `start`, `end`, `duration`, and `actual_duration` fields are normalized to numeric values or `None`; mapping-backed/corrupted track snapshots no longer crash queue serialization.
- Fixed Audioknigi search pre-filtering so queries such as `Акунин Азазель` are not discarded when the search card exposes only the title; strict matching now uses hydrated title + author + narrator metadata when available.
- Made CSV history export robust for multiline descriptions/quotes with explicit `QUOTE_ALL`, and coordinated backup restore with the live player-position timer/store so restored progress cannot be immediately overwritten by stale in-memory state.
- Removed forced `shiboken6.delete(QApplication)` from the accessibility selftest, avoiding undefined Qt singleton teardown in in-process test runners.
- Declared pointer-sized WinAPI ctypes signatures for `RegisterHotKey`/`UnregisterHotKey` on x64 and added registration fallback without `MOD_NOREPEAT`.
- Fixed Player UX/state: removed duplicate chapter activation wiring, background/automatic chapter transitions no longer switch tabs or steal focus, volume/rate changes update the live settings snapshot, and Stop after EndOfMedia cannot preserve an end-of-track resume point.
- Implemented `AccessibleDescriptionRole` for track rows, made vertical headers explicit strings, preserved explicit Cyrillic dynamic accessibility names in non-Russian locales, and removed duplicate whole-row AccessibleText announcements from Queue/History cells.
- Fixed Search provider-filter dead state: zero selected sites is rejected before inputs are disabled or progress animation starts. Empty analyses now clear deferred auto-download/queue/reanalysis state so a later unrelated book cannot start automatically.
- Hardened worker/thread teardown by clearing owner references before `deleteLater()` and guarding QThread state queries against already-destroyed C++ wrappers.
- Hardened PoleKnig PlayerJS fallback parsing to inspect script/code regions rather than arbitrary HTML `file:` text; authorless Knigavuhe recording pages can group by normalized title.
- Full-MP3 conversion now reports an explicit FFmpeg-missing error instead of falling through to `FileNotFoundError`; raw OSError caused by cancellation-closing a streamed response is normalized through the cancellation contract.
- Added effective-font-size fallback for unusual system fonts, extended FFmpeg-family startup probe timeout for slow antivirus/first-launch environments, and explicitly release tray menus/actions at shutdown.
- Added 22 Phase 38 regression tests and synchronized four older source-contract tests with safer QApplication/thread/player behavior.

Verification: 259/259 active tests pass; localization audit RU/UK/DE/EN PASS; full parity 61/61; Qt import audit 43 modules / 0 legacy; compileall PASS.

### Phase 37 deep audit hardening and shutdown/runtime cleanup

- Hardened parallel splitting/loudnorm: missing local source mappings now fail with a controlled diagnostic instead of `KeyError`, and complex loudnorm measurement requires an explicit map label.
- Made cancellation more deterministic: active HTTP responses are claimed once before close, zero-progress Range retries use cancellable backoff, and ffprobe/FFmpeg pipe handles are explicitly closed on teardown.
- Bounded long-running caches and thread ownership: audio/dataclass/DNS caches stay finite, PoleKnig author-page workers use their own thread-local sessions, and local NAS/.lan/.internal hostnames bypass public Cloudflare DoH.
- Preserved Knigavuhe performer search semantics, including narrator matching and Ё/Е normalization; search cancellation now propagates as `Cancelled` instead of returning a partial-success result set.
- Added PoleKnig `/books/<id>-slug/read` URL acceptance/canonicalization and BOM-tolerant backup JSON restore.
- Hardened legacy queue recovery: malformed string track indices are normalized, author/narrator metadata survive old queue imports, and Retry now automatically re-analyzes `needs_analysis` tasks and rebuilds their `DownloadRequest`.
- Reworked application exit to avoid `QThread.terminate()`: cooperative cancellation uses one guarded polling timer and a bounded final wait; only a process-level hard exit remains as the last resort for uninterruptible native I/O.
- Removed duplicate custom Ctrl+Tab shortcuts and relies on QTabWidget's native Ctrl+Tab/Ctrl+Shift+Tab behavior. URL edits compare canonical supported URLs before invalidating the analyzed book.
- Reduced UI/accessibility churn for large Queue/History/track/search tables with blocked bulk-update signals and bounded resize precision; row checkbox accessibility updates now cover the complete row.
- Fixed first-run/live scale reapplication from an unscaled QFont baseline, palette-sensitive System-theme onboarding contrast, hidden search-progress timer activity, weak-reference localized context-menu wiring, and low-level accessibility announcement throttling.
- Player resume waits for a seekable backend before applying the saved offset; saved positions below three seconds are consistently treated as the beginning. Windows media-key dispatch uses the window as the QTimer context.
- Bounded cached QMediaPlayer event-sound instances to three and retires old players cleanly.
- Extended the localization release audit to the user-visible technical session log; newly surfaced downloader/queue runtime messages are translated for RU/UK/DE/EN.
- Synchronized older regression/parity contracts with the safer Phase 37 behavior and added 21 dedicated Phase 37 regression tests.

Verification target: 237/237 active tests; localization audit RU/UK/DE/EN PASS; full parity 61/61; Qt import audit no legacy frontend path; compileall PASS.

### Phase 36 ID3 chapter titles and repair-source cleanup hardening

- Verified the packaged source contains the real `audioknigi/brand.py`; external `text/x-python` naming was a MIME/dump label, not a repository filename.
- Verified the Qt Search worker/service contract is already synchronized: `search_all_sources(..., sources=None)` accepts the per-site filter used by `SearchWorker`.
- Preserved meaningful chapter titles in MP3 ID3 `TIT2` tags. When a source track has a title, the tag now uses `Book — Chapter title` (without duplicating an already-prefixed book title); the generic `Book — часть NN` label remains only as a fallback when no chapter title exists.
- Hardened damaged-track repair: a failed verified output now forces a fresh `_repair_source_NN.mp3` download instead of trusting the cached source that may itself be corrupt.
- Source cleanup now keeps a stable set of every disposable original and repair source, so replacing `local_map[track.file]` with a repair file cannot orphan an old `_source*.mp3` on disk when `delete_source` is enabled.
- Kept the declared runtime baseline unchanged (`Python >= 3.11`, `PySide6 >= 6.8`); no obsolete Qt 6.5 accessibility fallback was added.
- Added executable regression coverage for the packaged brand module, Search `sources` API contract, real Mutagen ID3 round-tripping, title de-duplication/fallback behavior, and repair-source cleanup invariants.

Verification: 216/216 active tests pass; localization audit RU/UK/DE/EN PASS; full parity 61/61; Qt import audit 43 modules / 0 legacy; compileall PASS.

### Phase 35 audit hardening, global media keys and modular Qt UI

- Hardened shared-source recovery: a truncated `_source*.mp3` is cleared before audioknigi.com.ua -> Knigavuhe fallback, and fallback cancellation uses a safe optional `cancel_event`.
- Completed single-file MP3 parity: sidecars and Audiobookshelf scanning run for full-MP3 downloads, history records one output part, duplicate preflight understands `{title}.mp3`, and cleanup no longer creates empty folders.
- Fixed downloader/network edge cases: negative `fmt_time()` clamps to zero, duration errors use `effective_track_duration()`, PoleKnig Playwright logging is valid, Knigavuhe Ё/Е matching is normalized, the local HTTP DoH proxy strips blank header lines, and PoleKnig metadata workers use thread-local HTTP sessions.
- Hardened Qt startup/runtime: existing `QApplication` instances are reused, legacy UI-scale migration is applied, pixel-sized fonts scale correctly, onboarding theme changes apply before the first main-window paint, and the internal migration marker is synchronized to phase-35.
- Protected playback progress from being overwritten with zero before resume is applied; localized the resume message; auto-delete localized context menus; improved onboarding folder accessibility; de-duplicated tray activation.
- Added Search source filters for audioknigi.com.ua / knigavuhe.org / poleknig.com plus “Only available”, localized missing-media and output-folder dialogs, synchronized Easy/Advanced quality presets, fed zero-speed samples into the graph, hid Easy search results after selection, and added Shift+F10 to Queue/History.
- Added early shared-source timeline validation to `BookAnalysisService`, so truncated audioknigi.com.ua media can fall back during analysis instead of only after download starts.
- Added Windows global multimedia-key support: Play/Pause and Next/Previous chapter work while the window is minimized or another application is focused via `RegisterHotKey`, with `WM_APPCOMMAND` fallback, unregister-on-close, and duplicate-event suppression.
- Began structural decomposition of the oversized Qt window: worker classes / queue table moved to `qt/workers.py`, and the complete Player UI/playback surface moved to `qt/player_mixin.py`; `main_window.py` is reduced from more than 5,100 lines to about 4,470 without changing its public window class.
- Clarified compatibility assumptions in regression coverage: supported runtime is Python >= 3.11 and PySide6 >= 6.8, so Python 3.8 / Qt 6.5 compatibility shims are intentionally out of scope.

Verification: 210/210 active tests pass; localization audit RU/UK/DE/EN PASS; full parity 61/61; Qt import audit PASS with no legacy frontend path; compileall PASS.

### Phase 34 PoleKnig timeline, clipboard and search-flow finalization

- Restored remote duration enrichment in the GUI-neutral `BookAnalysisService` for PoleKnig/Knigavuhe one-file-per-track playlists. The Qt analysis path now probes missing chapter durations before rendering the Book table, matching the older download-engine behavior.
- The track table now uses the display-only cumulative audiobook timeline, so chapters with known duration but no source trim coordinates show meaningful Start / End / Duration values without mutating FFmpeg trim fields.
- Clipboard detection now listens to `QClipboard.dataChanged` while the application is already running, suppresses prompts for links copied by AudioKnigi itself, and writes an accepted clipboard URL into both Easy and Advanced input fields.
- Choosing a Search result now starts book analysis automatically in both UI modes; the action is explicitly labeled “Select and analyze”, leaving Download as the next normal user action.
- Expanded the localization audit across every Qt module: `_l`/`ui_text` literals, tooltips, accessibility names/descriptions, raw dynamic visible text, status-bar messages and modal prompts are checked for RU/UK/DE/EN coverage. Queue/history screen-reader summaries and diagnostics/About/Audiobookshelf text were localized as part of the pass.
- Updated Help Center search instructions in all four languages to describe automatic analysis after result selection.
- Added seven regression tests covering PoleKnig-style duration enrichment, cumulative timeline display, shared-source safety, live clipboard prompting, Easy/Advanced clipboard insertion, automatic Search analysis, and the extended localization audit.

Verification: 194/194 active tests pass; localization audit PASS; full parity 61/61; Qt import audit 41 modules / 0 legacy; compileall PASS.

### Phase 33 event-sound exclusivity

- Event cues now share one logical playback channel: starting a new cue stops any older MP3 cue first, so a retry/download-start sound cannot overlap a still-playing error sound.
- Re-triggering the same event restarts its existing player instead of layering a second playback instance.
- Narration changes now produce one success cue: `narration_changed` is played immediately, while the automatic re-analysis suppresses the redundant `book_found` cue on success. Analysis errors still keep their own failure cue.
- Added regression coverage for global event-sound exclusivity, retry-after-error behavior, and narration-change re-analysis sound suppression.

### Phase 32 runtime/i18n fixes

- Fixed a critical downloader name collision where the i18n `tr()` function was shadowed by a local `Track` variable, causing `Track object is not callable` immediately after `ffmpeg_split_start`.
- Download worker failures now write a full traceback through `app_logger.exception`, so `errors.log` captures worker exceptions as well as user-visible error text.
- Search availability codes are presentation-safe: `available` / `restricted` / `unavailable` are rendered as localized human labels, and an empty status is shown as a localized “status unknown” message instead of an em dash.
- Successful Knigavuhe result hydration now marks the row as available, reducing indeterminate statuses.
- Replaced Qt's potentially English-only native text-editor context menu with an application-language menu (Undo/Redo/Cut/Copy/Paste/Delete/Select All) for RU/UK/DE/EN, including the first-run folder field.
- Added five regression tests covering the real downloader split path, status localization, Knigavuhe availability propagation, text context-menu localization, and worker traceback logging.

Verification: 184/184 active tests pass; localization audit PASS; full parity 61/61; Qt import audit 41 modules / 0 legacy; compileall PASS.

### Phase 31 search feedback and volume polish

- Increased first-run subtitle contrast specifically for the System theme with a dedicated onboarding subtitle color, avoiding the too-dark native `palette(mid)` value seen on Windows dark system palettes.
- Added exact visible percentage labels for Player and event-sound volume sliders, localized AccessibleDescription updates, and a live tooltip while dragging.
- Added a circular animated search progress indicator with a percentage in both Easy mode and the Search tab; progress is tied to actual provider stages and keeps an activity arc moving while a slow provider is still busy.
- Added backend search progress callbacks without changing the existing SearchOutcome contract, plus localized progress/status strings for RU/UK/DE/EN.
- Added the new progress/value indicators to the accessibility ID contract and regression coverage for theme contrast, volume feedback, stage progress and localization.
- Verification: 179/179 active tests; localization audit RU/UK/DE/EN PASS; strict parity 61/61; Qt import audit 40 modules / 0 legacy paths; compileall PASS.

### Phase 30 API contract verification guard

- Re-verified the Phase 29 Qt localization/diagnostics API against the packaged source after an external audit reported stale-file ImportError risks.
- Added executable regression guards proving that `ui_text`, `localize_runtime_text`, `ERROR_LOG_FILE`, and `tail_error_log` are present, exported, importable and callable.
- Added a source contract test that the application-level `audioknigi_language` property is initialized and updated by `change_language()` for accessibility hints.
- No runtime implementation change was required: all reported missing symbols were already present in the actual Phase 29 final-product ZIP.

### Phase 29 final product UX, localization, accessibility and diagnostics

- Replaced the multi-step first-run flow with one compact setup dialog for language, output folder, quality and Easy/Advanced mode, ending with one primary “Save and start” action.
- Finalized the product UI: dynamic Easy-mode search/open action, contextual secondary actions, empty states for Book/Search/Queue/History, context-only destructive History actions, four Settings sections, stronger Player hierarchy, and a cleaner Help > Diagnostics menu.
- Completed the Qt localization contract for Russian, Ukrainian, German and English, including visible widgets, Help Center topics, onboarding, runtime statuses and 66 dedicated screen-reader AccessibleName strings.
- Added a release accessibility safety sweep that fills missing names/descriptions on every focusable app-level button, edit, combo, checkbox, slider, table/list and spin control; the runtime audit still validates stable control IDs and descriptions.
- Added a rotating `errors.log` created at startup, included its tail in copied support reports, exposed “Open error log” under Diagnostics, and record full unhandled crash tracebacks in both the crash report and error log.
- Removed hidden compatibility History buttons: Redownload/Delete now exist only as context-menu actions with stable QAction object names.
- Scoped default pytest discovery to the active `tests/` tree so archived pre-retirement Tk reference tests are no longer collected by a normal release test run.
- Verification: 170/170 active tests; localization audit RU/UK/DE/EN PASS; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Phase 28 Windows build finalization hardening

- Replaced the final release SHA-256 dependency on PowerShell `Get-FileHash` with a direct .NET `System.Security.Cryptography.SHA256` implementation, so release-manifest generation works in restricted Windows PowerShell environments.
- Made the queued Easy/Advanced focus handoff teardown-safe by weak-referencing the target widget and swallowing only the expected Shiboken `RuntimeError` when a deferred callback outlives the window.
- Added regression coverage for both the portable hash path and the deleted-widget focus race observed by the Windows offscreen accessibility preflight.
- Verification: 162/162 active tests; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Phase 27 book-player UX finalization

- Moved the Settings save action into a persistent footer outside category scroll areas, so it remains visible on short windows.
- Made the Player chapter list wrap text and permanently disable horizontal scrolling; shortened the unopened-book placeholder.
- Widened the centered Easy-mode card and made the speed graph compact while idle, expanding only during live transfer.
- Reworked Player opening around audiobook folders: open a book folder or an individual audio file, discover neighboring chapters, natural-sort numbered files, ignore temporary `_source*` media, load `metadata.json`, and find common local cover filenames.
- Opening an individual chapter, a selected downloaded track, the latest completed book, or a History item now builds the complete local-book chapter list.
- Added automatic EndOfMedia advance to the next local chapter while preserving per-file resume positions.
- Added the new folder-open control to the accessibility audit contract.
- Verification: 160/160 active tests; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Phase 26 accessibility/UI polish follow-up

- Synchronized the frozen accessibility contract with the Phase 25 History dropdown and three-section Settings layout; retained stable object names on History menu actions for diagnostics.
- Added an explicit disabled-state override for primary CTA buttons so an unavailable Download action is visually muted instead of remaining blue.
- Added Player empty states for missing cover art and an unopened chapter list.
- Made View > Easy/Advanced an exclusive radio-style QActionGroup and keep its check state synchronized with the segmented mode switch.
- Disable Search result actions until a concrete result row is selected in either advanced or easy mode.
- Verification: 153/153 active tests; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Phase 25 product UI polish

- Removed migration/parity engineering labels from the user-facing header, Book tab, Player tab and About surface.
- Rebuilt Easy mode as a centered 560–760 px card with one clear primary download CTA and an analyzed-book cover/metadata card.
- Reduced the Book toolbar to one dynamic Analyze/Cancel action plus one dynamic Download CTA with a compact options menu; the technical session log is collapsed by default.
- Hide resume recovery UI when no unfinished downloads exist and removed the duplicate speed placeholder from the graph.
- Reduced Queue controls to Add, Start/Pause, Stop, Up/Down, Delete and Actions; moved pause/priority/retry to the row context menu and grouped batch cleanup/retry under Actions.
- Consolidated History export into one dropdown and added a row context menu.
- Split Settings into three left-navigation sections: Basic, Download & Network, and Appearance & Integrations.
- Rebuilt Player as a compact centered card with cover art, book metadata, chapter list, ±30-second transport controls, timeline, volume and playback-rate controls.
- Added a shared modern QSS layer with a blue primary CTA, rounded controls/cards, cleaner disabled states and a segmented Easy/Advanced switch.
- Verification: 147/147 active tests; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Post-Phase-20 audit follow-up hardening

- Accept PoleKnig book URLs with legacy/search-engine title slugs (`/books/<id>-<slug>`) and canonicalize them to the stable numeric book identity.
- Bound deferred Qt shutdown to a 5-second cooperative grace period, then use emergency thread termination and a final hard-process fallback only for workers stuck in uninterruptible I/O.
- Make the accessibility self-test restore `QT_QPA_PLATFORM` exactly, reuse an existing `QApplication`, and explicitly dispose a selftest-owned application.
- Re-verified the already-applied Knigavuhe `cancel_event` propagation and duplicate-preflight `create=False` behavior.
- Verification: 112/112 active tests; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Qt-only Phase 19 (single-download recovery + crash-safe fallback persistence)

- Restored `get_http_session()` in `_download_single()`, fixing the confirmed Phase 18 single-stream/full-MP3 startup crash.
- Persist automatic source fallback into the active Qt queue immediately through a thread-safe request-change callback instead of waiting for final download completion.
- Parse loudnorm JSON structurally, preserve nested standard dataclasses, and shorten PoleKnig search request timeouts.
- Balance system-sound queue sentinels and retire cached Qt media objects with `deleteLater()`.
- Centralize deferred application exit, cancel all active workers together, remove duplicate worker-finished close connections, and suppress UI re-enable during shutdown.
- Sanitize internal focus-trace arguments in direct `create_application()` calls.
- Verification: 103/103 active Qt-only tests; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Qt-only Phase 18 (resource lifecycle + shutdown hardening)

- Unregister FFmpeg processes in `finally` and reacquire the active HTTP profile on each resumed Range subrequest.
- Keep `DownloadRequest.book` aligned with automatic source fallback so results/history/UI use the actually downloaded book.
- Restrict supported-URL validation to real book pages and harden queue snapshots/needs-analysis priority state.
- Make Knigavuhe/PoleKnig cancellation non-waiting at pool boundaries and tighten metadata request timeouts.
- Prevent repeat hidden close modals during worker shutdown and make missing-media dialog teardown safe.
- Replace the Windows system-sound executor with a daemon worker queue; restore the configured accessibility coalescing cadence.
- Record rejected dump false positives (`text/x-python`, missing `task_requires_analysis`, unbound `out`, invalid cancel keyword) separately from confirmed fixes.
- Verification target: 91/91 active Qt-only tests, strict parity 61/61, Qt import audit 39/0, compileall PASS; Windows accessibility self-test required (PySide6 is not installed in the Linux audit environment).

### Qt-only Phase 17 (audit follow-up hardening)

- Made legacy `needs_analysis` queue entries structurally non-runnable and guarded every Qt retry/resume path.
- Canonicalized search deduplication and Audioknigi metadata titles; added no-scheme host:port URL support.
- Fixed Knigavuhe cancellation NameError and propagated cancellation through variant/title hydration.
- Converted MappingDataclass to a truly read-only Mapping with cached field metadata.
- Hardened queue completion semantics/focus, manual output-directory synchronization, theme style guard, focus-trace CLI errors and event-sound lifecycle.
- Preserved the first polite accessibility status while coalescing later progress updates.
- Kept already-correct FFmpeg input-seek/output-duration semantics and assembling cleanup unchanged after verification.
- Verification target: active Qt-only tests 74+, strict parity 61/61, Qt import audit 39/0, compileall PASS.

### Qt-only Phase 16 (deep audit hardening)

- Hardened FFmpeg/ffprobe subprocess lifecycle, input-side seek consistency for two-pass loudnorm/splitting, partial `.assembling` cleanup, transfer-metric finalization and resume-manifest write failures.
- Duplicate preflight now requires every expected track to be validated as ready; HTTP sessions are long-lived and refreshed only when the persisted browser profile changes.
- Fixed proxy half-close relay/path forwarding, reduced nested search concurrency, added cancellation plumbing, legacy queue-item preservation and model-safe serialization.
- Hardened Qt accessibility announcements, focus selection, theme font preservation, speed graph finite-value handling, player resume/EndOfMedia behavior and focus-trace argument parsing.
- Classified audit false positives separately instead of changing already-correct SNI, PoleKnig scanner termination or queue end-DnD semantics.
- Verification: active Qt-only tests 55/55; strict parity 61/61; Qt import audit 39 modules / 0 legacy paths; compileall PASS.

### Qt-only Phase 15 (Windows runtime hardening)

- Fixed the confirmed PySide6 Windows startup crash caused by passing a tuple to `QObject.findChildren`; table scaling now uses `findChildren(QTableView)`.
- Hardened style switching with `QStyleFactory`, accessibility announcement politeness fallback, missing-media cancellation/modal lifecycle, queue selection resets, keyboard seeking and Qt Multimedia stop/resume behavior.
- Removed duplicate settings assignments; initialized Playwright analysis locals defensively; accepted both `CheckStateRole` and safe `EditRole` checkbox values.
- Strict functional parity remains **61/61**, with no legacy Tk runtime restored.

### Qt migration Phase 13 (full parity + Qt-only retirement)

- Replaced the previous "critical parity" rule with a strict inventory of **61 legacy user capabilities**; all 61 have concrete Qt/backend evidence.
- Added/finished Simple mode, universal input, URL/.url DnD, complete track/queue/history columns and actions, event sounds via Qt Multimedia, session log, speed graph, exact duplicate preflight, first-run wizard, geometry/large-mode/source-column settings, full hotkeys and diagnostic surfaces.
- Preserved Phase 8 keyboard/accessibility contracts after Phase 13 expansion (first-row focus, Enter/Return activation, F1 help and accessible row summaries).
- Pre-retirement full regression: **613/613 passed**.
- Built a reproducible Qt-only source tree and physically removed the legacy Tk frontend/support modules, fallback launchers, legacy build scripts and legacy dependencies.
- Post-retirement strict audit: **61/61 PASS, 0 legacy runtime paths**. Qt import boundary: **39 modules / 0 legacy frontend paths**. Qt-only active tests: **5/5**.
- The pre-retirement test suite is retained under `archive/tests/pre_qt_retirement/` solely as verification evidence.

### Qt migration Phase 12 (acceptance-gated default launcher promotion)

- Added a separate explicit Qt promotion contract; acceptance PASS alone never changes the default frontend.
- Added `promote_qt_launcher.bat`, `check_default_launcher.bat`, `rollback_to_legacy.bat` and fail-closed `run.bat`.
- Promotion is bound to app version, migration stage and the exact accepted Qt EXE SHA-256; rebuilding the EXE automatically revokes eligibility.
- `run.bat` revalidates complete Windows automated+NVDA+JAWS acceptance and the promotion marker on every start, otherwise launching the stable legacy frontend.
- Rollback removes only the promotion marker and preserves the Qt EXE, acceptance report and all user data.
- Moved two misplaced Phase 11 Qt build audit reports into the required `audits/4.12/` catalog.
- Verification: Phase 1–12 migration 92/92; full active repository suite 604/604; Qt import audit 33 modules / 0 legacy paths; 14/14 protected legacy files unchanged from Phase 11.

### Qt migration Phase 11 (live NVDA acceptance hardening)

- Исправлены шесть зон, отмеченных как FAIL в первой живой NVDA-проверке: ComboBox, очередь, история, настройки, плеер и модальные окна.
- Добавлены signal-only accessibility announcements для списков и секунд/процентов плеера без FocusIn/eventFilter-перехватчиков.
- Очередь и история теперь публикуют полноценное описание строки и динамически включают только применимые действия.
- QScrollArea настроек исключён из Tab-цепочки; интерактивные поля остаются нативно фокусируемыми.
- Вопросы/предупреждения переведены на явные application-modal QMessageBox с безопасным Escape.
- Acceptance runner стал возобновляемым: сохраняет PASS, повторяет только FAIL/SKIP, пишет детали ошибки и корректно переживает Ctrl+C.

### Qt migration Phase 10 (hash-bound Windows NVDA/JAWS acceptance)

- Added an exact-EXE SHA-256 release-candidate manifest after frozen Qt build gates pass.
- Added an incremental Windows acceptance runner requiring every mandatory matrix item separately with NVDA and JAWS; rebuilt binaries invalidate old approval.
- Added passive `QApplication.focusChanged` JSONL tracing with privacy-minimized metadata only and no event filters/focus redirection.
- Added focus-trace summaries plus `run_qt_acceptance.bat` / `check_qt_acceptance.bat`.
- Full active repository suite: 591/591 passed; Qt Phase 1–10: 79/79; static Qt import audit: 33 modules and 0 legacy frontend paths.
- Stable Tk protection: 14/14 key legacy files are byte-for-byte unchanged from Phase 9.

### Qt migration Phase 9 (critical functional parity)

- Added a formal Tk→Qt capability matrix and made critical functional parity a regression-tested invariant.
- Ported advanced downloader settings/templates, narration variants, Audiobookshelf, clipboard URL flow and `resume.json` continuation to Qt.
- Added Qt history open/redownload/delete/clear, JSON/CSV export and validated backup/restore of settings/history/player positions/Qt queue.
- Added direct URL→queue, queue clear and per-track context actions.
- Restored the legacy “Одним MP3” capability through the GUI-neutral downloader core, including resume/Range/cancel, ID3 and a real FFmpeg/local-HTTP integration test.
- Recorded Easy Mode/queue drag-drop as intentional differences and event voice sounds/localization/decorative cover cards as non-blocking deferred items.
- Full active repository suite: 580/580 passed; Qt Phase 1–9 focused suite: 68/68 passed; static Qt import audit: 32 project modules and 0 legacy frontend paths.

### Qt migration Phase 8 (accessibility hardening + acceptance gate)

- Added debounced native Qt accessibility announcements to prevent worker/status speech floods while keeping assertive errors immediate.
- Added deterministic current-row focus for search results, analyzed tracks and explicit queue transitions.
- Added `AccessibleTextRole` semantics for search/track models and queue/history cells.
- Added keyboard-only Space toggle for track selection, Enter/Return search activation and F1 accessibility help.
- Changed Qt player seek UI values from milliseconds to seconds (5 s arrows / 30 s page step) while preserving millisecond QMediaPlayer calls.
- Added dynamic Play/Pause accessible names and safe Stop/Escape semantics to the missing-media modal.
- Added `audioknigi/qt/accessibility_audit.py`, `--qt-accessibility-selftest`, frozen accessibility report and build gate.
- Added the Windows NVDA/JAWS acceptance matrix.
- Full active repository suite: 571/571 passed; Qt Phase 1–8 focused suite: 59/59 passed.

### Qt migration Phase 7 (clean runtime + Windows build pipeline)

- Split Qt runtime and build requirements; `pip install .[qt]` no longer inherits the stable Tk/pygame/pystray/Prism dependency stack.
- Added a static import-graph audit from `audioknigi_qt.py` that fails if the Qt runtime reaches legacy frontend modules.
- Added source/frozen Qt runtime self-tests that reject loaded legacy-only modules and verify Qt Multimedia/system-tray imports.
- Rebuilt `build_qt_exe.bat` around an isolated `.venv-qt` and `build_qt_ci.ps1`: one-file PyInstaller, bundled real FFmpeg/FFprobe, compact Playwright driver using installed Edge, frozen runtime/Edge reports and Analysis-TOC legacy-module rejection.
- Stable Tk launcher, runtime and build pipeline remain separate.

### Qt migration Phase 6 (native system tray)

- Added `QSystemTrayIcon` tray integration with Show/Hide/Player/Queue/Exit actions and native Qt notifications.
- Enabled the shared `minimize_to_tray` setting for active downloads/queues while keeping explicit Exit separate from ordinary close-to-tray behavior.
- Hidden 404/410 missing-media decisions now restore the main window before showing the required Qt modal prompt.
- Made `requirements-qt.txt` standalone and removed the legacy Tk/pygame/pystray stack from the Qt dependency path; the Qt PyInstaller build explicitly excludes pystray.
- Complete active regression suite passed in non-overlapping Xvfb groups: **552/552 passed**.

### Qt migration Phase 5 (Qt Multimedia player)

- Added a sixth `Плеер` tab backed by `QMediaPlayer` + `QAudioOutput`; the Qt branch no longer needs the legacy pygame player.
- Added local-file open, selected downloaded-track playback, Play/Pause/Stop, seek, restart, volume and 0.75×–2× playback-rate controls with Qt accessibility metadata.
- Added GUI-independent `PlayerPositionStore` using the same `player_positions.json` schema as the stable Tk player, including resume clearing at the beginning/end of a file.
- Persisted Qt player volume/rate in the shared settings and save player position during clean shutdown.
- Full active regression suite passed in timeout-safe groups: **544/544 passed**.

### Qt migration Phase 1 (parallel preview)

- Added a parallel `audioknigi_qt.py` PySide6/Qt Widgets entry point without replacing the stable Tk launcher.
- Added a GUI-independent multi-source search service and Qt `QThread` orchestration.
- Added accessible `QTableView` search results, existing-history display, shared settings, native Qt themes and `QAccessibleAnnouncementEvent` status announcements.
- Added `run_qt.bat`, `build_qt_exe.bat`, migration documentation, audit record and regression coverage.
- Downloader, queue, player and tray remain on the stable Tk implementation until their backend controllers are decoupled.

### Historical 4.12.31 release notes

- Reworked Tk accessibility focus handling after a repeated frozen-Windows `RecursionError`: global `FocusIn` now performs only constant-time queueing, coalesces bursts to the newest widget and runs visual/semantic work on a later `after(0)` turn.
- Removed nested `update_idletasks()` from accessibility initial-focus, visual-focus and search-result focus paths; search/root `FocusIn` handlers no longer synchronously force focus or finalize announcements inside `tkinter._substitute`.
- Coalesced `CTkScrollableFrame` focus auto-reveal callbacks and moved them from `after_idle` to `after(0)`, preventing nested scrollable ancestors from amplifying one focus transition into a callback storm.
- Made the `RecursionError` emergency branch strictly Tcl/Tk-free: it records a compact Python-side report and suspends accessibility focus processing without `after`, `after_idle`, messagebox, focus queries or traceback formatting.
- Added a 1,500-event `FocusIn` storm regression plus nested-event-pump and scroll-coalescing checks; complete active suite is now **512/512 passed**.
- Hardened shared-source recovery after a second real frozen-Windows reproduction: remote FFprobe may lose its HTTPS tunnel through the Cloudflare-resolving local proxy with `WinError 10054`, so an unavailable remote duration probe is no longer treated as proof that the source is valid.
- Added a local FFprobe packet-presence scan near the final advertised chapter timestamp. This detects truncated VBR/Xing MP3 files even when their metadata header still claims the original full duration.
- If the local shared source has no real audio packets near the required timeline end, the current download now raises a typed recovery condition and automatically switches to an identity-matched `knigavuhe.org` recording inside the same operation; if the fallback is unavailable, splitting stops safely instead of producing truncated chapters.
- Centralized FFprobe subprocess execution so the new packet scan reuses the existing cooperative/cancellable hidden-process path instead of adding another standalone `Popen` lifecycle.
- Added four follow-up regression cases for false-full VBR headers, real packet presence, in-download automatic fallback and safe stop without fallback; complete active suite is now **509/509 passed**.
- Added shared-source timeline validation for `audioknigi.com.ua`: one-file playlists are checked against the real remote/local MP3 duration before FFmpeg splitting.
- When an `audioknigi.com.ua` shared source is materially shorter than its chapter timeline, the app now searches and identity-matches the same title/author/narrator on `knigavuhe.org` and switches automatically before download.
- Added a local pre-split guard so incomplete shared sources can never be converted into truncated “ready” chapters; wrong-author fallback candidates are rejected.
- Added real-case regression coverage for the 14,068 s playlist vs ~12,254 s source mismatch; complete active suite is now **505/505 passed**.
- Added a compact Windows one-file build: Playwright now uses installed Microsoft Edge (`channel="msedge"`) instead of embedding its own Chromium browser.
- Build scripts remove stale Playwright `.local-browsers` content before PyInstaller, so an older reused `.venv` cannot silently restore the oversized browser payload.
- Reduced broad PyInstaller collection for Pillow/Mutagen/pygame/tkinterdnd2/ttkbootstrap/pystray while retaining required theme data, the Windows pystray backend, full Prism/tk-uia payloads and embedded FFmpeg/FFprobe.
- Added pre-build and frozen-EXE Playwright/Edge smoke tests plus final EXE-size reporting.
- Added compact-build regression coverage; complete active suite is now **499/499 passed**.
- Added a non-stealing Windows low-level `Insert+Up` observer so NVDA/JAWS gestures captured before Tk can still trigger reading of the actual focused editor value through Prism.
- Added automatic keyboard/screen-reader usage hints for every standard focusable control role and explicit open/closed/navigation speech for Comboboxes, including narration variants in Easy and Advanced modes.
- Hardened accessibility FocusIn callbacks against reentrancy and added a minimal RecursionError emergency handler that avoids recursive traceback formatting inside an exhausted Tk callback stack.
- Runtime-audited 117 focusable controls across Easy, all five Advanced tabs and Help Center with 0 unnamed/unknown controls requiring action hints; stress-tested Help Center focus transitions.
- Added screen-reader all-elements/recursion regression coverage; complete active suite is now **494/494 passed**.
- Extended the Simple-mode screen-reader editor contract to Advanced Book/Search/Queue/settings editors; Advanced Book accepts title/author text and routes it into search.
- Added explicit Windows diagnostics for `tk-uia`, `Insert+Up` gesture/read-line delivery, physical-VK hotkeys, confirmed search-table focus and speech delivery.
- Search result focus is now confirmed from the actual Tk focus transition instead of being logged immediately after `focus_set()`.
- Added strict Cloudflare 1.1.1.1 DNS-over-HTTPS resolution for public Python hostnames with direct `1.1.1.1` / `1.0.0.1` bootstrap and no system-DNS fallback.
- Playwright/Chromium and remote FFprobe use an application-owned localhost proxy whose destination DNS resolution is performed through Cloudflare DoH; Chromium QUIC is disabled to prevent proxy bypass.
- `requests` sessions ignore environment proxy variables so they cannot silently bypass the application's Cloudflare DNS policy.
- Hardened recreated Tk roots: reset inherited process `tk scaling` to the native baseline before child-widget creation, and `silent=True` scale application no longer persists transient values.
- Added Cloudflare/accessibility diagnostics regression coverage; complete active suite is now **485/485 passed**.
- Added Windows `tk-uia` accessibility provider so the universal `ttk.Entry` publishes its live value through UI Automation for NVDA/JAWS standard reading commands.
- Added a Prism-backed `Insert+Up` current-editor fallback when the screen-reader gesture reaches Tk.
- Made global `Ctrl+L`, `Ctrl+D`, `Ctrl+F`, `Ctrl+Q` and `Ctrl+H` layout-independent on Windows via physical virtual-key codes while retaining normal Latin Tk bindings without double execution.
- Successful searches now move focus to the Simple/Advanced results table, select the first row when needed, and explicitly announce the focus move/result count to NVDA/JAWS.
- Windows PyInstaller builds explicitly collect/self-test `tk_uia` and `tk-uia` metadata in the finished EXE; restored the active `docs/build/` documentation set.
- Added screen-reader editor/layout/search-focus regression coverage; complete active suite is now **470/470 passed**.
- Added exclusive cross-module operation ownership/generation so analysis/download/full/queue paths cannot overlap on shared `cancel_event`/runtime state.
- Added stale-result generations for search, cover previews and player duration probes.
- Publish `current_book` together with the UI update instead of from the worker thread.
- Moved player FFprobe duration work off the Tk thread and made audio probing cooperatively cancellable through managed `Popen` subprocesses.
- Shutdown now interrupts active HTTP responses and media subprocesses and gives registered background workers a cooperative completion window.
- Serialized history mutations, added strict persistence for backup restore, and made startup logging fail-safe on unwritable paths.
- Made `AudioKnigiApp` a lazy package export to avoid eager GUI/logging side effects during model imports.
- Added explicit parents to every active native file dialog.
- Moved periodic screen-reader backend refresh off the Tk callback path and routed remaining worker UI actions through the UI event bus.
- Added deep-hardening regression coverage; the complete active suite is now 461 tests.
- Micro-hardening follow-up: missing temporary source files are treated as already-clean without debug-noise or false removal counts.
- Added translation-placeholder regression validation across all 85 i18n keys and RU/UK/DE/EN without weakening runtime formatting diagnostics.

#### Additional late 4.12.31 accessibility and UI hardening

- Fixed context F1 on the Book tab so it opens the dedicated Book help topic.
- Synchronized read-only Text accessibility wording with the actual five-line PageUp/PageDown step.
- Removed Python 3.14 `return in finally` warning from the application Event Bus.
- Removed UTF-8 BOM from both Windows BAT build entry points.
- Made all native and custom question/error dialogs truly owned/modal; all 71 `messagebox` calls now have an explicit parent.
- Catalogued audit reports under `audits/` and technical documentation under `docs/`; added indexes for both collections.

- Help Center is now a real screen-reader document: activating a topic moves focus directly to its text and automatically announces the first paragraph.
- Help navigation reads paragraphs with Up/Down, jumps five paragraphs with PageUp/PageDown, supports Home/End, and Shift+Tab returns to the selected topic.
- Tab traversal is scoped to the currently active Toplevel so focus cannot escape behind Help Center or dialogs.
- Added a dedicated 3-pixel high-contrast visual focus ring for native ttk controls; read-only Text uses a matching native highlight ring.
- Visual focus is independent of NVDA/JAWS and therefore also helps keyboard-only/sighted low-vision users.
- Added regression coverage for Help Center reading, dialog focus containment and visual focus across real application controls.
- Hardened Dark/Light/System themes: semantic filled vs outline colors now use separate WCAG-safe palettes, and hover/pressed/disabled button states are visually distinct.
- Fixed Simple-mode confirmation/recovery cards staying dark in Light/System-Light.
- System theme now follows Windows appearance changes while the application is running.
- Visual keyboard focus uses yellow in dark themes and dark blue in light themes so the 3-pixel ring remains visible on both surfaces.
- Added automated contrast coverage for all semantic button states, hidden Simple-mode cards, all Advanced tabs and System-Light/System-Dark.

## 4.12.30

- Added immediate NVDA/JAWS feedback for checkbox/radio/combobox/slider changes.
- Added button-action confirmation when no richer status/dialog replaces it.
- Added explicit speech for track selection and bulk selection.
- Disabled action controls are skipped by Tab; global Tab fallback covers dynamic controls.
- Read-only Text controls remain keyboard-accessible and can be read line-by-line.
- Context-menu items are announced on `<<MenuSelect>>`.
- Fixed `PY_VAR...` Tcl variable names leaking into Combobox speech.
- Notebooks now announce selected tab name and position.
- Added mode-switch announcements and retained Prism NVDA/JAWS frozen packaging from 4.12.29.

## 4.12.29

- Fixed PyInstaller omission of the compiled CFFI extension `prism._prism_cffi`.
- Explicitly bundles `prism._prism_cffi` and `_cffi_backend` `.pyd` files.
- Adds hidden imports for both CFFI modules.
- Frozen accessibility self-test now validates and reports both compiled extension modules.
- Raised Windows Prismatoid minimum to 0.18.2.
- Added a default frozen self-test report path beside the built EXE.

## 4.12.28

- Fixed Windows frozen NVDA/JAWS packaging: Prismatoid's runtime package (`prism`) and native payload are now explicitly collected by PyInstaller.
- Removed the invalid `import prismatoid` runtime fallback that masked the original Prism loading error.
- Added a post-build accessibility self-test that runs inside the finished EXE; the build now fails if Prism/NVDA/JAWS API support is missing.
- Added `dist/accessibility_frozen_selftest.txt` diagnostics for Windows builds.

## 4.12.27 — NVDA/JAWS Tab Accessibility

- Fixed the real Advanced-mode startup focus bug that targeted the hidden Simple-mode URL entry and could leave focus on the root window.
- Added deterministic Tab/Shift+Tab navigation over visible, viewable, enabled interactive controls only.
- The accessibility layer now announces focused control name, role, state and value through Prismatoid and registers dynamic controls on first focus.
- Added `Ctrl+Shift+F12` to test the active NVDA/JAWS bridge and actionable ACCESSIBILITY logging in `app.log`.
- Upgraded the Windows Prismatoid requirement to `>=0.18.1,<0.19`; build scripts now upgrade requirements and verify the NVDA/JAWS backend API.
- Preserved normal Tk keyboard behavior, context shortcuts, scrolling and all MP3/download functionality.

## 4.12.26 — Event Sound Coverage & Windows System Fallback

- Audited all 17 bundled voice events and all 34 RU/EN MP3 assets; every asset parses as valid MP3.
- Confirmed 16 voice events have live runtime triggers; `update_available` remains intentionally dormant until a real update checker exists.
- Added Windows system-sound fallback for every voice event when pygame/MP3 playback is unavailable.
- Added system-only cues for application ready, required-input attention, and missing files detected during queue revalidation.
- Added the existing `error.mp3` to total search-provider failure, mini-player failures and disk-space preflight failures.
- Settings now expose separate **Voice** and **System** sound preview buttons and document the separate volume domains.
- Added `docs/audio/SOUNDS_4_12_26.md` plus regression coverage for event registration, call-site coverage, system-only playback and Windows fallback.

## 4.12.25 — Duplicate Metadata Fallback Hardening

- Повреждённый или нечитаемый `metadata.json` больше не означает «это точно другая книга»: duplicate-preflight использует `history.json` как резервный источник метаданных.
- `metadata.json` теперь записывается через временный файл + `os.replace()`, поэтому следующий запуск не увидит частично записанный JSON.
- Повторно проверены спорные пункты аудита: настройки действительно MP3-only; одна bulk-toggle кнопка подключена к `ActionsMixin`; root-coordinate fallback `_logical_y()` остаётся стабильным при прокрутке.

## 4.12.24 — Direct Slider Click & Queue File Revalidation

- Bandwidth and event-sound-volume sliders now move directly to a single clicked track position while preserving native thumb dragging and keyboard behavior.
- Queue items remember the actual MP3 paths that completed successfully.
- `Start Queue` performs a local finished-file preflight: intact non-empty files stay `done`; deleted/missing/zero-byte outputs reset the item to `pending` / «Ожидает» and allow it to run again.
- Added `QUEUE FLOW | event=completed_files_missing` logging and dedicated regression tests.

## 4.12.23 — Audit Hardening & Adaptive Range Recovery

- Confirmed that project `CTk*` widgets are native Tk/ttk compatibility classes, not CustomTkinter; `CTkButton` explicitly consumes `bootstyle` and maps it to project/ttkbootstrap styles.
- Centralized `APP_TITLE` on `brand.DISPLAY_NAME` and removed the hard-coded accessibility ready announcement.
- Corrected `DragDropMixin` class-docstring placement; its mode detection continues to use safe `getattr` fallbacks.
- Synchronized JSON readers and writers with the same re-entrant lock while retaining temp-file + `os.replace()` atomic persistence.
- Removed a dead MP3-only `output_mode` local and redundant pre-processing before `json.loads()`.
- Auto-Chunker can now recover concurrency after a temporary slowdown: downshifted workers park instead of terminating, and sustained per-worker recovery scales the target back up toward the initial worker count.
- Added a root-coordinate fallback to scrollable-frame focus positioning for unusual Tk parent hierarchies.
- Fixed DPI-responsive squeezing found by the full regression sweep: simple-mode stacking now considers current natural panel widths after scaling, quality cards use the real main-panel width, hero wrapping re-syncs after reflow, and the advanced Book bulk-toggle button reserves its natural width before the header text.
- Added focused regression coverage for bootstyle compatibility, DnD host safety/docstring, JSON read/write synchronization, branding, scroll-position fallback, Auto-Chunker downshift/recovery, MP3 estimator cleanup and raw JSON parsing.
- Re-audited the reported SyntaxError/source-artifact/zebra/tray/hotkey/alias concerns and documented why they are not current runtime bugs.

## 4.12.22 — One Toggle Bulk Selection Button

- Replaced the two visible bulk-selection buttons on the advanced Book tab with one state-aware **«Снять все» / «Выбрать все»** button.
- The button derives its label from the real track state: all selected -> **«Снять все»**; any track unselected -> **«Выбрать все»**.
- Manual checkbox changes immediately synchronize the button label and accessibility name for NVDA/JAWS.
- Preserves bulk operation across large books (including 100+ parts) and all 4.12.21 hidden-FFmpeg/maximized-start behavior.
- Added regression coverage for one-button rendering, 100-part toggling, and partial manual selection synchronization.

## 4.12.21 — Hidden Media Processes & Maximized Startup

- FFmpeg and FFprobe now launch with Windows `CREATE_NO_WINDOW` plus `STARTUPINFO/SW_HIDE` fallback, preventing console/terminal windows from flashing above the GUI on Windows 10/11.
- The hidden-process policy covers media-tool validation, local/remote duration probing, codec inspection, normal FFmpeg conversion/splitting and loudness-analysis paths.
- The main window now starts maximized. On Windows it uses the native `zoomed` state so the OS sizes the app to the active monitor work area using the user's current resolution, DPI scaling and taskbar reservation rather than a hard-coded fullscreen geometry. The old fixed 1080x760 minimum is now capped for smaller displays.
- Restoring the app from the tray returns it to the maximized layout.
- Added `DISPLAY START` diagnostics to `app.log` with detected screen/virtual resolution and Tk scaling.
- Added regression coverage for Windows hidden subprocess flags and maximized startup behavior.
- Windows EXE build scripts remain pinned to CPython 3.14.7 x64.

## 4.12.20 — MP3-only & Complete Help Center

- Removed the current M4B feature set from runtime/UI: output selection, preview, build/tagging paths, queue/resume output mode and M4B-specific onboarding/settings strings. The supported final audio format is now MP3 only.
- Legacy saved output-format preferences are ignored safely and are not persisted back into current settings.
- Audited all application keyboard bindings and consolidated their user-facing descriptions into the Help Center.
- Expanded the Help Center into a complete topic-based manual covering supported sources, modes, Book tab, narration selection, bulk part selection, mini-player, download/duplicate/cancel behavior, queue, history, quality, settings, files/metadata, backup/restore, accessibility, hotkeys, app.log/BOOK FLOW diagnostics and recovery.
- Added regression coverage that prevents M4B runtime code from returning and verifies Help/shortcut coverage.
- Windows EXE build scripts remain pinned to CPython 3.14.7 x64.

## 4.12.19 — Automatic Duplicate Guard & Reliable Cancel

- Removed the manual **«Проверить скачанные файлы»** button from the advanced Book tab. Existing-file verification now runs automatically as part of the normal analysis/download flow.
- Added one common duplicate preflight for simple mode, advanced mode, and auto-download. The modal is shown only for a full-book selection when the requested output is complete and saved metadata matches the same normalized source, title, author, narrator, genre, year, description, cover metadata, part count, and chapter structure.
- Partial selections intentionally bypass the duplicate modal so a user can repair or re-download individual parts.
- The existing duplicate dialog remains actionable: open the existing folder, download again, or cancel.
- Cancel is now idempotent and immediately changes both cancel buttons to **«ОТМЕНЯЮ…»** and disables them after the first click.
- Active streaming HTTP responses are registered and closed on cancel so Range/single-file downloads are not forced to wait for a long read timeout before observing cancellation.
- Local/remote ffprobe duration checks are now cancellation-aware and terminate their subprocess promptly when cancel is requested.
- Added `BOOK FLOW` diagnostics for duplicate preflight/dialog, cancel request, and interrupted network responses.
- Added regression coverage for exact duplicate detection, metadata mismatch, history fallback, common preflight routing, button removal, idempotent cancel, and active-response interruption.

## 4.12.18 — Stable Source Mapping & Duration Verification

- Fixed partial retry/repair source mapping: temporary `_source_XX.mp3` slots are now derived from the complete book playlist, so retrying parts 2/3/5 continues to use `_source_02`/`_source_03`/`_source_05` instead of renumbering the subset and feeding the wrong chapter to FFmpeg.
- Added DEBUG `BOOK FLOW | event=source_mapping` records with stable source index, temporary filename and affected track indices for future diagnostics.
- Relaxed MP3 duration verification from 2 to 5 seconds to tolerate normal playlist/encoder/VBR metadata drift while still rejecting clearly mismatched chapters.
- Added regressions reproducing the real 48:21 vs 48:24 false-positive and the 21:06 wrong-source mismatch from the Windows log.
- Preserves 4.12.17 bulk part selection and one-button mini-player, plus the 4.12.16 event-bus hardening. Windows EXE builds remain pinned to CPython 3.14.7 x64.

## 4.12.17 — Bulk Part Selection & One-Button Mini-Player

- Moved the existing **Выбрать все** / **Снять все** actions from the right-side scrollable controls directly into the parts-table header on the advanced Book tab so they remain visible next to large track lists.
- Bulk selection updates every track model and every checkbox cell in one operation; the buttons are enabled only when a book is available and the app is not busy.
- Replaced the separate Play and Pause controls with one stateful mini-player button: **▶ Воспроизвести** → **⏸ Пауза** while playing → **▶ Воспроизвести** while paused. Pressing Play after a pause resumes from the same position.
- Stop and natural completion reset the stateful button to **▶ Воспроизвести**; seeking while paused keeps the player paused and keeps the Play label.
- Added 4.12.17 regression coverage for 100-track bulk select/clear and single-button transport-state dispatch.
- Windows build remains pinned to CPython 3.14.7 x64 and keeps the real FFmpeg/FFprobe bundle checks.

## 4.12.16 — Event Bus Reliability & Queue State Consistency

- Replaced `traceback.print_exc()` in `UIEventBus._drain()` with full `app.log` traceback diagnostics that do not depend on `sys.stderr` in PyInstaller `--windowed` builds.
- Re-arm the Tk event-bus `after()` callback from `finally`, guaranteeing that a failing queued UI callback cannot permanently stop future `self.ui(...)` updates.
- Continue processing later callbacks in the same batch after one callback fails; callback diagnostics include a privacy-safe module/qualname label.
- Added `QueueItem.status_code_before_pause` and restore it together with `status_before_pause`, keeping `retry_pending` and future semantic states consistent across item pause/resume.
- Made the 4.12.9 HTTP 404/410 recovery contract literal: at most one full page/playlist refresh per `_process_book()` run, even when multiple distinct missing parts are skipped afterward.
- Added regression coverage for `sys.stderr = None`, logger failure during event-bus error handling, pump re-arming, semantic queue status restoration and multi-part one-refresh behavior.
- Release packaging is cleaned of Python/test caches and temporary build output before ZIP creation; `make_source_release.py` reproduces the same exclusion/validation rules.
- Validation note: source tests here run in the available Linux Python 3.13.5 environment; Windows EXE build scripts remain hard-pinned to CPython 3.14.7 x64.

## 4.12.15 — Full Book Flow Logging

- Added structured `BOOK FLOW | event=...` records to `app.log` for the successful audiobook lifecycle: analysis start/completion, narration selection, download planning, source downloads/reuse, FFmpeg split, verification, cover state, ID3, M4B, sidecars, cleanup, history save and final completion.
- Per-track FFmpeg, verification and ID3 success records are written at DEBUG level, while stage boundaries remain INFO for fast support diagnostics.
- Successful FFmpeg runs now record return code, elapsed time and the sanitized command, complementing the existing full stderr diagnostics on failure.
- Main download and full-MP3 worker failures now write full tracebacks with book/narrator context instead of relying only on the short UI error line.
- Media URL refresh/retry and skipped-part paths now leave structured lifecycle markers so a 404/410 recovery can be reconstructed from the log.
- History persistence now records a `history_saved` event, allowing support to distinguish successful file creation from successful history commit.
- Updated the legacy architecture regression check to the 4.12.14+ log rotation policy (at least 5 MB × 5 files).

## 4.12.14 — UX, Narration Choice & Detailed Diagnostics

- Added the same narration/reader selector to the simple-mode pre-download confirmation that already existed on the advanced Book tab; it is shown only when more than one recording is available.
- Added explicit dark/light-aware `AudioKnigi.Vertical.TScrollbar` and `AudioKnigi.Horizontal.TScrollbar` styles to every Treeview table.
- Made bandwidth and event-sound slider values visually explicit; unlimited bandwidth is now shown as `0 МБ/с — без лимита`.
- Made simple/search keyboard shortcut hints responsive so Enter / Shift+F10 help wraps instead of clipping on narrow windows.
- Expanded `app.log` to include thread name, module, function and source line, increased rotation to five 5 MB backups, and enabled file-level DEBUG diagnostics.
- Added full traceback logging for unhandled Tkinter callbacks, background threads and main-thread failures, plus key caught/recovered boundaries (analysis, provider search, queue processing, backup/restore, ID3/M4B/sidecars and Audiobookshelf).
- Audited all 40 Python modules for exception handling; added a regression check that every module parses and that no bare `except:` exists. See `audits/4.12/ERROR_HANDLING_AUDIT_4_12_14.md`.
- Preserves 4.12.13 logic/i18n hardening, 4.12.12 safe shutdown, real FFmpeg/FFprobe bundling and the Python 3.14.7 x64 build pin.

## 4.12.13 — Logic & i18n Hardening

- Replaced Russian-substring status inference with semantic status kinds plus locale-aware rendering, preventing status badges from breaking in English/German/Ukrainian and avoiding false positives from book titles such as «Ошибка резидента» or «Разделение».
- Normalized simple/advanced UI mode logic to stable internal keys (`easy` / `advanced`) instead of localized display text.
- Made advanced-tab cycling tolerant of either a method or stored tab key, avoiding accidental `TypeError` when the active-tab value is a string.
- Marshalled AccessibilityManager Tk calls/scheduling back to the UI thread when invoked from workers.
- Added stable queue `status_code` values so queue success/failure logic no longer depends on localized words such as «Ошибка».
- Added dynamic track-number padding for 100+ part books (`001` … `100`) in both default naming and `{Track_Number}` templates.
- Completion size calculation and built-in Listen actions now recurse into book subfolders such as CD1/CD2.
- Updated simple-mode Drag-and-Drop hint together with the other registered drop targets.
- Replaced O(N²) media-URL de-duplication with ordered set-based tracking.
- Hardened metadata fallback: generic JavaScript `name` values are no longer mistaken for book titles; structured JSON-LD Book/Audiobook/CreativeWork metadata is preferred.
- Replaced dynamic `__import__("re")` use with a normal module import and removed several avoidable localized/UI coupling points.
- Prefer Tk's native single-binding `unbind(sequence, funcid)` on modern Python/Tk, retaining the Tcl-script parser only as a compatibility fallback.
- Avoid indefinite synchronous player-position writer joins during shutdown and keep the safe-shutdown behavior from 4.12.12.
- Keeps the validated real FFmpeg/FFprobe bundle from 4.12.11, missing-part choice from 4.12.10, and Python 3.14.7 x64 build pin.

## 4.12.12 — Safe Tk Shutdown

- Fixed a Python 3.14/Tk 8.6 shutdown race that could create `last_crash_report.txt` with `_tkinter.TclError: can't delete Tcl command` after the application had already saved `running: false`.
- The known duplicate-command error is suppressed only during final application teardown; the same Tcl error still surfaces during normal runtime/rebuilds.
- `on_close()` is idempotent so repeated WM close events cannot start teardown twice.
- Direct root destruction is also guarded and continues to cancel pending `after` callbacks before Tcl teardown.
- Keeps the validated real FFmpeg/FFprobe bundle from 4.12.11 and the missing-part choice from 4.12.10.

## 4.12.11 — Real FFmpeg Bundle

- Windows/PyInstaller builds resolve the actual FFmpeg and FFprobe binaries instead of embedding Chocolatey `bin` shims.
- Build-time `-version` validation rejects unusable media-tool executables.
- Runtime resolution validates bundled FFmpeg/FFprobe and falls back to a working system copy if a bundled executable is broken.
- Fixes `_MEI...\ffmpeg.exe` / `_MEI...\ffprobe.exe` returning `0xFFFFFFFF` (`4294967295`) with no stderr.
- Keeps the 4.12.10 missing-media skip/stop choice and all previous 4.12.x fixes.

## 4.12.10 — Missing Media Part Choice

- When a media file remains HTTP 404/410 after refreshing the playlist, show an accessible decision dialog instead of always aborting the whole book.
- Safe default: **Остановить загрузку**. Optional action: **Пропустить часть и продолжить**.
- Identify the exact affected track indices, including multiple chapters that share one missing source file.
- Continue all remaining selected parts after an explicit skip and log the skipped indices.
- Finish partial books with a visible warning/status **Готово с пропуском**; queue items use the same explicit partial-completion state.
- Preserve the Python 3.14.7 x64 build pin and all 4.12.9 media-URL refresh behavior.

## 4.12.9 — Expired Media URL Recovery

- Detect HTTP 404/410 from direct audio/CDN downloads, including wrapped Range-download errors.
- Re-analyze the book page and fetch a fresh playlist once instead of retrying a stale media URL.
- Preserve selected/local track state while replacing fresh network metadata.
- Remove only disposable `_source`, `.part`, and `.seg` download artifacts before retrying.
- Show a clear error if the refreshed playlist also leads to HTTP 404/410.

## 4.12.8 — FFmpeg Compatibility and Full Diagnostics

- Fixed original-quality MP3 export for sources whose real codec is AAC/M4A or cannot be identified as MP3.
- Stream-copy is now allowed only for genuine MP3 input.
- Added one automatic retry with `libmp3lame` when stream-copy fails unexpectedly.
- Added FFmpeg command, return code, and complete stderr to `app.log` on failures.
- Kept the Windows build pinned to Python 3.14.7 x64.

### Build system — Python 3.14.7
- Windows EXE builds are pinned to CPython 3.14.7 x64.
- Existing `.venv` environments created with a different Python version/architecture are automatically recreated.
- `build_ci.ps1` now hard-fails on interpreter mismatch.
- GitHub CI and release workflows use Python 3.14.7 explicitly.

## 4.12.7 — Direct Folder Picker in Simple Mode

- In simple mode, **Шаг 3. Папка сохранения → Изменить** now opens the system folder chooser directly instead of redirecting to Advanced Settings.
- The action reuses the same `choose_folder()` flow as the advanced Book tab, so the selected path is immediately reflected in both modes and persisted in settings.
- The simple-mode folder action remains keyboard-accessible.
- Added regression coverage ensuring the button invokes folder selection without leaving simple mode.

## 4.12.6 — Scale Migration & Combobox Wheel Direction

- Existing profiles that still contain the legacy automatic `125%` UI scale are migrated to `100%` exactly once.
- A persistent migration marker ensures that if the user later selects `125%` manually, that preference is preserved on future launches.
- Closing an open native `ttk.Combobox` with the mouse wheel no longer triggers focus auto-reveal that could pull a scrollable page upward.
- The wheel gesture that dismisses an open dropdown is forwarded to its owning scrollable page with the original direction: wheel down scrolls down and wheel up scrolls up.
- The dropdown still closes immediately when scrolling starts, preventing the popdown from sticking over the interface.

## 4.12.5 — Keyboard & Validation UX

- Empty «Найти или открыть» input now opens a centered modal validation dialog instead of a card below the fold.
- «Перейти к полю» closes the dialog and returns keyboard focus to the universal input; Enter activates it and Esc closes the dialog.
- Native buttons reliably activate with Enter / keypad Enter in addition to Space.
- Search result tables open the selected book with Enter and expose actions through Shift+F10.
- Alt+1…5 opens Book / Search / Queue / History / Settings; Ctrl+Tab and Ctrl+Shift+Tab cycle advanced tabs.
- Ctrl+L focuses the universal input, while F4 / Alt+Down opens dropdowns and Esc closes them before cancelling work.
- Fresh search results receive keyboard focus automatically, with the first row selected when needed.
- Screen-reader announcement accompanies the empty-field validation dialog.

## 4.12.4 — Combobox Scroll Guard

- Исправлено зависание/«прилипание» открытых выпадающих списков `ttk.Combobox` при прокрутке колёсиком длинных страниц.
- Перед прокруткой Canvas открытый native ttk popdown закрывается, поэтому он больше не остаётся поверх несвязанных пунктов интерфейса.
- Глобальный wheel-guard охватывает и обычные `ttk.Combobox`, и совместимый `CTkOptionMenu`, включая внутренний Tcl Listbox выпадающего окна.
- Перетаскивание вертикального scrollbar длинной страницы также закрывает открытый список до перемещения содержимого.
- Добавлены 3 regression-теста для MouseWheel, обычного ttk.Combobox и scrollbar-прокрутки.

## 4.12.3

- Changed the first-run/default interface scale from 125% to 100% for clean installations and portable EXE distribution.
- Centralized the default in `DEFAULT_UI_SCALE = 100` so app startup, settings saving/restoring and scale fallbacks cannot drift apart.
- Existing users keep an explicitly persisted scale (125/150/175/200%); only missing or invalid scale settings fall back to 100%.
- Added regression coverage for clean-profile 100% startup and preservation of a saved 125% preference.

## 4.12.2

- Audited the complete 4.12.1 archive; reported truncated-file SyntaxErrors were not present in the actual ZIP and the project compiles cleanly.
- Made `AccessibilityManager.install()` idempotent, added root-parent guards and changed repeated screen-reader announcements to a sliding debounce window.
- Guarded clipboard offer dialogs from FocusIn re-entry and made tray/DnD state reads safe on partially initialized hosts.
- Completed Help Center short aliases for all ten topics and localized the first onboarding step for RU/UK/DE/EN.
- Knigavuhe now hydrates missing author metadata even when a narrator is already known, improving author-search filtering.
- Player resume markers are removed when seeking back below three seconds; M4B/M4A/AAC consistently route to the external player from the normal Play action.
- PoleKnig search title scoring rejects catalogue badges in favor of descriptive book labels; the unquoted PlayerJS fallback parses balanced nested object literals safely.
- History cover discovery no longer probes CWD when an entry has no folder.
- `CTkOptionMenu.configure(width=...)` now preserves CustomTkinter-style pixel semantics; `CTkScrollableFrame` proxies geometry reconfiguration to its outer viewport.
- Added 15 focused 4.12.2 regression tests.

## 4.12.1

- Audited the complete 4.12.0 archive against a new set of truncated-source reports; the reported SyntaxErrors were not present in the actual files.
- Help Center navigation now resolves articles by stable i18n keys rather than translated display titles.
- PoleKnig search filters short service labels such as “Слушать онлайн”, “Скачать” and “Подробнее о книге” so they cannot replace the actual book title.
- PoleKnig PlayerJS property extraction now ignores property-looking text inside JavaScript strings and comments.
- Queue row drag feedback now validates Treeview bbox tuple length before indexing partially visible rows.
- Added focused regression coverage for the confirmed audit findings.

## 4.12.0

- Reworked the default home screen around one universal **title / author / URL** field. Supported URLs open directly; ordinary text searches audioknigi.com.ua, knigavuhe.org and poleknig.com together.
- Renamed the visible UI modes to **Простой режим** and **Расширенный режим**, and added a direct **Расширенные возможности** entry point from the simple dashboard.
- Reworked first-run onboarding around two user goals (search for a book or use an existing link) while preserving the compact three-step setup.
- Added simple-mode recovery cards that offer the next useful action for bad URLs, network failures, missing books, and restricted recordings.
- Narration selectors can label known availability and restricted books expose **Перейти к доступной озвучке** when an accessible alternative exists.
- Simplified search tables to Title / Author / Reader / Status / Source. Raw URLs are hidden from the table and remain available from the context menu.
- Added an explicit pre-download confirmation card showing title, author, reader, part count and destination folder. Ctrl+D follows this confirmation in simple mode instead of bypassing it.
- Expanded human-readable progress states and made the completion card report downloaded part count and destination folder with clear next actions.
- Added contextual F1 help for Search, Queue, Settings, History/Files and Download workflows.
- Added 11 dedicated 4.12.0 regression tests covering the new simple workflow, status/search UI, narration recovery, confirmation, completion, contextual help and shortcut behavior.
- Hardened responsive header layout so the full version badge remains readable after live theme/scale changes, and shortened the no-DnD fallback hint for high DPI layouts.
- Direct application destruction now closes the UI event bus, cancels pending Tk `after` callbacks, restores the process thread exception hook and clears the running-session marker; this prevents stale Tcl callbacks during repeated GUI lifecycles.

## 4.11.2

- PoleKnig author searches now supplement the generic `?q=` results with the matching author's own `/authors/<id>` catalogue.
- Author-catalogue pagination (`?p=2`, `?p=3`, ...) is followed automatically up to the existing 100-result application ceiling.
- Matching author links are discovered both directly on PoleKnig search cards and from hydrated book detail pages.
- Author-catalogue books are prioritised ahead of unrelated title matches for broad surname searches, then existing narration grouping/deduplication is applied.
- Existing hydrated metadata is reused to avoid unnecessary duplicate book-detail requests.
- Added regression coverage for a PoleKnig author whose books span multiple author-catalogue pages.

## 4.11.1

- PoleKnig: manual book analysis now discovers alternative narration pages through the author's public catalogue.
- PoleKnig: harmless title prefixes such as “Сказ про …” and “Пьеса: Сказ про …” are grouped with the same logical work when the author matches.
- PoleKnig: rights-restricted alternative pages are filtered out of the narration selector.
- Restricted-book UI now says explicitly when no other accessible narration was found.
- Added regression coverage for author-catalogue discovery and pagination.

## 4.11.0

- Added `poleknig.com` as the third supported audiobook source.
- Added PoleKnig URL recognition for `/books/<id>` links, including scheme-less and `www` forms.
- Search now runs across audioknigi.com.ua, knigavuhe.org, and poleknig.com in parallel.
- PoleKnig search follows `p=` pagination up to the existing 100-result application ceiling, deduplicates book URLs, hydrates Title/Author/Reader metadata, and groups separate recording pages of the same logical work as narration variants.
- Added PlayerJS 19.x-compatible extraction for public inline `file`/`playlist` configs, JSON/JS arrays, compact `[Chapter]URL` lists, direct audio URLs, and external JSON/TXT playlists.
- Added a Playwright fallback that inspects only browser-visible public PlayerJS/DOM/resource URLs when the static page does not expose the playlist.
- Pages marked as removed by the rights holder are represented as restricted and are never bypassed.
- Added 6 PoleKnig regression tests; full suite passes with 238 tests.

## 4.10.4

- Completed the English event-sound pack: all 17 registered cues now have English recordings.
- Added English recordings for link pasted, book added to queue, restoring download, files already downloaded, narration changed and update available.
- English UI no longer needs the Russian sound fallback for any registered event.
- Added regression coverage for complete English event-sound localization.

## 4.10.3

- Expanded the English event-sound pack with Search complete, Queue started, Queue completed, Download resumed, and Download cancelled.
- English now covers 11 of the 17 registered event cues; untranslated events continue to use the Russian fallback.
- Added regression coverage to ensure the newly supplied English assets are selected for the matching events.

## 4.10.2

- Added language-aware event-sound lookup with per-language overrides and Russian fallback.
- Added the supplied English recordings for download start, download complete, error, book found, book not found, and download paused.
- Added new Russian cues for interrupted-download recovery, already-downloaded files, narration changes, and future update-available notifications.
- Recovery now announces when a resumable job is actually being restored.
- The duplicate-book dialog announces that files are already downloaded.
- Switching to another narration announces the selection before re-analysis.
- `update_available` is registered as a sound event but is intentionally not auto-triggered because the application does not yet contain an update checker.

## 4.10.1

- Добавлены 10 новых голосовых подсказок: вставка ссылки, результат поиска, книга найдена/не найдена, очередь, пауза, продолжение, отмена и добавление в очередь.
- Очередь получила собственные звуки запуска/завершения вместо звуков одиночной загрузки.
- Пауза и продолжение озвучиваются по фактическому состоянию очереди.
- Все 13 звуков управляются общим переключателем и отдельной громкостью в настройках.

## 4.10.0

- Added the three supplied application event sounds: download started/in progress, download completed, and error.
- Event sounds play one-shot; they are never looped during a long download.
- Added a dedicated `EventSoundManager` that uses a regular pygame mixer channel, while the audiobook preview continues to use `pygame.mixer.music`.
- Added Settings → **Звуки программы** with enable/disable, 0–100% volume, and a preview button.
- Single-book/part/full-MP3 downloads play start + success/error cues; queue mode plays one start cue and one final success/error cue for the whole queue.
- Unexpected Tk/background-thread failures also use the supplied error cue when event sounds are enabled.
- Event sound files are bundled under `assets/sounds`; the existing PyInstaller `--add-data assets;assets` rule includes them automatically.
- Added regression tests for bundled sound assets, dedicated mixer-channel playback, disabled mode, and success/error worker events.

## 4.9.9

- Fixed `audioknigi.com.ua` reader metadata leaking the following `Жанр:` label into the **Чтец** search column.
- Opening a missing historical/book folder no longer silently recreates an empty directory; only the configured output root is created on demand.
- Search narration variants are cloned before attaching to an analyzed book, so selecting/marking a variant cannot mutate the reusable search cache.
- Saved/restored window geometry is validated against Tk's current virtual desktop and stale coordinates from a disconnected monitor are clamped back on-screen.
- Native width compatibility accepts values such as `150px` and safely falls back to automatic width for malformed strings instead of passing them to Tcl.
- Audited reported truncations in `player.py`, `ui_kit.py`, and `settings_tab.py`; the complete archive compiles and those SyntaxError reports are false positives.

## 4.9.8

- Fixed queue pause button text not returning to `ПАУЗА` after queue completion/cancellation.
- Search relevance now recognises `-`, `–`, and `—` separators consistently.
- History no longer writes `null` for optional book metadata when an empty value is expected.
- Queue/history cover pipeline now accepts an existing `PIL.Image.Image` payload.
- Easy-mode Drag-and-Drop now targets the visible drag hint instead of an unmapped compatibility label.
- Added a small wraplength guard for quality cards and safer timer-owner cleanup.
- Audited reported source truncations, tray lock, CustomTkinter dependency, popup-menu grab, and Canvas line concerns; those reports do not reproduce in the complete project.

## 4.9.7
- Audited the reported source issues against the complete 4.9.6 archive; truncated-source SyntaxError reports were confirmed as false positives.
- Hardened runtime option capture for partial/destroyed Tk variable state.
- Cleared stale completion cover art when Pillow or cover data is unavailable.
- Knigavuhe BookController parsing now extracts only the first JS argument and lets `json.loads` decode valid escaped slashes.
- Hardened old/new Knigavuhe narration parsing and search-card semantic tag handling.
- Added scheme-less supported URL normalization, including `m.knigavuhe.org/...`.
- Localized the first-run welcome and Help Center for RU/UK/DE/EN.
- `SearchResult` now keeps the same mapping compatibility as the other data models.
- Image caches self-initialize in the visual mixin; recovery normalization no longer relies on exceptions for normal control flow.
- Removed an unused Knigavuhe parser wrapper/import.
- Added 9 targeted regression tests for the audit fixes.

## 4.9.6
- `audioknigi.com.ua`: every search result is now hydrated from its book page, not only duplicate-recording groups, so the **Чтец** column is populated for ordinary single-voice books too.
- AudioKnigi metadata hydration runs in one shared pool (up to 8 workers), then logical Title + Author duplicates are grouped and all reader names are preserved.
- A failed detail-page request remains non-fatal: the search row is kept with the metadata already available from the search page.
- Added a regression test for a single AudioKnigi recording whose narrator must appear in the search table.

## 4.9.5
- Added an **Озвучек** column to search results for both supported sites.
- `audioknigi.com.ua`: separate pages with the same normalized Title + Author are merged into one search row while preserving all recording URLs and reader names.
- `audioknigi.com.ua`: duplicate recording pages are hydrated only when necessary to identify their readers, then exposed through the common **Озвучка** selector.
- `knigavuhe.org`: search result variant counts are enriched from the book page's current **Другие озвучки** block, so alternatives absent from search pagination are still counted.
- Fixed the current Knigavuhe new-design parser: alternative `/book/.../` anchor text is treated as the reader name, and collection stops before comments so strings such as `Отмена` cannot become a narrator.
- Knigavuhe alternatives are re-read from their own pages to normalize reader names; duplicate recordings by the same reader become `Имя — вариант 1/2`.
- Default non-template download folders include the reader/variant suffix when multiple recordings exist, preventing different narrations from sharing the same MP3/M4B files.

## 4.9.4
- `audioknigi.com.ua`: search labels in the form `Author – Title` are now split into separate **Author** and **Title** columns.
- `knigavuhe.org`: current `.bookitem` cards are parsed structurally, so genre text from the cover cannot replace the real book title.
- `knigavuhe.org`: title, author and reader are read directly from the search card; detail-page hydration remains only as a compatibility fallback.
- Knigavuhe pagination (`?page=2`, `?page=3`, ...) is followed automatically up to the application's 100-result limit (currently up to 10 pages at 10 books/page).
- Pagination pages after the first are loaded concurrently and merged in page order with canonical-URL deduplication.
- Reader-only matches are filtered using card metadata, and multiple recording URLs for the same title/author are collapsed into one logical search result; alternative recordings remain available through the book's **Озвучка** selector.

## 4.9.3
- Knigavuhe search now filters out results matched only by narrator/performer.
- Search results show Author and Reader in separate columns.
- Book-page metadata hydration distinguishes title, author and narrator.
- Knigavuhe book pages expose an accessible «Озвучка» selector when alternative recordings are available.
- Rights-restricted recordings are not bypassed; when Knigavuhe exposes other recordings, the app shows those alternatives instead of a dead end.

## 4.9.2

- Исправлено фактическое отображение названий Knigavuhe в поиске: жанры вроде «Биографии», «Для детей» и «Аудиоспектакли» больше не используются как название книги.
- После получения канонических `/book/.../` URL названия подтверждаются по `<title>` соответствующей страницы книги.
- Страницы книг проверяются параллельно (до 6 запросов), порядок результатов сохраняется; сбой одной страницы не ломает общий поиск.
- Добавлен regression-тест для ситуации со скриншота: `/book/leonid-filatov/` должен отображаться как «Леонид Филатов», а не как жанр.

## 4.9.1

- Исправлен парсер результатов поиска `knigavuhe.org`: жанры и служебные ссылки на комментарии больше не попадают в столбцы названия/URL.
- Ссылки результатов Knigavuhe канонизируются до `https://knigavuhe.org/book/<slug>/` без `#comments_block` и tracking-параметров.
- HTML-парсер карточек использует стек ссылок и корректно отделяет название книги от вложенных ссылок жанров, авторов и исполнителей.
- Добавлены regression-тесты для реальной выдачи Knigavuhe; полный набор: 175 passed.

## 4.9.0
- Добавлен второй источник: knigavuhe.org.
- Общий поиск теперь выполняется по audioknigi.com.ua и knigavuhe.org.
- Поддержан разбор BookController JSON: авторы, чтецы, обложка и плейлист.
- Поддержан резервный merged_playlist для повторной загрузки главы при сбое основного URL.
- Ссылки knigavuhe.org работают в главном поле, очереди, буфере обмена и Drag-and-Drop.
- Ограниченные правообладателем страницы не обходятся и показывают понятное сообщение.

## 4.8.22

- Re-verified that the reported source concatenations / `ui_kit.py` truncation are false positives; the shipped Python modules compile normally.
- Kept the official Prismatoid runtime import from `prism` and added a compatibility fallback to `prismatoid` for repackaged/future distributions.
- Made the accessibility fallback tolerant of CTk wrapper class-name suffixes instead of relying on an exact hard-coded class-name set.
- Hardened the process-wide Tk DPI baseline with a physical-DPI fallback and sanity bounds.
- Fixed scale minimum sizing on small/remote displays: even at 200%, the application no longer requests a minimum window larger than the usable screen.
- Made the legacy `normalize_audio_var` a derived mirror of the canonical `normalization_mode_var`, preventing `off` / `single` / `two_pass` state drift.
- Extended unfinished-download source discovery to `_repair_source*` and common audio container suffixes, and cached per-directory final-file checks to avoid repeated `iterdir()` calls.
- Rewrote the tray notification queue trim as explicit slice assignment while preserving list identity.
- Added `tests/test_audit_4822.py`.

## 4.8.21

- Fact-checked the new audit: no source truncation exists, Prismatoid still correctly imports as `prism`, accessibility polling already cancels its Tk timers, and `single` normalization is implemented by the downloader.
- Added `safe_normalization_mode()` and applied it to app startup, settings capture/save, queue snapshots/restores, resume restoration and FFmpeg processing.
- Added a resilient `_focus_easy_url_entry()` onboarding helper and made `EasyHome` expose the same field on both component and app compatibility surfaces.
- Made scale typography refresh explicitly tolerate an unbuilt `EasyHome`.
- Prevented malformed cover payload objects from collapsing to the same blank cache digest.
- Added a Settings trace registry that remembers the real variable/trace owner across rebuilds and partial legacy metadata loss; removed duplicate folder-template variable setup.
- Canonicalized Tk Canvas scrollregion comparisons through `splitlist()`.
- Hardened recursion-safe destroy wrappers for explicit-owner calls without adding `<Destroy>` bindings; retained the old tooltip destroy helper only for compatibility.
- Made player tick rescheduling explicit and no-op-safe for non-Tk mixin test hosts.
- Added `tests/test_audit_4821.py`.

## 4.8.20

- Verified the reported `context_download_part()` / `CTkTabview.add()` truncations are false positives; the shipped sources compile completely.
- Renamed transfer metrics to `speed_bytes_per_sec` to match the downloader's actual byte-rate semantics while preserving MiB/s display.
- Replaced the hard-coded 16 MiB Range threshold with a persistent `segment_threshold_mb` setting and an Advanced Settings selector (4/8/16/32/64 MiB).
- Made queue startup atomic: duplicate Start / Retry calls cannot launch parallel workers; a generation token prevents stale workers from clearing a newer run state.
- Queue status callbacks now target the stable `QueueItem` object rather than a fragile list index, and final completion counts are read under the queue lock.
- Priority toggling now restores a book to its previous queue position when priority is removed.
- The embedded player now updates the file label to `Сейчас играет: ...` when playback starts from the track tree.
- Closing the first-run wizard now means “skip onboarding” and persists `first_run_complete`, so it does not reappear on the next launch.
- Cover-cache hashing now handles objects exposing `tobytes()` and generic payloads instead of silently collapsing to an empty digest.
- `CTkTextbox` copy/cut checks for a real selection before touching `sel.first/sel.last`.
- Replaced tab-level `<Destroy>` event bindings with deterministic `destroy()` lifecycle wrappers. This preserves tooltip/trace cleanup while fixing a reproduced Tk/Python recursion failure during complete widget-tree teardown.
- Added `tests/test_audit_4820.py` and updated lifecycle regressions.

## 4.8.19

- Verified the reported `ActionsMixin`/`app.py`/`SearchMixin` EOF findings are truncated-source false positives; the package compiles successfully.
- Verified `_update_bandwidth_label()`, `AudioKnigiApp.t()`, `_player_position_key()`, `_player_select_current()`, and `_strip_ctk_kwargs()` exist in the composed application.
- Accessibility polling now tracks all Tk `after()` IDs and cancels them during shutdown before the root is destroyed.
- Main, History, and EasyHome now explicitly dispose tooltip resources on container teardown; EasyHome also cancels its pending responsive-layout callback.
- History double-click now requires a concrete row under the pointer and selects that row before opening its folder.
- EasyHome application-owned status variables now use the shared `ensure_app_string_var()` lifecycle helper.
- Settings rebuilds first dispose old traces/autosave timers, secret fields use portable `*` masking, and hotkey wraplength is updated only after meaningful width changes.
- Queue drag clamps above the first row and below the last row instead of dropping the visual target.
- The tray option is visibly disabled when the current platform/backend cannot support tray mode.
- Search relevance now prefers the shorter label when phrase/token relevance is otherwise equal, while parser cleanup removes artificial spaces before punctuation.
- Added `tests/test_audit_4819.py`; 132 pytest tests pass in the main isolated run, the two historically Tcl-pollution-sensitive tests pass separately, and all 27 script-style smoke/audit modules pass in fresh processes.

## 4.8.18

- Verified the reported `ActionsMixin` and `SearchMixin` EOF/SyntaxError findings are truncated-source false positives; both modules compile completely.
- Added `ActionsMixin._tr()` fallback and localized duplicate-book choice hints in RU/UK/DE/EN.
- Added warnings for i18n format-parameter mistakes while preserving non-fatal UI behavior.
- Added deep history validation/sanitization and validate-before-write backup restore semantics.
- Prevented empty history folders from accidentally adopting a `cover.jpg` from the process working directory.
- Queued tray notifications while a native icon generation is starting/restarting.
- Explicitly disposed Settings tooltips at tab teardown and centralized guarded immediate saves for dropdown settings.
- UI scale selection now applies immediately while keeping the Apply button as an explicit fallback.
- Removed the native-Tk width conversion cliff at 15/16 and made Linux edit shortcuts prefer logical keysyms before Cyrillic/physical fallbacks.
- Simplified search tokenization and history-cover cache identity work; moved `LANGUAGES` to a normal module import.
- Added `tests/test_audit_4818.py`; 131/131 collected pytest tests plus 27 script-style smoke modules pass in fresh Tk/Xvfb processes.

## 4.8.17

- Centralized application-owned `StringVar` lifecycle handling in `ui_kit.ensure_app_string_var()` and reused it from Settings, Queue, and Search tabs.
- The shared helper validates stale Tcl variables, prefers the application interpreter, falls back safely in lightweight tests, and never silently returns `None`.
- Removed duplicate per-tab variable bootstrap logic and dead `_existing_*_var` locals.
- Re-verified that Settings hotkey help already resizes on `<Configure>`, Queue/Search already dispose tooltips on `<Destroy>`, and queue row DnD handlers are bound without additive duplication.
- Made simple-mode quality-card descriptions wrap to their live card width, fixing a pre-existing 200% DPI squeeze detected by the full UI regression suite.
- 120 tests pass across fresh Tk/Xvfb groups.

## 4.8.16

- Verified the reported `ActionsMixin`/`ui_kit.py` source truncations are false positives; the shipped files compile completely and `AudioKnigiApp.t()` exists.
- Kept the correct Prismatoid runtime import `from prism import ...`; current upstream packaging builds the Python wheel from `bindings/py/prism/prism`.
- Added an SDL/pygame startup grace window so a transient `get_busy() == False` immediately after play/unpause/seek cannot falsely stop the embedded player.
- Made lazy queue-lock creation race-safe for standalone mixin hosts and gave queue runtime snapshots safe defaults when partial hosts omit runtime attributes.
- Added native support for CustomTkinter-style `(light_color, dark_color)` pairs throughout theme color resolution.
- Preserved an explicit year value of `0` in template substitution instead of treating it as empty.
- Normalized Linux wheel scrolling to one unit per wheel notch, matching Windows behavior.
- Hardened Queue/Search tab StringVar reuse against stale Tcl variables, removed additive duplicate drag bindings, and added explicit tooltip cleanup for tab rebuilds.
- Added explicit `Tooltip.dispose()` without reintroducing per-widget `<Destroy>` callbacks that previously caused Python 3.14/Tk recursion.
- Made the Settings hotkey-help wrap length responsive to the actual scrollable-page width instead of a fixed 980 px.
- Added 4.8.16 regression coverage; all 117 collected tests pass when Tk-heavy groups run in fresh Xvfb/Tcl processes.

## 4.8.15

- Verified `actions.py`, `app.py`, and `ui_kit.py` are complete and compile; the reported EOF/SyntaxError findings were truncated-source false positives.
- Kept the correct Prismatoid runtime import `from prism import ...`; upstream packages the Python binding from `bindings/py/prism/prism`.
- Restored `runtime_output_mode` after isolated context-menu MP3 downloads so M4B/Both settings do not leak across operations.
- Made completion UI tolerant of easy-mode widgets being absent during rebuild/teardown.
- Seeking while paused now reloads at the requested offset and re-pauses the decoder, keeping audio and UI position synchronized.
- M4B/M4A/AAC are opened by the system player instead of being passed to SDL_mixer/pygame.
- Localized the first-run M4B switch for RU/UK/DE/EN.
- Hardened unfinished-download indicator updates against UI teardown.
- Added `CTkOptionMenu.configure(variable=...)`, `CTkSwitch.select/deselect/toggle`, `CTkProgressBar.get`, `CTkTabview.delete`, and `CTkScrollableFrame` geometry-info proxies.
- Expanded ignored CustomTkinter-only compatibility arguments.
- Removed the recurring 500 ms descendant scan from scrollable frames; newly created CTk-compatible children notify their nearest scrollable ancestor instead.
- Smoothed macOS small-delta trackpad scrolling and prevented Command-key shortcuts from polluting the custom Entry undo stack.
- Tooltips now hide on Unmap and refuse to show for unmapped/destroyed owners without reintroducing the old Destroy-recursion bug.
- `set_button_active()` now restores a button's original inactive style instead of always forcing the default style.
- Added 4.8.15 regression coverage; full suite: 104 passed.

## 4.8.14
- Подтверждено, что `AudioKnigiApp.t()` существует, `app.py` и `ui_kit.py` не оборваны, а `apply_tree_zebra()` присутствует; сообщения о соответствующих `SyntaxError`/`AttributeError` не относятся к фактической 4.8.13.
- `_save_settings()` и runtime-снимок параметров устойчивы к пустым, дробным и повреждённым числовым Tk-значениям; `on_bandwidth_slider()` не падает, если `DoubleVar.get()` временно выдаёт `TclError`.
- Исправлена семантика `tk scaling`: пользовательский процент умножается на исходный DPI Tk, а исходный DPI фиксируется один раз на процесс, поэтому повторное создание окна не накапливает масштаб. Заголовок и простой dashboard дополнительно адаптируются на 150–200%.
- `ScreenReaderBridge` синхронизирует `backend/context` через `RLock`; обычные `tk.Entry`, `tk.Scale`, `tk.Checkbutton` и `tk.Radiobutton` теперь отдают значение/состояние, а нативная регистрация Tk 9.1 умеет находить путь внутри wrapper-виджетов.
- Буфер обмена и действия с последней папкой используют безопасные `getattr`; формат номера части устойчив к строковым индексам.
- Resume-манифест принимает `selected_indices=None`; история принимает произвольные `Mapping`; очередь безопасно создаёт запись даже при частично построенном UI.
- Шаблоны понимают строковый индекс трека и не удваивают целевое расширение; `sanitize_log_text()` сохраняет `0` и `False`.
- Мини-плеер не планирует следующий `after()` после уничтожения окна, не перетягивает ползунок во время ручной перемотки и использует позиционные аргументы `pygame.mixer.music.play()` для более широкой совместимости.
- `plyer>=2.1.0` добавлен в зависимости для уведомлений Linux/macOS; threaded pystray отключён на macOS, где Cocoa требует главный поток.
- `CTkTabview.set()` безопасно игнорирует неизвестную вкладку; cleanup `SettingsTab` принимает и Python-widget, и Tcl-path события уничтожения.
- Подтверждено по официальному исходному дереву Prismatoid: Python-модуль называется `prism`, поэтому импорт `from prism import BackendId, Context` оставлен без изменения.
- Добавлен `tests/test_audit_4814.py`; полный набор проходит 89 тестов.

## 4.8.13
- Добавлено отложенное автосохранение текстовых настроек: шаблон папки, шаблон имени трека, URL/API key/Library ID Audiobookshelf сохраняются примерно через 450 мс после окончания ввода.
- `_ensure_string_var()` больше не возвращает `None` при ошибке создания Tk-переменной: используется root-интерпретатор приложения, затем безопасный fallback на frame; при полном сбое выдаётся явная ошибка вместо тихой потери `textvariable`.
- Friendly-переменные `SettingsTab.speed_var` и `output_friendly_var` создаются на Tcl-интерпретаторе корневого приложения, сохраняя локальную область владения вкладки.
- Плашка очереди «Перетащи сюда…» получила явное accessibility-имя/описание и tooltip. Подтверждено тестом, что централизованный `DragDropMixin` регистрирует её через `drop_target_register()` и `<<Drop>>` после построения всех вкладок.
- Двойной щелчок в результатах поиска теперь сначала определяет строку под курсором, делает её активным выделением и только затем открывает книгу; пустая область/заголовок остаются no-op.
- Подтверждено: штатное закрытие и раньше вызывало `_save_settings()`, `use_selected_search_result()` уже был защищён от пустого выделения, а DnD-плашка очереди уже была реальной целью через централизованную регистрацию.
- Добавлен `tests/test_audit_4813.py`; 70 регрессионных тестов проходят в изолированных Tk/Xvfb-группах.

## 4.8.12
- Fixed late accessibility naming so widgets auto-scanned by `_walk()` still update Tk 9.1+ native accessible names when an explicit semantic label is registered later.
- Removed the synchronous tray-thread `join()` from `TrayManager.hide()`; backend retirement and waiting now stay off the Tk UI thread.
- Hardened history insertion to accept both typed `Book` models and mapping/dict records without `AttributeError`.
- Normalized Tk's `widget.configure({...})` dictionary form before filtering legacy CTk aliases in Frame/Label/Button/Entry/Textbox/AccessibleLabel and related controls.
- Added Linux X11/XKB physical keycode handling for Ctrl+A/C/V/X/Y/Z so edit shortcuts continue to work under Cyrillic layouts, with keysym fallback for unusual backends.
- Improved `_parent_bg()` for ttk parents such as `Notebook` by resolving the active ttk style background instead of falling back to a hard-coded surface color.
- Removed the unused `_theme_background(..., fallback_panel=...)` parameter.
- Added audit/regression coverage for the reported 4.8.11 findings.

## 4.8.11
- Усилена потокобезопасность обновления столбцов `Начало / Конец / Длительность`: `_refresh_book_timing_ui()` теперь сам определяет поток и отправляет любые операции `Treeview` в главный Tk-поток через event bus.
- Обработчик автоподстановки ссылки использует безопасный `getattr(..., None)` для `_clipboard_offer_after` поверх существующей ранней инициализации атрибута.
- `continue_unfinished()` больше не предполагает, что все Tk-переменные и вкладки уже созданы: значения восстановления задаются best-effort через безопасный setter, а частично построенный UI не падает с `AttributeError`/`TclError`.
- При восстановлении нескольких книг `resume_selected_indices` явно очищается, чтобы выбранные части предыдущего одиночного восстановления не могли повлиять на последующий ручной анализ.
- Переключение на вкладки при восстановлении использует логический селектор с безопасным fallback, совместимый с будущей локализацией названий вкладок.
- Повторно подтверждено регрессионным тестом: `_main_download_worker()` в 4.8.10 уже имел `except Exception` и `finally`, поэтому при сетевой/дисковой ошибке `busy` гарантированно сбрасывается.
- Повторно подтверждено: `ui_kit.py` полностью компилируется; сообщения об оборванных методах `AccessibleLabel` относятся не к содержимому релизного архива 4.8.10.

## 4.8.10
- Исправлена нативная регистрация Drag-and-Drop для обычного `tk.Tk`: после `TkinterDnD.require()` методы `drop_target_register`, `drop_target_unregister` и `dnd_bind` теперь подключаются из `DnDWrapper` к обычным Tk/ttk-виджетам. Ошибка `'_tkinter.tkapp' object has no attribute 'drop_target_register'` больше не должна возникать при установленном `tkinterdnd2`.
- Если ни одну DnD-цель зарегистрировать не удалось, интерфейс честно помечает Drag-and-Drop недоступным и пишет одну понятную диагностическую строку вместо повторяющихся ошибок по каждому элементу.
- Очередь защищена от рассинхронизированных Treeview iid: перемещение вверх/вниз, приоритет и пауза книги проверяют индекс внутри блокировки перед обращением к `queue_items`.
- `MappingDataclass` получил явный `__slots__ = ()`; `Track`, `Book` и `QueueItem` с `@dataclass(slots=True)` больше не наследуют ненужный `__dict__`.
- Восстановление нескольких незавершённых книг нормализует `selected_indices` в уникальный список целых индексов; некорректные значения из JSON отбрасываются.
- Сравнение директорий незавершённых загрузок на Windows нормализует регистр и разделители, чтобы `C:\...` и `c:\...` не создавали ложные orphan-файлы.
- Fallback `StringVar` вкладки настроек принадлежит главному приложению/Tcl-интерпретатору; существующая переменная дополнительно проверяется вызовом `get()` перед повторным использованием.
- `CTkScrollableFrame` больше не перехватывает колесо мыши у вложенных `Text`, `Treeview`, `Listbox` и `Canvas`; обычные дочерние элементы по-прежнему прокручивают внешнюю страницу.
- `set_appearance_mode()` сразу обновляет внутреннее состояние палитры `_CURRENT_DARK`, поэтому новые окна/подсказки получают правильную тему ещё до следующего полного style-refresh.
- Конвертация исторических pixel-width принимает дробные строки вида `"120.5"` через `int(float(...))`; `CTkOptionMenu` также безопасно обрабатывает такую ширину.
- Горячие клавиши вкладок используют логические ключи `book/search/queue/history/settings`, а не напрямую видимые русские подписи, что готовит переключение вкладок к локализации.
- Быстрый `tray hide() -> show()` больше не теряет запрос показа: повторное создание значка откладывается до полного завершения предыдущего native loop, без запуска двух `pystray.Icon` одновременно.
- Убрано лишнее двойное присваивание подписи файла при восстановлении позиции мини-плеера.
- `PhotoImage` обложек и фирменных изображений теперь создаются с явным `master=self`, что предотвращает привязку к уже уничтоженному Tcl-интерпретатору при пересоздании приложения/тестах.
- Повторно подтверждено: `_clipboard_offer_after`, `_last_clipboard_offer`, `last_completed_folder` и `speed_history` инициализируются до использования; ID3-ошибки уже логируются; `_analysis_worker` использует runtime-снимок каталога/формата вместо чтения Tk variables из worker-потока; `ui_kit.py` не оборван и компилируется полностью.

## 4.8.9
- Исправлен PowerShell WinRT fallback системных уведомлений: `XmlDocument` теперь создаётся с правильным namespace `Windows.Data.Xml.Dom`, а неудачный PowerShell-вызов больше не считается успешным уведомлением.
- Мини-плеер теперь отключает «Пауза» и «Стоп», когда воспроизведение остановлено или естественно завершено; кнопки снова активируются только после запуска аудио.
- `LibraryVisualMixin._payload_key` корректно хэширует как bytes-like данные, так и строки UTF-8.
- Счётчик шагов первого запуска переведён в i18n для RU/UK/DE/EN.
- `MappingDataclass` приведён к `MutableMapping`, соответствуя реализованному `__setitem__`.
- Неизвестные теги пользовательских шаблонов сохраняются как текст; слэши внутри автора/названия очищаются до подстановки и больше не создают неожиданные подпапки.
- Проверка незавершённых загрузок учитывает готовые M4A/M4B/AAC/FLAC/OGG/OPUS/WAV, а восстановление нескольких книг переносит настройки шаблонов в очередь и реально применяет их при обработке.
- История устойчиво обрабатывает нечисловые Treeview iid и некорректное/пустое количество частей.
- `CTkOptionMenu.configure(command=...)` теперь безопасно заменяет callback без `TclError`; `CTkSwitch.configure(variable=...)` обновляет внутреннюю переменную.
- `CTkScrollableFrame` автоматически подключает колесо мыши и фокус к дочерним элементам, добавленным после создания страницы.
- Системный трей не создаёт второй `pystray.Icon`, пока предыдущий экземпляр ещё завершает native loop.
- Вкладка «Поиск» сохраняет ссылку `search_query_entry` и реагирует на двойной щелчок только по ячейкам результатов, не по заголовкам/разделителям.
- Тонкие настройки соединений автоматически сохраняются; выбор friendly-пресета «Максимальная» больше не превращает вручную выбранные 2/4 потока в 8.
- Drag-and-Drop очереди начинается только с ячейки строки, клики по заголовкам больше не считаются перетаскиванием.

## 4.8.8
- Полностью проверен расширенный интерфейс на вкладках «Книга», «Поиск», «Очередь», «История» и «Настройки».
- На вкладке «Поиск» добавлена видимая подпись «Результаты поиска», имена полос прокрутки и подсказки; нижняя кнопка открытия книги теперь всегда резервирует место.
- На вкладке «Книга» кнопка «Проверить файлы» переименована в «Проверить скачанные файлы» и получила точное пояснение: проверяет наличие, целостность и длительность локальных MP3, ничего не скачивает.
- Общая шкала этапов и шкала текущей операции теперь явно различены, имеют accessibility-имена и видимый процент текущей операции.
- Мини-плеер перестроен так, чтобы длинное имя файла не вытесняло транспортные кнопки; «Воспроизвести», «Пауза/Продолжить» и «Стоп» всегда доступны.
- Правая колонка управления на вкладке «Книга» стала независимо прокручиваемой, поэтому при небольшой высоте окна список частей остаётся рабочим, а все элементы управления остаются достижимыми.
- На вкладке «История» добавлены «Создать резервную копию» и «Восстановить копию» рядом с действиями библиотеки; нижняя панель больше не вытесняется таблицей.
- Вкладка «Очередь» получила устойчивую двухрядную панель управления; кнопки больше не сжимаются на 175–200% масштабе.
- Основные элементы расширенного интерфейса получили всплывающие подсказки и accessibility-имена; добавлено имя ползунку ограничения скорости.
- Геометрический аудит 1080×760 в тёмной и светлой теме на 100/125/150/175/200%: 0 выходов за границы и 0 обрезанных текстовых элементов.
- Сохранены исправления Python 3.14 RecursionError из 4.8.7 и временных столбцов из 4.8.6.

## 4.8.7
- Найдена и устранена воспроизводимая причина `RecursionError`: обработчики `<Destroy>` у всплывающих подсказок больше не вызывают Tk-команды во время массового уничтожения дерева интерфейса.
- Исправлена рекурсия Tkinter на Python 3.14.3 при вложенной обработке Configure/Focus/Map событий.
- Убраны `update_idletasks()` из обработчиков масштаба, адаптивной разметки и буфера обмена.
- Адаптивная разметка получила debounce, защиту от повторного входа и гистерезис.
- Усилена защита `<Configure>` у прокручиваемого контейнера.
- Обработчик `RecursionError` больше не открывает вложенный modal messagebox.
- Сохранены исправления столбцов времени из 4.8.6.

## 4.8.6

- Fixed `Начало`, `Конец`, and `Длительность` staying as `—` when a PlayerJS playlist supplies one MP3 per chapter without source `start`/`end` coordinates.
- Playlist timing parser now accepts numeric seconds plus `MM:SS` / `HH:MM:SS` strings from `duration`, `length`, or `time` fields.
- Existing downloaded MP3 files now contribute their measured `actual_duration` to the visible chapter timeline and total book duration without overwriting FFmpeg source-cut coordinates.
- Missing durations for unique remote chapter files are resolved best-effort through `ffprobe`; failures remain non-fatal.
- Timing/status cells refresh while verified chapters become available during a download.
- M4B preview, M4B chapter metadata, sidecars, disk estimates, and the simple completion card now use the best known duration instead of treating unknown playlist duration as zero.
- Added regression coverage for playlist clock parsing, local measured-duration fallback, safe remote probing, live Treeview refresh, and cumulative chapter timing.

## 4.8.5

- Added Ctrl+Z undo and Ctrl+Y / Ctrl+Shift+Z redo to native Entry/Text editing without reintroducing the Python 3.14 recursive Tk event bindings; Windows virtual-key handling keeps these shortcuts working on Russian/Ukrainian layouts.
- Fixed Help and other child windows opening with a platform-white background in dark mode. `CTkToplevel` now applies the active theme before its first paint and follows live theme changes.
- Themed context menus and visual tooltips, and moved the M4B preview to the same themed top-level window class.
- Reworked the simple dashboard for narrow/high-scale layouts: the page is vertically scrollable and automatically stacks the sidebar below the main content at 175–200% or whenever horizontal room is insufficient.
- Re-audited simple + advanced UI at 100/125/150/175/200%: no visible child overflows or squeezed text controls were detected in the automated geometry audit.
- Added regression tests for Help dark/light surfaces, Ctrl+Z/Ctrl+Y, responsive simple-layout clipping, and current ttk field/table colors.

## 4.8.4

- Fixed the Python 3.14/Tkinter `RecursionError` introduced by overlapping clipboard key bindings; text fields now use one non-recursive physical-key handler for Ctrl+A/C/V/X plus the standard Insert shortcuts.
- Added a Windows virtual-key fallback so Ctrl+C/Ctrl+V/Ctrl+X/Ctrl+A keep working with Russian and Ukrainian keyboard layouts without generating replacement Tk events.
- Hardened the Tk callback exception handler so a recursion failure cannot recursively crash the crash-report builder and hide the original error.
- Reworked legacy CustomTkinter pixel-width conversion, including small 24–28 px values that native Tk had interpreted as 24–28 text columns and that squeezed neighbouring controls.
- Removed fixed legacy button widths and let native ttk buttons size to their captions; widened accessibility layouts at 150–200% when screen space permits and made the header mode switcher reserve its width first.
- Refreshed native Tk fonts after UI-scale changes, eliminating stale requested sizes that caused text to be clipped after changing scaling.
- Completed live dark/light theme propagation for native Frame, Label, Entry, Text, Canvas, Treeview, combobox and scrollbar surfaces; changing theme no longer leaves black islands on a light background.
- Added regression checks for clipboard handling, small-width conversion, live theme switching, layout sizing and launch stability.

## 4.8.3

- Restored conventional keyboard editing in every native text field: Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+Insert and Shift+Insert; added a Windows virtual-key fallback for Russian/Ukrainian keyboard layouts.
- Removed the main URL field's special Ctrl+V interception, so keyboard paste edits the field normally instead of invoking the dedicated “ВСТАВИТЬ” workflow.
- Fixed the native ttk compatibility layer so historical pixel widths are converted correctly for accessible labels; settings labels no longer become hundreds of characters wide and push adjacent controls off-screen.
- Made button widths text-safe so long Russian captions are never truncated by a too-small legacy pixel width.
- Made combobox widths large enough for their longest displayed option.
- Added horizontal and vertical scrollbars to Search, Queue and History tables.
- Split the crowded Queue action strip into two rows so controls remain visible at the minimum supported window width.
- Added regression coverage for clipboard shortcuts, text-safe sizing and the minimum-width interface layout.

## 4.8.2

- Replaced the obsolete DLE-style `index.php?do=search&subaction=search&story=...` request with the website's current `GET /search?text=...` contract.
- Added query-aware filtering so unrelated `/audio-*` links from popular/recommended/sidebar blocks are not returned as search hits.
- Search accepts author surnames and multi-word author/title queries; matching is case-insensitive, `ё/е` tolerant, and word-order tolerant for multi-word queries.
- Added a tolerant HTML parser that reads visible link text, `title`/`aria-label`, and image `alt`, merges duplicate links for the same book, and strips descriptive `Слушать онлайн аудиокниги ...` prefixes.
- Search minimum length is now 3 characters, matching the site's `minlength=3` form.
- Added screen-reader-friendly search guidance and `tests/test_search_accuracy_482.py`.

## 4.8.1

- Verified that the shipped 4.8.0 `app.py` and `easy_home.py` are complete and compile; reported truncations were artifacts of clipped source excerpts.
- Verified `AudioKnigiApp.t()` exists and `on_bandwidth_slider(self, _value=None)` accepts the value passed by native ttk Scale widgets.
- Replaced the leftover CustomTkinter-style focus-border fallback in `EasyHome._keyboardize()` with pure native ttk focus behavior.
- Preserved `placeholder_text` as semantic metadata without ever injecting it into the Entry/StringVar value.
- Added persistent visible “Пример: …” helper text for the book URL and Audiobookshelf server fields; JAWS/NVDA descriptions can announce the same example.
- Restored scrolling for the long Settings page with a passive Canvas viewport while keeping every interactive child a real Tk/ttk control; keyboard focus automatically scrolls the focused setting into view.
- Added `tests/test_audit_481.py` for source completeness, translation helper, slider callback, placeholder semantics, native focus behavior and scroll/focus-follow behavior.

## 4.8.0

- Replaced the runtime CustomTkinter widget layer with native Tk/ttk controls and visual containers; the historical `CTk*` compatibility names now resolve to standard Tk/ttk widgets rather than Canvas-based controls.
- Added `ttkbootstrap>=2.2.0,<3` as the modern theme engine and updated PyInstaller collection accordingly; the app falls back to native `clam` styling if the package cannot be imported.
- Introduced a compact Windows-style palette with WCAG-AA text contrast, Segoe UI typography, larger control padding and visible focus rings.
- Modernized Treeview density and headings, added alternating row backgrounds to book parts, search, queue and library, and retained textual status labels so state is never conveyed by color alone.
- Kept every actionable button text-named; icons remain supplemental rather than icon-only controls.
- Programmatic tab changes now move focus into the first logical native control in the selected tab.
- Native PhotoImage/Pillow rendering now handles brand/cover images without relying on CustomTkinter image objects.
- Added `tests/test_modern_accessible_ui.py` to enforce the no-CustomTkinter runtime, native interactive controls, core contrast ratios, text-named buttons and Treeview density/zebra rules.

## 4.7.10

- Hardened `SettingsTab` against partial initialization: `segment_count_var` and `output_mode_var` are repaired with safe `StringVar` fallbacks when missing.
- `_speed_changed()` now tolerates a missing settings persistence callback instead of raising `AttributeError`.
- Settings traces now have an explicit lifecycle: old traces are removed on rebuild and current traces are detached when the settings frame is destroyed.
- Added regression coverage for complete `app.py`, `AudioKnigiApp.t()`, settings trace cleanup, and partial settings hosts.
- Confirmed that the reported truncated `app.py` and missing `self.t()` were artifacts of incomplete source excerpts, not defects in the shipped 4.7.9 ZIP.

## 4.7.9

- Fixed the auto-download analysis-to-download handoff so the UI remains busy until the queued download or duplicate dialog takes ownership.
- Auto-analysis failures now always release the busy state, even when automatic download was requested.
- Duplicate-book dialog explicitly releases busy state on Open/Cancel and transfers it only when a download worker actually starts.
- `download_selected()` now returns a boolean start result so handoff code can safely resolve failed preflight/no-selection cases.
- Mode-button highlighting now uses an adaptive helper that supports current native `ttk.Button` wrappers and future real CustomTkinter buttons.
- `_book_outputs_complete()` no longer evaluates a Tk `StringVar` from a worker thread through an eager `getattr` default.
- Added `tests/test_audit_479.py` and included it in CI/release workflows.

## 4.7.8

- Verified the reported `core.py` truncation is not present in the shipped ZIP; the module compiles. Tightened bundled-tool probing from `exists()` to `is_file()` so a same-named directory cannot be treated as FFmpeg/FFprobe.
- Confirmed the 4.7.6+ `CTkButton` compatibility class is intentionally a native `ttk.Button`, so `style=` on the Simple/Advanced buttons is valid.
- Added a future-proof CustomTkinter interactive-class fallback to the accessibility manager while keeping the current universal UI natively ttk.
- Decoupled track Treeview row IDs from `Track.index`; zero-based, sparse or duplicated source indices can no longer select/toggle the wrong list element.
- Player position saving now self-initializes `player_positions` for alternate/minimal host objects instead of assuming the main app constructor already did so.
- Individual queue pause now remembers and restores the prior status, including `Ожидает повтор`.
- Resume manifests safely accept `selected_indices: null` and ignore malformed individual index values.
- History rows without covers omit the Treeview `image` option instead of passing an empty image name.
- `_safe_track_index()` now accepts a direct integer track index.
- Native EasyHome controls receive `accessible_name` before the native-keyboard early return.
- Friendly output settings tolerate partial/minimal app initialization where `output_mode_var` or `_save_settings` is not yet available.
- Added `tests/test_audit_478.py` and wired it into CI/release workflows.

## 4.7.7

- Verified that `app.py` is complete and `AudioKnigiApp.t()` exists; the reported truncation/missing-method issues came from incomplete snippets, not the shipped ZIP.
- Replaced `dataclasses.asdict()` in model serialization with a field-wise safe serializer that never deep-copies Tk/PIL/native image objects from `cover_cache`.
- Explicitly handles empty cover payloads without exception-driven control flow.
- PowerShell toast fallback now constructs `XmlDocument` and `ToastNotification` directly through WinRT type literals. User text remains Base64 data and never executable PowerShell.
- Privacy log sanitizer masks both `C:\Users\Name` and `C:/Users/Name` forms of the home path.
- Interrupted queue restore now uses typed `QueueItem.url` access and synchronizes the legacy normalization BooleanVar.
- Friendly MP3/M4B selector now follows `output_mode_var` changes caused by restore/profile/runtime code.
- Speed label is safe even during partial/minimal UI initialization.
- Language callback accepts either a language code or its display name.
- Accessibility label discovery now recognizes CTkLabel-like visual labels as well as native Tk/ttk labels.
- Added `tests/test_audit_477.py` and wired it into CI/release workflows.

## 4.7.6

- Made accessibility inherent to the single interface: there is no screen-reader-mode setting or alternate UI.
- Interactive controls are always native Tk/ttk widgets even when CustomTkinter is installed; CustomTkinter remains visual-only for cards, covers and layout.
- Replaced clickable-only quality cards with real native radio buttons while preserving the visual card design and mouse-wide click target.
- Added automatic Windows NVDA/JAWS direct-output integration through Prismatoid; it only acquires NVDA/JAWS backends and never falls back to SAPI/TTS.
- Re-detects a reader started/restarted after the app, without restart or user configuration.
- Added semantic focus descriptions, checkbox/radio state, tree-row position, notebook tab selection and restrained live status announcements.
- Progress speech is throttled to 10% milestones to avoid repetitive output.
- Added runtime support for Tk 9.1 `tk accessible` when present while remaining compatible with CPython 3.14's bundled Tk 8.6.
- Added `docs/accessibility/ACCESSIBILITY.md` and `tests/test_accessibility.py`; CI/release jobs now enforce the universal-accessibility contract.

## 4.7.5

- Normalize missing book titles to `audiobook` before full-MP3/M4B filenames and Mutagen tags.
- Explicitly handle empty tuple cover payloads.
- Publish completed search-result lists on the UI thread instead of incrementally mutating shared state in the worker.
- Explicitly activate Windows Runtime toast types in the PowerShell fallback while keeping user content Base64-transported.
- Track the last valid player position so natural end-of-track clears resume state even when pygame immediately returns `-1`; unexpected early stops preserve resume state.
- Guarantee a non-empty `audiobook` fallback folder for templates.

## 4.7.4

- Made keyboard focus decoration exception-safe for dynamic CustomTkinter cards.
- Kept friendly speed presets synchronized with the advanced segment-count control and made queue/search Tk variables persistent across tab rebuilds.
- Standardized Treeview `show` values and made the track context-menu master explicit.
- Ignored child `<Unmap>` events so tab/layout changes cannot accidentally trigger tray minimization.
- Hardened metadata parsing for `html=None`; retained the verified source-mode resource path and disk helper.
- Normalized Audiobookshelf URLs without a scheme and kept the long 120-second scan timeout.
- Removed PowerShell interpolation of notification text by transporting escaped toast XML as Base64.
- Restricted MappingDataclass mapping keys to declared dataclass fields only.
- Closing the first-run wizard no longer marks setup complete.
- Made player-position lock creation, snapshots and mutations thread-safe while retaining asynchronous disk writes and synchronous shutdown flush.
- Hardened logging home-path masking and corrupted numeric setting recovery.
- Preserved a track title of `0`, hardened folder-template edge cases, fallback widget option translation, Tooltip teardown and late tray-stop behavior.
- Added `tests/test_audit_474.py` and wired it into CI/release workflows.

## 4.7.3

- Removed Book/Track/QueueItem `.get()` and subscript access from the typed runtime path; compatibility mapping access remains only for legacy callers.
- `MappingDataclass` now advertises read-only `Mapping` semantics instead of `MutableMapping`; field deletion raises `TypeError` instead of silently assigning `None`.
- Added regression coverage proving the shipped `dnd.py` is complete/compilable and HTTP session rotation survives `session.close()` failures.
- Fixed empty/directory cover paths so Pillow is never asked to open `Path("")` / a directory.
- Windows PowerShell notification fallback now uses hidden/no-window process flags.
- Increased the default Audiobookshelf library-scan timeout from 20s to 120s.
- Added queue-state `RLock`, typed QueueItem access, per-book runtime snapshots and a structural run snapshot to prevent UI/worker state races.
- Moved periodic player-position JSON writes off the Tk main thread into a single coalescing background writer; shutdown performs a synchronized final flush.
- Fixed template expansion so braces inside real book/author/track data (for example `{Remix}`) are preserved.
- Hardened template input handling for `None`/non-mapping tracks and books, and only treats extensions literally present in the template as format directives.
- Hardened tray icon creation for older Pillow versions and made each tray generation use private start/stop events so a slow old backend cannot poison a later `show()`.
- Improved ttk fallback compatibility: `CTkSwitch.get()`, CTkFrame height preservation, and owner-only tooltip `<Destroy>` handling.
- Added `tests/test_hardening.py` and wired it into CI/release workflows.

## 4.7.2

- Standardized Book/Track use in the application core on typed dataclass attribute access; legacy mapping access remains compatibility-only.
- Fixed disk-space preflight for not-yet-created target folders by checking the nearest existing parent; unknown free space no longer silently bypasses the check.
- Fixed ttk Treeview colors in `system` appearance mode by using CustomTkinter's effective Light/Dark mode.
- Made JSON persistence thread-safe and atomic with a process-wide `RLock` plus `os.replace()`.
- Disabled speed-graph spline smoothing until at least three data points exist.
- Blocked queue deletion/clearing while the queue worker is active and fixed DnD insertion-slot calculations for top-to-bottom moves.
- Kept strict slotted dataclasses intentionally; no undeclared runtime fields are written to Book/Track/QueueItem.
- Moved unfinished-download startup scanning to a daemon worker, validated output paths and bounded directory depth.
- Backup restore now reapplies audio, normalization, templates, bandwidth, integration, UI and language settings to live variables.
- First-run wizard preserves an existing pure `m4b` output mode.
- Cover caches now use stable URL/path keys and prune stale images after queue/history changes.
- Template engine safely handles missing/non-numeric track indices, target extensions and mixed Windows path separators.
- Tooltips now hide on `<Destroy>` to prevent orphan popups.
- Tray startup/shutdown is synchronized to prevent show/hide races and phantom icons.
- Added `tests/test_maintenance.py` and wired it into CI/release smoke tests.

## 4.7.1.3

- Fixed `TclError: image "pyimageN" doesn't exist` when a previous cover preview was cleared.
- CTkLabel image replacement is now image-first and text-second.
- The native Tk image slot is cleared before CTkImage replacement to recover from stale Tcl image handles after DPI/theme redraws.
- Applied the same safe image lifecycle to the completion/result cover card.
- Added a regression test that simulates a stale Tk image handle.

## 4.7.1.2

- Range segments now continue automatically when a CDN/proxy returns a capped partial 206 response (for example 3 MiB).
- Interrupted Range responses preserve already-written bytes and retry from the first missing byte.
- Added regression coverage for server-capped Range responses.

## 4.7.1.1

- Fixed delayed UI error callbacks capturing Python exception variables after the `except` block had exited.
- Fixed all five affected callbacks in analysis, download, recheck and Audiobookshelf paths.
- Added an architecture regression guard that rejects unsafe exception-variable capture inside deferred lambda bodies.

## 4.7.1

- Renamed the internal package from `audioknigi_v46` to stable `audioknigi`.
- Moved runtime version to `audioknigi.__version__` / `audioknigi/version.py`.
- Added `pyproject.toml` with dynamic version metadata.
- Standardized documentation as `README.md` and `docs/build/RELEASE_SETUP.md`.
- Moved smoke/regression scripts to version-neutral `tests/` modules.
- Routed Audiobookshelf HTTP through the shared retry-enabled session.
- Added explicit architecture tests for HTTP timeouts and GUI worker-thread rules.
- Added rotating privacy-sanitized application logs (1 MB × 3 backups).
- Bounded the last crash report and kept it privacy-sanitized.
- Added an explicit `.part` single-stream resume regression test.

## 4.7.0

- First-run wizard, listening-position resume, library covers, duplicate detection, site-structure diagnostics, Help Center, accessibility and RU/UK/DE/EN localization foundation.

