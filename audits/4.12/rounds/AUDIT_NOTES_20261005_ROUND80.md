# Round 80 — external audit follow-up

Applied confirmed or defensively useful findings from the 2026-10-05 follow-up review:

- missing-source diagnostics no longer depend on the track index being valid: a missing URL with a malformed/negative index is reported using a stable 1-based positional fallback instead of falling through to a deeper generic `Не указан адрес аудиофайла.` failure;
- segmented Range geometry now caps `task_count` by the positive byte size, so tiny/direct-call payloads cannot produce zero-length chunks or an invalid `Range: bytes=0--1` request;
- the headless `download_engine._ask_missing_media_action()` now mirrors the safe BookFlow index policy: booleans and malformed/negative values are filtered instead of being converted with raw `int()` (notably `True -> 1`);
- queue re-analysis in the Qt analysis/download mixin now preserves valid track index `0` consistently with the Round 78/79 zero-index contract.

Reviewed and intentionally unchanged:

- `ProbeMixin._estimate_required_space()` deliberately rejects boolean, fractional, non-finite and malformed selected indices. Existing regression tests require the strict failure because silently filtering invalid selections could underestimate required disk space; BookFlow's softer runtime filtering serves a different boundary;
- Mapping tolerance in a few BookFlow normalization helpers is defensive input hardening, not a promise that the complete downloader accepts arbitrary dictionaries in place of the `Track` model. The main processing pipeline still intentionally uses model attributes such as `local_status` and `actual_duration`;
- `AppSettings.__contains__` intentionally reports physically stored canonical keys while legacy aliases remain readable through `[]`/`.get()`. Round 79 regression tests explicitly protect that persistence/membership contract;
- Windows directory-like path masking remains privacy-first. Ambiguous no-extension strings such as `C:\\Audio\\My Book for Alice` cannot be reliably distinguished from a real private directory path without risking data leakage. File paths with an extension already preserve trailing diagnostic text;
- runtime localization resolves exact entries before regex rules and regex rules before prefix fallbacks. Existing tests cover both the exact `Анализирую audioknigi.com.ua быстрым HTTP-способом…` wording and regex-before-prefix messages such as progress/history, so the reported shadowing is not present;
- `source_health_service.py` deliberately uses `trust_env = False`, matching `core.build_http_session()` and the Cloudflare/DoH proxy-isolation policy;
- `parts` versus `selected` download-mode naming and provider/service coupling are broader domain/architecture migrations, not correctness fixes for this round;
- PoleKnig's generic `_clean_text()` edge punctuation behavior is not changed without a reproducible real author/narrator parsing failure; title parsing already uses its separate title-preserving cleaner;
- full-MP3 duplicate preflight, Easy-mode stale-input protection, focus-frame ownership and help-center translation completeness were reviewed as intentional/correct behavior.
