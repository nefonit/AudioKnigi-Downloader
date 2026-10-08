# Round 81 — external audit follow-up

Applied confirmed findings from the 2026-10-06 review:

- `_download_single()` now rejects a cleanly terminated but incomplete response when the expected total size is known, preserving the `.part` file instead of promoting truncated content to the final source file;
- `ProbeMixin._estimate_required_space()` accepts mapping-backed selected tracks consistently and reads mapping-backed `index`, `local_status`, and `file` fields through one helper while retaining its intentionally strict validation for booleans, fractional/non-finite values, and malformed indices;
- `source_target_assignments()` now derives stable source slots from both dataclass tracks and mapping-backed tracks;
- `BookFlowMixin` dispatches timing refresh callbacks only when `self.ui` is actually callable;
- source-health probing treats HTTP 503, as well as 403/429, as a reachable-but-protected response so Playwright-capable sources are not mislabeled dead;
- added runtime translations for playlist-refresh narration loss, persistent 404/410 media loss, no-selected-parts, and interrupted single-stream downloads;
- restored the missing Ukrainian advanced-settings location in help text;
- exported `install_keyboard_focus_frame` and `KeyboardFocusFrameManager` from the accessibility module;
- keyboard-invoked localized text context menus now open next to the focused editor/caret instead of following a stale physical mouse cursor;
- Ukrainian `Пробіл` is recognized as a keyboard key in help-center `<kbd>` rendering.

Reviewed and intentionally unchanged:

- the reported `source_analysis.py` `(candidate_score, candidate_url)` unpacking bug is stale in Round 80: the live code already iterates `for candidate_url, _score in sorted(best_by_url.items(), ...)` and passes the URL string to the provider;
- exact runtime translations are resolved before regex rules, and regex rules before prefix fallbacks; the reported prefix-shadowing and exact-vs-regex collisions do not occur in the current resolver;
- `session.trust_env = False` remains the intentional application-wide Cloudflare DoH/proxy-isolation policy and is not changed in source-health probing;
- duplicate strings across locale catalogs, the duplicated fallback-search architecture, first-run wizard cleanup, provider/service coupling, `parts` versus `selected`, PlayerJS emergency scraping breadth, and onboarding/dead-code cleanup are maintainability topics rather than Round 81 correctness fixes;
- the Windows diagnostic path redactor remains privacy-first for ambiguous directory-like prose; file paths retain following diagnostic text where a file boundary can be identified;
- forced process termination can lose the latest in-memory player-volume slider change by design; normal shutdown persists settings.
