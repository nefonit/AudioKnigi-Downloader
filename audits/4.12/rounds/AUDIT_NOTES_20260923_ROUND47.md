# Round 47 audit notes — 2026-09-23

Round 47 reviews the fifth external audit against the Round 46 codebase and applies only findings reproduced or proven from the current implementation.

## Confirmed fixes

- **Support bundle privacy/log integrity:** `_sanitize_log_bytes()` no longer collapses an entire multi-line log because its first line starts with a Windows/UNC path. `Path.home()` failure no longer bypasses drive/UNC masking, and drive-root / trailing-slash paths are covered by the embedded path sanitizer.
- **Settings mapping contract:** `AppSettings` now materializes canonical defaults at construction so `[]`, `in`, `keys()`, `len()`, deletion, `dict()`/`to_dict()` all describe the same mapping. Explicit and unknown/plugin keys are preserved. Legacy profiles containing only removed keys such as `auto_chunk_min_kbps` or `normalize_audio` are treated as existing profiles for onboarding migration.
- **Disk-space preflight:** selected track indices are normalized with `safe_int`, so legacy/string indices do not silently bypass required-space estimation.
- **AudioKnigi author provenance:** `SearchResult.author_inferred` marks the ambiguous single `Name - Title` search-card heuristic. Once a detail page provides a trusted author, an inferred card prefix cannot become a false coauthor or be used to strip a character/series name from the title. Explicit author fields and unambiguous multi-author prefixes retain prior coauthor behavior.
- **AudioKnigi narrator/direct parsing:** the plain-text `Исполнитель/Читает/Диктор` fallback is shared between search hydration and direct book analysis. Direct analysis also strips multiple verified coauthor prefixes cumulatively.
- **Unfinished manifests:** `selected_indices` values `""`, `"all"`, and `"*"` now retain whole-book semantics consistently with queue deserialization.
- **Integer normalization:** `safe_int("12.0")` is accepted as 12, while genuinely fractional values such as `"12.5"` still fall back instead of being silently truncated.
- **Qt context menu:** the delete action accepts the `QAction.triggered(bool)` payload on all supported PySide6 builds.

## Reviewed but intentionally unchanged

- `safe_normalization_mode` already accepts the documented second `default` argument.
- Queue `Track`/`NarrationVariant` values already inherit `MappingDataclass.to_dict()`, so the reported silent loss of dataclass tracks is not present.
- `session.trust_env = False` remains an intentional networking contract required by the Cloudflare-DoH routing design.
- Stable Russian fallback template path tokens remain intentional to prevent folder renames when UI language changes.
- PoleKnig narration variants continue to use the representative canonical title by design; this is grouping semantics rather than data corruption.
- Runtime localization duplication/order observations are maintenance notes; current precedence and translations are covered by localization audits and were not changed in this runtime-hardening round.
- The reported AudioKnigi cancellation limitation is architectural: `requests` cannot safely interrupt an already-running synchronous socket from `Future.cancel()`. The existing bounded network timeout remains unchanged here rather than introducing unsafe cross-thread session closure.

## Verification

- `pytest -q`: **598 passed**
- Round 47 focused + relevant prior regressions: **49 passed** before the full suite
- Historical regression audit: **PASS — 255 passed / 128 known shape incompatibilities**
- Full parity: **PASS — 61/61**
- Qt localization: **PASS — ru/uk/de/en**
- Qt import audit: **PASS — 75 project modules**
- Exception audit: **PASS — 107 reviewed broad exception passes**
- Undefined-global audit: **PASS — 79 modules**
- Unused-import audit: **PASS — 32 implementation modules**
- `compileall`: **PASS**
