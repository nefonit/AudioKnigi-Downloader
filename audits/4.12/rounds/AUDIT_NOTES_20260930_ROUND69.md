# Round 69 — Round 68 audit follow-up

Applied confirmed findings from the 2026-09-30 review:

- `_is_expired_media_error` now recognizes `MissingMediaSourceError` directly, preserving the 404/410 refresh contract even if an exception is reconstructed without its original cause chain;
- `_download_source_with_fallback` now builds a unique list of non-empty source URLs before enumeration, avoiding a phantom empty primary entry;
- AudioKnigi result hydration explicitly re-raises `Cancelled` instead of letting the generic metadata fallback temporarily swallow it;
- the Easy-mode operation dialog now uses a context-specific `cancel_operation` translation instead of the text-editor `Отменить` literal, so English shows `Cancel` while the editor context menu correctly keeps `Undo`;
- German analysis guidance uses `Strg+D`, and the shortcut help consistently uses `Umschalt+Tab`.

Reviewed and intentionally unchanged:

- selected-track disk preflight remains deliberately conservative when only whole-book remote size is known;
- Windows-path support-bundle matching intentionally favors over-redaction over path/privacy leakage;
- `QT_QPA_PLATFORM` restoration in the accessibility self-test is already correct;
- runtime regex localization is evaluated before prefix fallback, so overlapping regex/prefix entries do not shadow richer translations;
- overlap between legacy/runtime localization tables is redundant but not a runtime defect and is left intact to avoid broad localization churn;
- `source_health_service` intentionally uses `trust_env=False`, matching the main `build_http_session` policy, so ordinary search and health probes share the same proxy isolation policy;
- history persistence is intentionally bounded to the latest 500 rows;
- PoleKnig `_extract_meta_content` does not require `re.S`: its patterns use negated character classes that already match newline characters; a multiline regression covers this behavior;
- author spelling `Едуард Саратовцев` is the creator-selected canonical spelling;
- Linux/macOS DNS behavior, stable template path identity, queue cover-size limits, player edge guards, modeless operation UI, media-key handling and screen-reader routing are all intentional current contracts.
