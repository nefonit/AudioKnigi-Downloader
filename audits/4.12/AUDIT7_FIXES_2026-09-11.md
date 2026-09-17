# Audit 7 fixes — 2026-09-11

Base: `AudioKnigi_Downloader_v4_12_31_PHASE39_AUDIT6_FIXED_20260911`.

## Fixed

- `downloader.py`: Smart Format now normalizes FFprobe codec names with `strip().lower()` before comparing to `mp3`, avoiding needless transcoding for values such as `MP3` or ` mp3 `.
- `core.py`: extended JSON-LD metadata is now read only from `Book` / `AudioBook` / `CreativeWork` nodes. `WebSite`, `Organization`, breadcrumbs and other page chrome can no longer supply the audiobook description/genre/year.
- `downloader.py`: removed the unreachable `task_count < 2` branch in segmented downloading.
- `downloader.py`: HTTP 200 Cloudflare/Turnstile interstitials are recognized via strong challenge markers while ordinary pages that merely mention Cloudflare/CAPTCHA do not trigger the browser fallback.
- `downloader.py`: oversized/corrupt `.segNNN` resume files are removed before the initial aggregate progress value is computed, preventing progress from exceeding the real total when the segment is re-downloaded.
- `network_dns.py`: added Cloudflare's official IPv6 bootstrap addresses (`2606:4700:4700::1111`, `2606:4700:4700::1001`) so DoH can bootstrap on IPv6-only networks.
- `knigavuhe.py`: narration-reader hydration uses the project `Cancelled` exception inside workers and never swallows `Cancelled` from `future.result()`.
- Qt queue UI: retry-task control now uses the contextual translation key `Повторить задачу` (`Retry task`) instead of the text-editor `Повторить` key (`Redo`).

## Reviewed; no code change needed

- `run_full_mp3`, `runtime_delete_source=False`, `copy_mode=True`: retaining a second identical source file would duplicate bytes with no semantic benefit. The final MP3 is itself the untouched source in copy mode.
- `run_full_mp3`, `remote_size == 0`: a reliable pre-download disk-space estimate is impossible without a server size. The post-download/transcode check already uses the actual local source size.
- `audioknigi_qt.py` absolute package imports: intentional launcher/package contract; supported launch paths already put/install the package root correctly.
- file status localization: `Track.local_status == "нет"` is explicitly mapped by `TrackTableModel` to `нет (файл)`, so file status remains `missing / fehlt / немає`. The generic `нет` key is intentionally used for Boolean/no UI text.
- plain HTTP proxy relay: the previous audit already added `return_when_right_closes=True`, so ordinary HTTP responses terminate when upstream closes.
- PoleKnig pagination, UI scale base font, template path traversal, theme restoration and event-sound LRU notes were confirmed as already correct.

## Regression coverage added

`tests/test_audit7_followup_20260911.py` covers:

1. case/whitespace-insensitive MP3 Smart Format detection;
2. JSON-LD site metadata not leaking into book metadata;
3. HTTP 200 protection-page detection without broad false positives;
4. oversized segmented-resume sanitization and dead-branch removal;
5. IPv4 + IPv6 Cloudflare bootstrap addresses;
6. typed Knigavuhe hydration cancellation;
7. `Retry task` vs text-editor `Redo` localization contexts;
8. contextualized missing-file status.

## Verification

- pytest: **358 passed**
- Full Parity: **61/61**
- Qt Localization Audit: **OK** (`ru`, `uk`, `de`, `en`)
- Qt Import Audit: **OK** (46 project modules reachable)
- `audioknigi/qt/main_window.py`: **3998 lines**
