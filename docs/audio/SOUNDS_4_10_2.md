# AudioKnigi Downloader 4.10.2 — multilingual event sounds

## New localized sounds

The event sound manager now checks `assets/sounds/<language>/` first and falls back to the original Russian asset when a localized recording is not present.

English recordings supplied in this release:

- `download_start` — Book download in progress
- `download_complete` — Download complete
- `error` — An error occurred
- `book_found` — The book has been found
- `book_not_found` — Book not found
- `download_paused` — Download paused

## New Russian events

- `recovery_started` — Восстановление загрузки
- `files_already_downloaded` — Файлы уже скачаны
- `narration_changed` — Выбран другой вариант озвучки
- `update_available` — Обновление доступно

`update_available` is bundled and exposed by the sound manager but has no automatic trigger yet because 4.10.2 does not contain a network update checker.

Ukrainian and German currently use the Russian fallback until matching localized recordings are supplied.
