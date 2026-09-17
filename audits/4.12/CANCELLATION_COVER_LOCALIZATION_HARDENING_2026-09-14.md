# 4.12.39 Cancellation, cover and localization hardening

## Confirmed and fixed

- PoleKnig narration discovery no longer swallows `Cancelled`.
- CONNECT relay exits on upstream EOF.
- PoleKnig meta-content extraction preserves URL punctuation.
- Crash-report formatting has a recursion-safe fallback.
- Downloader media processing now has a real shared `_fetch_cover_bytes` implementation.
- WebP cover sidecars use `.webp`.
- `metadata.json` uses the central `save_json` lock/atomic writer.
- Playlist `title: null` no longer becomes the literal string `None`.
- Analysis futures re-raise `Cancelled`.
- Accepted onboarding settings use `save_app_settings`.
- Worker request snapshots discard unsupported native cover objects before deepcopy.
- Missing Ukrainian UI literals and the unresolved queue message are localized.
- `Скачано X из Y` is translated as one runtime template.

## Reviewed but intentionally unchanged

- `MappingDataclass.to_dict()` is a Python mapping conversion, not the queue JSON serializer; queue persistence already base64-encodes cover bytes explicitly.
- Full-MP3 copy mode is only selected when the source codec is already MP3. Keeping a second source when `delete_source=False` would duplicate the final bytes, so the existing behavior remains intentional.
- `diagnostics/support_bundle.py` imports `QT_QUEUE_FILE` from the GUI-neutral queue service; this does not create a Qt dependency.
- The current Chrome 153 user-agent is not a future version on 2026-09-14.
- The output-folder signal connection is safe because `_choose_output_dir(self, _checked=False, *, target=None)` explicitly consumes Qt's `clicked(bool)`.
- The 404/410 fallback already infers missing track indices from response/request URLs and the single-active-track case.

## Working-tree verification

- Active pytest: 155 passed.
- Full parity: 61/61.
- Localization audit: OK for ru/uk/de/en.
- Qt import audit: 73 project modules, no legacy frontend path.
- Exception audit: 113 reviewed broad silent handlers.
- Unused-import audit: 32 implementation modules.
- Undefined-global audit: 77 modules.
- Historical regression: 273 passed, 0 unexpected regressions.
- `compileall`: OK.
