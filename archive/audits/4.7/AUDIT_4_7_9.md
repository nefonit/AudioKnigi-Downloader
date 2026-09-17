# Audit 4.7.9

This audit was performed against the uploaded 4.7.8 ZIP.

## Confirmed and fixed

1. **Auto-download busy-state handoff** — confirmed. The previous code cleared
   `auto_download_after_analysis` before `finally`, so `set_busy(False)` could
   run before the queued download/dialog started. 4.7.9 uses an explicit local
   handoff state.
2. **Worker-safe output mode** — hardened. `_book_outputs_complete()` now reads
   only the runtime copy captured on the Tk thread.

## Reported issues that were not present in the uploaded ZIP

1. **`core.py` truncated USER_AGENTS / syntax error** — not present. The exact
   uploaded file compiles successfully.
2. **`CTkButton.configure(style=...)` incompatible** — not present in the
   current universal-accessibility UI because public `CTkButton` is deliberately
   a native `ttk.Button`. 4.7.9 nevertheless adds an adaptive styling helper so
   the same code remains correct if the implementation later changes back to a
   real CustomTkinter button.

## Regression coverage

`tests/test_audit_479.py` simulates delayed Event Bus callbacks and verifies:
- no transient busy-state release during auto-download handoff;
- busy state is released on analysis failure;
- manual analysis still releases busy state;
- duplicate dialog releases/transfers busy ownership correctly;
- adaptive button styling supports native ttk and future CTk-like controls.
