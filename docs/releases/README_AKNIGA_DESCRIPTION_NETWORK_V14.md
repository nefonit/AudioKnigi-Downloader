# V14: Akniga synopsis boundaries and Playwright auto DNS fallback

- Descriptions now stop at a standalone `Содержание`/`Оглавление` heading even if the track list is embedded in the very same `description__article-main` element as the prose. Adjacent support and recommendation section headers are excluded too. Do not hard-code book text.
- In DNS `auto` mode with no user proxy, `Page.goto: net::ERR_CONNECTION_TIMED_OUT` and other explicit network navigation errors can trigger **one** clean retry with system DNS. `cloudflare` mode is strict. Generic 30-second DOM navigation timeout, HTTP status and player/content errors never trigger retries.
- Automatic retry is not a WARP/VPN replacement. With network filtering, both routes can fail. A safe explanatory message is shown if both attempts encounter navigation connectivity errors.
- Source project only, not Windows executable. Check on Windows with Cloudflare One on/off and verify both Akniga pages; playback/HLS was not changed.
