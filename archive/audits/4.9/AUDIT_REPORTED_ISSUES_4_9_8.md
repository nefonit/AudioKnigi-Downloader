# Audit of reported issues — 4.9.8

This report checks the complete uploaded 4.9.7 archive rather than truncated `[source: ...]` excerpts.

## Confirmed and fixed

1. **Queue pause button label** — confirmed. The worker restored the resume event but did not always restore the visible label from `ПРОДОЛЖИТЬ` to `ПАУЗА`. 4.9.8 resets it in the worker `finally` block.
2. **Unicode dash relevance bonus** — confirmed. `_title_score()` only recognised `" - "`. It now treats spaced `-`, `–`, and `—` consistently.
3. **`None` values in history** — confirmed. `_add_history()` could preserve `None` for optional metadata. It now normalises `None` to the requested default (normally an empty string), preventing JSON `null` and accidental `"None"` UI text.
4. **Decoded Pillow image payloads** — confirmed as a robustness gap. `_photo_from_payload()` now accepts either encoded image bytes or an already decoded `PIL.Image.Image`.
5. **Easy-mode Drag-and-Drop target** — confirmed. `easy_drop_label` existed but was not managed by `pack/grid`, so it was an unsuitable DnD target. The already visible text “Ссылку можно перетащить из браузера.” is now the registered target.
6. **Quality-card Configure churn** — hardened. `wraplength` is now updated only when the card width meaningfully changes, avoiding redundant geometry updates.
7. **Easy-mode timer cleanup** — hardened. The scheduled layout callback is cancelled through the widget that owns the timer when available.

## Reported issues that do not reproduce in the complete archive

1. **`actions.py` truncated at `context_redownload_part`** — false positive from a truncated source view. The method is complete and uses `_current_tree_track()`.
2. **First-run wizard truncated in `finish()`** — false positive. `onboarding.py` is complete and safely focuses `easy_url_entry` when present.
3. **`tray.py` truncated / `RLock` not instantiated** — false positive. The complete file contains `threading.RLock()` and a complete `notify()` implementation.
4. **`settings_tab.py` truncated in imports** — false positive. The file is complete and compiles.
5. **Missing `customtkinter` dependency** — not applicable. `ui_kit.py` intentionally exposes CTk-compatible names implemented by the project's own native Tk/ttk compatibility layer. It consumes/translates `bootstyle`, `fg_color`, `text_color`, etc.; external CustomTkinter is not required.
6. **`SearchMixin.use_selected_search_result()` calls a nonexistent `analyze()`** — false positive. `ActionsMixin` defines both `analyze()` and `_begin_analysis()`; the search call is valid.
7. **Queue drag `bbox` returns `""` instead of bool** — already handled. Both drag paths explicitly wrap the expression with `bool(...)`.
8. **Immediate `grab_release()` after `tk_popup()`** — current code follows the standard Tkinter popup pattern and avoids stale grabs. No reproducible closing bug was found.
9. **`canvas.create_line(*pts)` grows without bound** — false premise. `speed_history` is `deque(maxlen=80)`, limiting the call to at most 160 coordinate values; this is trivial for Python/Tk.
10. **Treeview double-click region mismatch** — intentional. Search uses `show="headings"`, while History/Queue expose the tree column (`#0`), so their accepted hit regions differ by design.
11. **ttk Notebook inside a CTk container necessarily conflicts with themes** — not reproduced. Here `CTk*` names are the project's native compatibility widgets, not external CustomTkinter canvas widgets.

## Validation

- `python -m compileall -q audioknigi tests` — OK
- `python audioknigi_gui.py --ci-selftest` — `CI SELFTEST: OK (4.9.8)`
- Full regression suite under Xvfb — **206 passed**
- Added 6 dedicated regression tests in `tests/test_audit_498.py`
