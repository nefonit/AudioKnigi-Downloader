# AudioKnigi Downloader V12 — safer HLS interruption and resume

Based on **V11**, which remains unchanged. All eight audiobook sources, Akniga collections and book descriptions are retained.

## Changes

- Parallel HLS interruption: running workers receive their stop signal **before** waiting for the worker pool to finish; pending tasks are canceled. A blocked HTTP read can still take up to its socket timeout.
- Previously completed HLS VOD segments are retained under the book's hidden `.hls-cache` directory and can be reused on the next attempt **only** for an identical signed playlist URL and manifest bytes. Their SHA-256 sidecars are checked before reuse.
- A segment whose actual byte count differs from the HTTP `Content-Length` is rejected and retried, instead of being cached as complete. This extra check is available only for uncompressed non-chunked responses with a usable `Content-Length`; it does not by itself prove the media contents are intact.
- The progress/status message distinguishes completed segments, reused segments, and bytes newly downloaded over the network. The network speed indicator no longer counts bytes read from disk cache.
- After the full MP3 is successfully produced and validated, the existing successful-download cleanup still removes the book's HLS cache.

## Important limitations

- **Parallel HLS mode must be enabled**, and the operation must be for a whole supported VOD. Chapter-only FFmpeg seeks and unsupported playlists do not use this segment cache.
- A re-analysis can produce a new expiring/signed URL or changed manifest. In that case the cache is **not** reused, by design. No auth tokens or playlist URLs are persisted to the cache.
- This is not arbitrary MP3 Range resume. A server that does not declare a valid length may still terminate a segment early; downstream MP3 duration checks guard against publishing an obviously short file.
- Repeated interruptions leave the hidden `.hls-cache` folder until a validated complete MP3 finishes. Old unused cache directories can occupy disk space and can be removed manually after the application is closed.
- Network access restrictions without Cloudflare One/WARP remain unchanged.

## Manual Windows verification

1. Enable Cloudflare One if required for Akniga access and enable **parallel HLS** in the downloader.
2. Analyze an authorized, longer Akniga audiobook and start downloading the **whole book**. Cancel after some segments finish (not while chapter-seek downloading).
3. Reuse the **same analyzed book** and restart promptly. The status should indicate `из кэша N` and the log should report `HLS: восстановлено N готовых сегментов из кэша.` when a matching manifest is used.
4. Verify the final MP3 plays to the last chapter; confirm the `.hls-cache` folder is cleared after successful validated completion.
5. Retry after changing/reanalyzing the playlist; a changed signed manifest should download again rather than trust old parts.
6. Check screen-reader status announcements on Windows with NVDA/JAWS if used.

**Validation performed:** offline synthetic tests for cancellation timing, restart reuse, cached bytes not counted as network traffic, SHA-256 corruption and `Content-Length` mismatch. Also tested existing search, download-flow, network, localization and diagnostics regressions. Live Windows HLS download was not available in this environment.
