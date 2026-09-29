# Round 61 — external audit follow-up

Applied confirmed fixes from the 2026-09-29 external review:

- unified AppSettings construction semantics and hid migration metadata;
- hardened support-bundle secret/path redaction and queue URL hashing;
- deduplicated fallback candidates before the top-8 cap;
- persisted selected indices after skipping unavailable media;
- counted segmented resume files in disk estimates and validated start-only shared timelines;
- stopped inventing chapter timeline positions when duration is unknown;
- fixed one-letter title matching and author-detail scoring;
- preserved Playwright User-Agent case-insensitively in both fallback paths;
- hardened queue dataclass serialization;
- used the Windows known Documents folder and expanded narrator metadata stop labels;
- fixed Easy narration activation, player-rate persistence, normalized chapter-path matching, history focus recovery, dropped-batch cancellation, current guidance refresh, and system-theme callback lifetime;
- normalized the specifically reported DE/EN/UK localization inconsistencies.

Not changed: Python 3.8 `cancel_futures` compatibility because the project contract is Python 3.11+; broad dead-code, MRO and legacy-model refactors are deferred as architectural cleanup rather than runtime defects.
