# 4.12.17 — Bulk Part Selection & One-Button Mini-Player

## Advanced Book tab: bulk selection

`Выбрать все` and `Снять все` are now placed directly above the parts table. The actions update the `Track.selected` model state and the visible checkbox glyph (`☑` / `☐`) for every row in one pass. This makes the common “download only one part from a 100-part book” workflow two clicks: **Снять все**, then select the one required row.

The controls are disabled until a book with tracks is loaded and are disabled again while an operation is busy.

## Mini-player: one Play/Pause control

The advanced-mode mini-player renders a single primary button instead of separate Play and Pause buttons. Its UI state follows playback state:

- stopped/not started: `▶ Воспроизвести`;
- actively playing: `⏸ Пауза`;
- paused: `▶ Воспроизвести`;
- resumed: `⏸ Пауза`;
- stopped or naturally completed: `▶ Воспроизвести`.

A paused stream is resumed with `pygame.mixer.music.unpause()`, so the current playback position is preserved. `■ Стоп` remains a separate control.

`player_pause_btn` is retained as a compatibility alias to `player_play_btn`; only one visible Play/Pause button exists.
