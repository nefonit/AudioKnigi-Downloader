# AudioKnigi Downloader 4.12.42 — complete review of the 2026-10-12 audit

**Reviewed source:** `Вставленный текст(20261012-183838).txt` (242 lines), against the Round 90 audit-follow-up source archive and GitHub `main` at commit `a94879ca84247c8a4c8cb710830874d5812ce7c4` before this report. The four recently edited archive files were confirmed identical to GitHub using Git blob SHA-1.

**Audit status:** All substantive claims in the uploaded report were individually classified below. There were **no new confirmed runtime defects requiring a production-code change**. Two reported duplicate JSON keys do not exist in the current file. Both allegedly missing localization messages are already translated. Several positive claims are confirmed by inspection but cannot be treated as Windows/NVDA/JAWS runtime acceptance.

## Individual claim verification

Legend: **Verified** = current source evidence or targeted test supports the claim; **Already fixed/stale** = finding describes an older revision, not the inspected one; **Observation** = cosmetic/compatibility note rather than a defect; **Windows validation needed** = the indicated code exists but real device/UIA behavior has not been proved in this environment.

| # | Finding in the supplied report | Result | Code/evidence |
|---|---|---|---|
| 1 | Python 3.12+ `SyntaxWarning` from `\(` / `\{` in POSIX regexes | **Not reproduced; claim is incorrect for the current raw-string patterns.** | `audioknigi/diagnostics/support_bundle.py`; `python -W error::SyntaxWarning -m compileall -q audioknigi` succeeded on Python 3.13.5; both expressions compile. Do not apply the proposed unvalidated character-class rewrite. |
| 2 | `typing.Mapping` in `session.py` vs `collections.abc.Mapping` elsewhere | **Observation, not a bug.** | `audioknigi/diagnostics/session.py` imports from typing and runs on supported Python; optional style-only cleanup is not worth changing runtime code in this stability pass. |
| 3 | Parked segmented workers exit when the one-shot job queue empties; errors still propagate | **Verified source control flow.** | `audioknigi/download/network.py`: parked workers return on `jobs.empty()`, failures are stored in `errors`, and raised by the coordinator. No new work is enqueued after creation. Network behavior tests passed; real network variability is not exhaustively proved. |
| 4 | Repaired shared source is moved back and reused | **Verified source control flow.** | `audioknigi/download/book_flow.py`: `replace_with_retry`, `cleanup_sources.discard`, `src = Path(original_source)`, and `repaired_sources[source_key_value] = src` follow sequentially. |
| 5 | Stream-copy failure can recover bitrate/channel arguments before re-encode | **Verified source control flow.** | `audioknigi/download/media.py`, `_split_track` and nested `make_cmd`: missing bitrate/channels are read from `_cached_probe_audio_info` on non-copy fallback. Cannot guarantee FFmpeg accepts every damaged input. |
| 6 | Duplicate key `Аудиоссылка устарела — обновляю плейлист…` | **Already fixed/stale.** | `runtime_exact.json`: key appears once. JSON parsed using an explicit duplicate-key rejecting hook. |
| 7 | Duplicate key `Проверить системный звук` | **Already fixed/stale.** | `runtime_exact.json`: key appears once; no duplicate object keys anywhere in the current file. |
| 8 | No translation for FFmpeg loudnorm first-pass statistics absence | **Already fixed/stale.** | Exact message has nonempty `en`, `de`, `uk` entries in `runtime_exact.json`; verified with runtime translator. |
| 9 | No translation for free-disk-space determination failure | **Already fixed/stale.** | Exact multiline status (plus companion plain variant) in `runtime_exact.json` in three languages; verified with runtime translator. |
| 10 | `ThreadPoolExecutor.shutdown(cancel_futures=True)` requires Python 3.9+ | **Verified, no incompatibility.** | Executing interpreter is Python 3.13.5 and supports argument; the project already uses 3.10+ typing syntax. |
| 11 | `..config.settings` relative import depends on correct package layout | **Verified.** | `audioknigi/services/download_request.py` imports `audioknigi.config.settings` successfully. Package is present. |
| 12 | Empty future collection in `_iter_completed_cancellable` | **Verified by tests.** | Both `audioknigi/providers/audioknigi_search.py` and `audioknigi/services/book_analysis_service.py` yield an empty list without errors. |
| 13 | No AB-BA inversion in `PlayerPositionStore` persistence/reload/update | **Verified for inspected methods.** | `audioknigi/services/player_position_store.py`: `_persist_latest` and `reload` lock `_persist_lock` then `_lock`; `update` releases `_lock` before persisting. This is **not** a global proof that every possible thread schedule is deadlock-free. |
| 14 | Sorting uses tuples of distinct widths depending on `field` | **Verified.** | `audioknigi/services/search_service.py`; targeted parametrized tests confirm comparable keys for `title`, `author`, `narrator`, `genre`. |
| 15 | Locale files must be placed alongside `i18n.py` under `locales/` | **Verified.** | All six named JSON catalogs are present in `audioknigi/locales/`; `i18n.py` resolves that directory. |
| 16 | `HTTPSConnection._context` is a private stdlib attribute | **Valid portability observation, no observed defect.** | `audioknigi/network_dns.py`; present in the CPython 3.13.5 runtime. Behavior on alternate Python runtimes was not verified; avoid compatibility refactoring without a reproducer. |
| 17 | The year 2026 in `brand.py` and `core.py` is a duplicate constant | **Mischaracterized.** | `brand.py` declares `COPYRIGHT_YEAR = 2026`; `core.py` only has a dated comment about browser versions, not a second copyright constant. |
| 18 | `Track`/`Book` dataclass fields and track status normalization | **Verified for the named fields.** | `audioknigi/models.py`: named fields exist; `Track.__post_init__` normalizes the status. Sweeping guarantees about *all* possible source integrations are beyond static verification. |
| 19 | Folder templates filter path traversal | **Verified for the tested metadata traversal case.** | `audioknigi/templates.py` strips `.`/`..` components and normalizes substituted values with `safe_name`. Targeted test keeps the output under the configured base directory. This is not a security proof for every crafted filesystem/symlink case. |
| 20 | Download history writes are synchronized with `HISTORY_LOCK` | **Verified for inspected save/read paths.** | `audioknigi/services/library_service.py` and `audioknigi/download_engine.py` share a `threading.RLock`, including the checked history-save path. Do not infer that no external process can ever modify the files. |
| 21 | Qt runtime audit forbids legacy frontend imports | **Verified static contract.** | `audioknigi/qt_runtime_audit.py` defines and checks both prefix lists. Frozen Windows process import graph still requires a Windows runtime audit. |
| 22 | `DownloadWorker` normalizes native cover objects before `deepcopy` | **Verified source order; GUI validation needed.** | `audioknigi/qt/workers.py`: `normalize_cover_cache` and a shallow snapshot are used before the final deep copy. No real Qt native object was created here. |
| 23 | `QueueTableWidget` uses Qt 6 drag/drop pointer position | **Verified statically; GUI validation needed.** | `audioknigi/qt/workers.py`: `event.position().y()` is present. Actual mouse interactions were not tested. |
| 24 | Windows media key pointer conversion, return tuple and 180 ms suppression | **Verified statically; Windows validation needed.** | `audioknigi/qt/media_keys.py`: `MSG.from_address(address)`, `(bool, 0)` return shapes, and `0.18`-second cross-source debounce are present. Windows hotkey delivery and native pointer correctness are not reproducible here. |
| 25 | Progress dialog guards Esc/close and hides on finish | **Verified statically; Windows/UIA validation needed.** | `audioknigi/qt/operation_dialog.py` overrides `reject`, `closeEvent`; `finish` sets `_allow_close` and uses `hide()`. Interaction with Windows screen readers remains to be tested. |
| 26 | Track checkbox model updates relevant accessibility roles | **Verified statically; screen-reader validation needed.** | `audioknigi/qt/track_model.py`: handles `Qt.CheckState`, `bool`, and 0/2; emits CheckStateRole, AccessibleTextRole and AccessibleDescriptionRole. No NVDA/JAWS test here. |
| 27 | Search results have accessible row summaries | **Verified statically; screen-reader validation needed.** | `audioknigi/qt/search_model.py`: `AccessibleDescriptionRole` assembles localized column values. Actual speech output remains unverified. |
| 28 | Theme switching preserves font and subscribes to system theme changes | **Verified statically; GUI validation needed.** | `audioknigi/qt/theme.py`: caches `app.font()`, calls `app.setFont(preserved_font)`, and hooks `colorSchemeChanged`. System theme and scaling changes need Windows testing. |

## Tests run during this review

- `python -W error::SyntaxWarning -m compileall -q audioknigi`: **PASS** (Python 3.13.5).
- `runtime_exact.json` duplicate-key rejecting parser: **PASS**, 139 unique top-level entries.
- Added `tests/integration/test_round90_report_contracts.py` with targeted source/API tests including empty futures, invalid-escape claim, locale layout, sorting, model contracts, and static Qt checks.
- Ran all available tests **excluding `tests/integration/test_accessibility.py`** in independent groups: **922 passed, 0 failed** (87 + 158 + 156 + 282 + 223 + 16). The providers group took approximately 22 seconds; it did finish normally.
- PySide6 and Windows UIA/NVDA/JAWS acceptance **not performed**; successful Python/structural tests cannot substitute for these checks.

## Conclusion and follow-ups

This report does not reveal a new confirmed bug in the currently published Round 90 production code. **No speculative runtime refactor was applied.** The already-correct locale values and the privacy-sensitive regexes were preserved unchanged.

Before release sign-off, run Qt accessibility self-tests and `run_qt_acceptance.bat` with NVDA and JAWS on Windows, including keyboard operation, drag/drop behavior, media keys, theme changes, and cancel/finish dialog behavior. Check the exact EXE hash and test the packaged build. These remain the only outstanding validation gates raised by this source review.
