# 4.12.42 acceptance-parser, cancellation and diagnostics hardening

Date: 2026-09-15

## Confirmed findings fixed

- Candidate-manifest automated gates may now be represented either as the release manifest's compact `"pass"` strings or as detailed gate dictionaries containing `status`.
- `unused_import_audit.py` resolves quoted forward references nested inside generic annotations such as `Optional["Model"]`.
- Runtime localization scanning covers `main_window_pages.py`, `player_mixin.py` and every Qt main-window mixin.
- Full-parity evidence consults the modular source bundle before treating a compatibility facade as missing.
- Historical pytest failure parsing preserves spaces and ` - ` text inside parametrized node IDs; the two previously truncated HTTP-416 incompatibility IDs were expanded in the allowlist.
- PoleKnig author-catalog and Playwright fallbacks preserve `Cancelled` instead of converting cancellation into partial success/fallback.
- Existing empty error logs are retained in the support ZIP.
- Atomic text writes create parent directories.
- Track splitting honors an explicit/effective duration when no end timestamp is present.
- The audioknigi.com.ua browser fallback releases Chromium before the ordinary HTTP playlist request.
- The queued full-MP3 multi-source warning now has RU/UK/DE/EN runtime translations.

## Findings already fixed or not defects in 4.12.41

- Frozen C-extension package paths, standard module globals, direct/qualified localization calls, line-anchored pytest ERROR detection, log secret-key boundaries, HTML title fallbacks, atomic text sidecars, selective configured-URL masking, untruncated history export, non-mutating SearchResult canonicalization, provider cover prefetch, early `search_model`, `transient_menu` use and queued full-MP3 mode were already present in 4.12.41.
- PoleKnig currently names the catalogue seed parameter `seed_links`; there is no unresolved `seed_author_links`/`seed_links` NameError in this source.
- `--status` and `--automated-only` intentionally remain tied to the exact hash-bound release-candidate manifest. The documented Windows acceptance workflow builds that manifest after the frozen automated gates and then re-validates the same EXE before status/manual sign-off.
- In full-MP3 copy mode the source is already MP3 and becomes the final MP3 without transcoding; creating another retained byte-identical "source" file would duplicate the output rather than preserve a distinct source format.

## Verification before packaging

- active pytest: 197 passed
- full parity: 61/61
- localization audit: OK (ru/uk/de/en)
- Qt import audit: OK (73 modules)
- exception audit: PASS (113 reviewed broad silent handlers)
- unused-import audit: OK (32 implementation modules)
- undefined-global audit: OK (77 modules)
- historical regression: 273 passed, 110 known incompatibilities, 0 unexpected regressions
