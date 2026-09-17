# 4.12.24 — Direct slider click and queue file revalidation

## Settings sliders

The bandwidth and event-sound-volume controls opt into `CTkSlider(jump_on_click=True)`. A click on the trough is converted to the exact scale position (respecting configured discrete steps) and stops ttk's default one-step/auto-repeat trough action. Clicking and dragging the thumb keeps the native ttk behavior.

## Queue completion revalidation

After a queue item finishes, the queue stores the actual MP3 paths that represent that completion. Before every `start_queue()`, finished items are checked locally. If every remembered file still exists and has a non-zero size, the semantic status remains `done` / `done_partial`. If a file was deleted, moved away, or became zero bytes, the item is changed to `pending` with visible status «Ожидает», then the normal queue worker can analyze and download it again.

The preflight does not contact the source site and does not infer completion from localized status text or folder names.
