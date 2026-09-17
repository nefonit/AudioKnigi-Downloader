# AudioKnigi Downloader 4.10.4 — complete English event sounds

The English sound pack now contains localized recordings for all 17 registered program events.

## Newly added English recordings

- `link_pasted` — Link pasted
- `queue_item_added` — Book added to queue
- `recovery_started` — Restoring download
- `files_already_downloaded` — Files already downloaded
- `narration_changed` — Another narration selected
- `update_available` — Update available

## Complete English event set

1. `download_start`
2. `download_complete`
3. `error`
4. `link_pasted`
5. `queue_item_added`
6. `search_complete`
7. `queue_complete`
8. `queue_started`
9. `download_cancelled`
10. `download_resumed`
11. `download_paused`
12. `book_not_found`
13. `book_found`
14. `update_available`
15. `recovery_started`
16. `files_already_downloaded`
17. `narration_changed`

When the interface language is English, every registered event resolves to `assets/sounds/en/` without using the Russian fallback.

`update_available` is bundled and registered, but it will only play once a real application update checker reports an available update.
