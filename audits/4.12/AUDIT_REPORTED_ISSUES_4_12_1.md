# Audit of reported 4.12.0 issues — 4.12.1

The uploaded 4.12.0 archive was inspected as complete source files, not as truncated `[source: ...]` excerpts.

## False truncation / syntax reports

The reported endings `if required >`, `canvas.`, `def toggle_queue_pause(self):`, and the partial `queue_start_btn` line are not present as incomplete code in the archive. `python -m compileall` succeeds. `LibraryVisualMixin._photo_from_payload`, `QueueMixin.toggle_queue_pause`, and `queue_tab.py` are complete.

`HAS_CUSTOMTKINTER` is intentionally always `False` in the current native Tk/ttk UI layer. `CTkButton`, `CTkFrame`, etc. are compatibility wrapper names implemented by `ui_kit.py`; `bootstyle`, `fg_color`, and related options are translated there rather than passed to real CustomTkinter widgets.

Queue Drag-and-Drop is registered centrally by `DndMixin._setup_dnd()` in `audioknigi/dnd.py`, including `queue_drop_label`. The main window therefore does not need to inherit `TkinterDnD.Tk`; the adapter loads tkdnd and attaches the wrapper API to the native widgets.

The reported custom ttk styles are registered by `ui_kit.apply_native_styles()`. Track Treeview callbacks accept Tk event arguments.

## Confirmed and fixed

1. **Help topic lookup used translated titles.** Help navigation now passes stable i18n keys. A backward-compatible title fallback remains for old callers.
2. **PoleKnig search could prefer service labels** such as `Слушать онлайн`, `Скачать`, or `Подробнее о книге` because the shortest candidate won. Known short action labels are now filtered without broad prefix matching that could hide legitimate book titles.
3. **PlayerJS property regex could match `file:`/`playlist:` inside quoted text.** Property extraction now validates that a match is outside JavaScript strings and comments before reading its value.
4. **Queue drag bbox assumptions were unnecessarily loose.** Motion and release paths now verify bbox tuple length before indexing so partially visible/malformed geometry does not abort useful drag feedback.

## Reviewed, no code change required

- Clearing a Tk/ttk image with an empty Tcl image name is a standard operation; the legacy CustomTkinter branch is unreachable in this build and is exception-protected.
- Accessibility sibling lookup intentionally suppresses an announcement position when a row disappears during a live Treeview mutation; it does not use an invalid index.
- `pygame-ce` is intentionally imported as `pygame`, which is its supported drop-in namespace.
