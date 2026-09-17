# AudioKnigi Downloader 4.12.10 — missing media parts

If an audio source returns HTTP 404/410, the application first refreshes the public book page and playlist once. If the refreshed media URL is still missing, a modal accessible decision dialog is shown.

- **Остановить загрузку** — safe/default action.
- **Пропустить часть и продолжить** — removes only the affected selected track indices and continues the remaining tracks.
- If one missing source contains several selected chapters, all affected indices are listed before the user decides.
- If all selected parts are unavailable, skipping is not offered because there is nothing left to download.
- A completed partial book is clearly marked **Готово с пропуском** and a final warning lists skipped parts.
- Skipped indices are also written to `app.log`.

Windows EXE builds remain pinned to CPython 3.14.7 x64.
