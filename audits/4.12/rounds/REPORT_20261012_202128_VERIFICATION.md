# Round 90 — verification of report submitted 2026-10-12 20:21

**Scope:** Every substantive observation in the 397-line Russian report, checked against the Round 90 source snapshot. Source-level review and tests must not be mistaken for Windows accessibility acceptance.

**Environment:** Linux / Python 3.13; PySide6 absent. All 919 non-accessibility tests collected across `tests/unit` and `tests/integration` (`--ignore=tests/integration/test_accessibility.py`) passed when run in four nonoverlapping groups: **276 + 341 + 229 + 73 = 919, zero failures.** Code compiles with `compileall`. No Windows EXE or real NVDA/JAWS run was performed.

## Item-by-item findings

1. **Parallel download unpacking (`download/book_flow.py`) — FALSE POSITIVE.** Current `futures` values are `(file_index, url, target)` (three fields) and are unpacked into exactly three variables. `fallback_url` is passed separately to `pool.submit`, not retained in the result tuple. No change.
2. **Legacy onboarding flag in `config/settings.py` — CONFIRMED, FIXED.** A direct partial save of an *existing* settings file without the onboarding flag previously inserted `False` before migration, forcing a legacy profile to repeat onboarding. A new profile must still keep `False`. The fix distinguishes those cases; three regressions cover legacy, new and unfinished profiles.
3. **Track dictionaries vs. `Track` objects (`download/media.py`, `download/book_flow.py`) — CONDITIONAL COMPATIBILITY RISK, NOT PROVEN RUNTIME CRASH.** `Book.tracks` is explicitly typed as `list[Track]`; `Track` exposes its attributes and the standard engine uses that type. Some probing helpers also support mappings. Rewriting all typed paths to mapping access without a supported integration contract would risk regressions. No change.
4. **Missing terminal return in `download/common.py:unlink_with_retry` — FALSE POSITIVE.** Every successful path returns `True`; failures raise, including the last attempt. The loop executes at least once. Adding an unreachable `False` could conceal an impossible failure path. No change.
5. **Literal `{Author}` placeholders (`i18n.py`, `legacy_literals.json`) — ALREADY PROTECTED.** `ui_text` explicitly excludes `_LITERAL_TEMPLATE_EXAMPLES` from `.format`, and `tr` does not call `.format` with empty kwargs. Regression verifies intact placeholders. No change.
6. **Overlap between runtime prefix and regex — INTENTIONAL FALLBACK.** `localize_runtime_text` evaluates regex rules first, then prefixes; prefix covers unmatched variants and is retained for compatibility with existing tests. No change.
7. **Blank line in translated disk-space error (`runtime_regex.json`) — CONFIRMED, FIXED.** Added matching double newline in EN/DE/UK translations. Tested localized paragraph separation.
8. **German grammar for tray minimization (`legacy_literals.json`) — CONFIRMED, FIXED.** Changed to `Bei langem Download oder langer Warteschlange ...`.
9. **Wrong settings import path (`services/download_request.py`) — FALSE POSITIVE.** `audioknigi/config/settings.py` exists, imports successfully and is used throughout the repository. No change.
10. **Final chapter's unknown end (`services/book_analysis_service.py`) — CONFIRMED CONDITIONAL BUG, FIXED.** When the last chapter lacks `end` but has known positive duration, include `start + duration` in the shared-source lower bound. When final duration is unknown, do not invent one. Both branches tested without network calls.
11. **Pending future cancellation (`services/book_analysis_service.py`) — CONFIRMED SMALL CONSISTENCY GAP, FIXED.** Call `future.cancel()` for pending tasks when the cancellation event is set, then raise the existing `Cancelled` error. Tested.
12. **`source_health_service.py:trust_env=False` — CONDITIONAL NETWORK TRADEOFF.** This deliberately ignores proxy environment variables for the quick health probe. It can be inaccurate in proxy-only networks; changing it globally requires proxy/VPN policy and real network testing. No change.
13. **`QueueItem` versus `QueueTask` — INTENTIONAL LEGACY COMPATIBILITY.** The service has a legacy adapter; removing either public model without a migration plan could break existing queues. No change.
14. **PoleKnig author query vs. matching title — PLAUSIBLE RANKING EDGE CASE, NOT FULLY REPRODUCED.** The exact-title branch can supersede the author-expansion branch even when author evidence exists. A behavioral change needs reproducible provider fixtures distinguishing author from book title. Deferred, no speculative ranking change.
15. **Automatic Cloudflare DoH limited to first two IPv4 bootstrap IPs — NETWORK POLICY TRADEOFF.** Strict mode allows a larger bootstrap list. Auto mode deliberately uses two endpoints to bound latency. IPv6-only conditions need on-network verification. No change.
16. **Loss of ordered steps in `qt/help_center.py` — CONFIRMED, FIXED.** Render numbered instructions with `<ol>` (preserving non-1 starting numbers) and bullets with `<ul>`; split when list types change. Tested with AST-extracted pure renderer because PySide6 is unavailable.
17. **Easy-mode Download disabled after search — FALSE POSITIVE FOR CURRENT FLOW.** `SearchUiMixin.use_selected_result()` writes `selected_result.url` to `easy_input` before analysis. No change.
18. **No retry on acceptance report replacement — CONFIRMED RESILIENCE GAP, FIXED.** Use the established Windows-safe `replace_with_retry` helper rather than `Path.replace`. Regression tests report serialization and cleanup; real Windows AV contention remains to be validated.
19. **Transient mixed-language screen reader announcements after language switch — ACKNOWLEDGED RESTART BEHAVIOR.** Program explicitly informs the user that the UI language applies fully after restart. A live-language refactor is beyond a safe bug fix; Windows UIA behavior remains unverified. No change.
20. **`TrackTableModel.set_selected_indices(None)` clears all tracks — CONFIRMED SEMANTIC BUG, FIXED.** `None` now selects all via `set_all_selected(True)` per `DownloadRequest` contract, while explicit empty lists clear the selection. Static contract test added; Qt runtime needs validation.
21. **Volume value not saved until later settings write — CONFIRMED RESILIENCE GAP, FIXED.** Added single-shot 750-ms persistence debounce plus immediate `sliderReleased` save, avoiding write-per-`valueChanged`. A crash within the debounce window can still lose the latest value; not an absolute durability guarantee.
22. **Hidden compatibility controls (`qt/main_window_pages.py`) — INTENTIONAL TEST/API COMPATIBILITY.** Hidden and disabled buttons retain accessibility identities for old contracts. Removing them risks regressions. No change.
23. **Queue reanalysis error text is lost (`qt/mixins/analysis_download.py`) — CONFIRMED, FIXED.** Preserve the task ID on error; update its `last_error`, persist the queue, refresh rows, then clear the marker. Existing `needs_analysis` status is retained so user can retry. Static contract regression included; Windows UI test pending.
24. **Daemon startup source-health worker continues briefly after window closes — MINOR BOUNDED BACKGROUND BEHAVIOR.** Daemon cannot block process exit, and request timeout is bounded. Forcing cancellation into HTTP retries risks destabilization; no change without confirmed user impact.
25. **Keyboard context menu outside viewport (`qt/mixins/history.py`, `queue.py`) — CONFIRMED EDGE CASE, FIXED.** On keyboard invocation, `scrollTo(current, EnsureVisible)` before calculating `visualRect`. Static contract check included; actual Qt screen-reader validation pending.

## Changes made

Production: `audioknigi/config/settings.py`, `audioknigi/qt/track_model.py`, `audioknigi/qt/mixins/analysis_download.py`, `audioknigi/qt/mixins/history.py`, `audioknigi/qt/mixins/queue.py`, `audioknigi/qt/help_center.py`, `audioknigi/services/book_analysis_service.py`, `audioknigi/qt/acceptance_contract.py`, `audioknigi/qt/player_mixin.py`, `audioknigi/locales/runtime_regex.json`, `audioknigi/locales/legacy_literals.json`.

Tests: `tests/integration/test_round90_report202128.py` (13 new tests).

## Release gate

This source-level audit is complete for all 25 items. It does **not** close the Windows/NVDA/JAWS accessibility acceptance gate or guarantee all runtime combinations. Before release, validate help ordering through QTextBrowser and NVDA/JAWS, selecting a whole book in TrackTableModel, queue reanalysis errors, keyboard context menus, volume slider persistence, and fallback download on Windows.
