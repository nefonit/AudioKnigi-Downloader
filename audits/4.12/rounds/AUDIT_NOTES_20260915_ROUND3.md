# Audit notes — round 3 (2026-09-15)

This round was applied to the Round 2 fixed tree. Findings from the supplied audit were verified against the actual code before modification; recommendations that were stylistic, already covered, or not reproducible were not treated as runtime defects.

## Confirmed and fixed

- `download_engine.py`: duplicate preflight now requires `strictly_ready` when duration probing is enabled; file existence alone is only accepted by the explicit no-probe path.
- `core.py`: header-only browser-profile refreshes preserve the previously persisted cookie count.
- `cover_fetch.py`: protocol-relative cover URLs (`//host/path`) are promoted to HTTPS even without a referer.
- `logging_utils.py` and support diagnostics: Windows home-path masking is case-insensitive.
- `network_dns.py`: half-closed proxy sessions now have a bounded 30-second drain deadline instead of being able to wait forever for the peer FIN.
- `i18n.py`: malformed non-dictionary runtime-exact entries no longer raise `AttributeError`.
- `support_bundle.py`: ordinary two-backslash UNC paths are redacted correctly.
- `download/probe.py`: standard `number_title` naming strips an existing audio extension before appending `.mp3`; disk-space preflight now uses a conservative 128 kbps duration-based fallback when remote size is unknown.
- `download/media.py`: FFmpeg timeout cleanup protects the post-kill `communicate()` call so a secondary `TimeoutExpired` cannot mask the primary timeout error.
- `download/network.py`: once a Range worker reports a fatal error, active peer responses are cancelled so the controller does not wait on unrelated network timeouts.
- Runtime localization: completed duration probing now has completed-tense translations; full-MP3 ID3 stage wording is aligned with `messages.json`; dynamic search-result counts and partial-source failures are localized.
- `search_service.py`: the short-query validation message now exactly matches the localization catalog.
- `book_analysis_service.py`: playlist track indices are contiguous after invalid entries are skipped; protocol-relative and root-relative `.pl.txt` references are supported without breaking the one-argument extraction helper contract.
- Qt accessibility/UX: settings combo accessible names reuse their already localized visible labels; selected-track lookup falls back to the current index; duplicate dialogs/buttons have stable accessibility identifiers.

## Reviewed but intentionally not changed

- Use of `DownloadRequest._track_index`: this is an encapsulation/style concern, not a demonstrated runtime defect. Refactoring it would widen the public API without a user-visible fix.
- `runtime_prefixes.json` generic `Обрабатываю полный файл` prefix: the actual current full-file message is already handled by a more specific runtime regex. No speculative generic-suffix translator was added.
- Event-sound replay: the current code already calls `stop()` before seeking/replaying; no reproducible failure was established by the report alone.
- The defensive `playlist_response is None` guard is technically unreachable for ordinary `requests`, but retaining it is harmless and preserves archived behavioral-contract tests.

## Verification

- New Round 3 regressions: 12 passed.
- Full pytest suite: 228 passed, 0 failed.
- Exception audit: PASS (`reviewed_broad_exception_passes=113`).
- Historical regression audit: PASS (`passed=271`, `known_shape_incompatibilities=112`).
- Undefined-global audit: OK (77 modules).
- Unused-import audit: OK (32 implementation modules).
- Qt localization audit: OK for `ru`, `uk`, `de`, `en`.
- Full parity audit: PASS 61/61.
