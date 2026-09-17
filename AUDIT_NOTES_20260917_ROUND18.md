# Audit notes — Round 18 (2026-09-17)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND17_20260917`

## Confirmed and fixed

1. **Range fallback / Windows finalization**
   - A `RangeUnsupported` failure now removes `.segNNN`, `.segments.json` **and** stale `.assembling` before ordinary single-stream fallback.
   - Final segmented assembly uses bounded sharing-violation retries.
   - Full-MP3 target/source moves and retained-source replacement use the same bounded Windows retry helper, covering short Defender/indexer locks.

2. **Parallel duration-probe cancellation**
   - `download/probe.py` no longer blocks inside `as_completed()` waiting for the next future before observing Cancel.
   - It polls completion every 100 ms, cancels queued futures and terminates registered ffprobe subprocesses before executor shutdown.

3. **Search false positives from initials**
   - Abbreviated-name matching now accepts initials only from author/narrator person fields.
   - One-letter words in a title can no longer satisfy an unrelated first name; common Russian query conjunction/preposition noise is ignored.

4. **Support-bundle privacy precision**
   - Forward-slash UNC masking now requires a real `//server/share` shape.
   - Strings such as `// TODO` stay untouched while Windows UNC paths remain redacted.

5. **History and backup state integrity**
   - `_add_history()` checks the `save_json()` result and does not log/callback a successful history save when persistence failed.
   - `restore_backup()` snapshots current members and rolls back earlier writes if a later restored member fails, preventing partially restored player positions/settings/queue state.

6. **JSON-LD robustness**
   - Post-parse JSON traversal is iterative and cycle-defensive, avoiding Python recursion-depth failures on abnormally deep programmatic structures.

7. **Qt / Windows safety and accessibility**
   - Event-sound players detach `QAudioOutput` before `deleteLater()`.
   - Search rows now expose full `AccessibleDescriptionRole` summaries for NVDA/JAWS row navigation.
   - Media-key registration rechecks the native HWND and re-registers when the window handle changes.
   - Combo announcements fall back to a localized human label instead of speaking `objectName()`.

8. **User-state behavior**
   - Saving unrelated settings while in Easy mode no longer overwrites a custom advanced audio/normalization profile. Easy quality changes still synchronize the advanced controls through the existing signal path.
   - Explicitly cancelling analysis clears the remaining Drag-and-Drop URL batch instead of immediately starting the next queued URL.

## Reviewed but not changed

- **Peer-abort Range corruption:** not reproduced. The first worker failure is recorded under the error lock before `peer_abort_event` is set, and the coordinator raises that root error before assembly. `jobs.task_done()` is queue bookkeeping; there is no `jobs.join()` success criterion.
- **Adaptive worker parking deadlock:** `jobs.empty()` is checked before parking. Concurrency changes apply between Range tasks by design; an already-open HTTP segment is not forcibly killed merely because the target worker count fell.
- **FFmpeg `filter_complex` and special characters in source paths:** the path is passed via `-i` and is not interpolated into the filter graph.
- **Localization prefix/regex shadowing:** current `localize_runtime_text()` checks runtime regex rules before exact/prefix rules, so the reported prefix-first shadowing does not match the code.
- **`selected_indices=[]`:** intentionally means no selected parts and must fail validation; converting it to `None` would silently mean “all tracks”.
- **PoleKnig escaped quotes:** current JS-literal normalizer already tracks an `escaped` state inside quoted strings.
- **Playwright cookies/profile:** `persist_browser_session()` refreshes the HTTP-session generation, so the next `get_http_session()` rebuilds with the persisted browser profile.
- **`Track_Title` empty fallback:** retained as the established naming behavior; previous regressions explicitly prevent falling back to a duplicate numeric title.
- **30-second proxy half-close bound:** retained to allow a client FIN while the upstream is still finishing a response; eliminating it could truncate valid transfers.
- **Forced-exit deadline:** remains a last-resort bounded shutdown policy after cooperative cancellation/persistence; removing it would reintroduce invisible hung processes.
- **Queue drop-to-end:** after removing the source row, inserting at the original last-row index appends correctly; the reported penultimate-row error does not reproduce.

## Regression coverage

New file: `tests/integration/test_report_followup_round18_20260917.py`

Focused tests: **10/10 passed**. Coverage includes UNC masking precision, person-only initial matching, 2500-level iterative JSON walking, simulated Windows sharing violations, transactional backup rollback, Range/probe cancellation contracts, full-MP3/history/event-sound hardening, accessibility/Easy settings, dropped-batch cancellation and HWND re-registration.

## Final verification

- `pytest`: **352 passed, 0 failed**
- Historical regression: **PASS — 269 passed, 114 known source-shape incompatibilities**
- Exception audit: **PASS — 109 reviewed broad-exception passes**
- Undefined globals: **OK — 77 modules**
- Unused imports: **OK — 32 implementation modules**
- Qt localization: **OK — RU/UK/DE/EN, help topics complete**
- Full parity: **PASS — 61/61**
- Qt import audit: **OK — 73 project modules reachable**
- `compileall`: PASS

Windows/PySide6/PyInstaller frozen execution is not available in this Linux environment; no Windows build success is claimed here.
