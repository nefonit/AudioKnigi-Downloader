# Round 76 — Round 75 external audit follow-up

Applied confirmed findings from the 2026-10-03 follow-up review:

- `AppSettings.__setitem__` now maps legacy write keys `normalize_audio` and `auto_chunk_min_kbps` to their canonical settings (`normalization_mode` and `auto_chunk_min_kbytes_per_sec`) while keeping deprecated keys out of live/persisted settings;
- queue deserialization uses the public `dataclasses.fields()` API for `Track` and `NarrationVariant` field filtering instead of their private `__dataclass_fields__` implementation attribute.

Reviewed and intentionally unchanged:

- `download_request.py` and `download_engine.py` correctly import `config.settings`; the repository physically contains `audioknigi/config/settings.py`, and the same package path is used consistently by the GUI;
- support-bundle POSIX path masking remains deliberately privacy-first. Treating slash-prefixed tokens such as `/sec` less aggressively would make it impossible to guarantee masking of valid one-component absolute paths such as `/secret`;
- `_cancel_active_network_io` already snapshots active responses under its lock and closes them outside the lock, while worker error handling checks cancellation/peer abort state; no change is required;
- lazy provider/service imports, worker-thread UI marshaling, cover-cache normalization before `deepcopy`, accessibility throttling/focus handling, media-key declarations, player resume behavior, event-sound threading and system-theme updates were reviewed as correct and require no patch.
