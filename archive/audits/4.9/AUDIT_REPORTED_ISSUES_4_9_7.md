# Audit of reported issues — AudioKnigi Downloader 4.9.7

This audit was performed against the complete uploaded 4.9.6 ZIP, not truncated `[source: ...]` excerpts.

## Confirmed and fixed

1. **`ActionsMixin._capture_runtime_options` partial-UI safety**
   - Confirmed as a hardening gap.
   - All Tk variables are now read through a defensive helper with runtime/settings fallbacks.
   - Missing or already-destroyed variables no longer raise `AttributeError`/`TclError`.

2. **Completion cover fallback without Pillow / cover payload**
   - Confirmed.
   - The result cover is explicitly cleared and reset to the `📘` placeholder, preventing stale artwork from a previous book.

3. **`knigavuhe._extract_call_argument` with multiple JavaScript arguments**
   - Confirmed.
   - Extraction now stops on a top-level comma as well as the closing parenthesis.
   - `BookController.enter({...}, config)` therefore feeds only the JSON object to `json.loads`.

4. **Pre-replacing `\/` before `json.loads`**
   - Confirmed as unnecessary and potentially destructive.
   - Raw JSON is now passed directly to `json.loads`, which already decodes valid JSON slash escaping.

5. **Old Knigavuhe narration layout could confuse metadata links with a reader**
   - Confirmed as a resilience issue.
   - `/author/`, `/genre/`, and `/series/` links are ignored while the parser waits for an explicit `/reader/`, `/performer/`, or `/narrator/` link.

6. **Knigavuhe search-card semantic classes tied too tightly to `<div>`**
   - Confirmed as a future-compatibility weakness.
   - `bookitem_name`, `icon_author`, and `icon_reader` are now also captured when moved to `<a>`, `<span>`, `<h3>`, or another non-div tag.

7. **First-run / Help Center localization**
   - Confirmed.
   - The first-run welcome/tagline and complete Help Center now use the selected RU/UK/DE/EN language.

8. **`SearchResult` model consistency**
   - Confirmed as an API consistency improvement.
   - `SearchResult` now inherits `MappingDataclass`, so attribute access and legacy `.get()` / `[...]` access are both supported.

9. **Image-cache initialization**
   - `AudioKnigiApp` already initialized both caches, so normal application startup was safe.
   - The mixin now self-initializes them as additional protection for partial/test hosts.

10. **Supported URLs without a scheme**
    - Confirmed.
    - Inputs such as `m.knigavuhe.org/book/...` and `audioknigi.com.ua/audio-...` are normalized to HTTPS; mobile Knigavuhe is then normalized to the desktop host.

11. **Recovery normalization control flow**
    - Confirmed as a cleanup opportunity.
    - The already-sanitized `normalization_mode` value is now used directly to synchronize the legacy boolean instead of intentionally triggering/catching missing-variable exceptions.

12. **Minor style**
    - Split `latest = updated; chosen = candidate` into two statements.
    - Removed an unused Knigavuhe parser wrapper/import.

## Reported items that were not bugs in the uploaded archive

1. **Truncated `actions.py` / `_refresh_book_timing_ui`**
   - False positive caused by an incomplete source excerpt.
   - The complete file ends the method with:
     `if threading.current_thread() is threading.main_thread(): ...`
   - `compileall` succeeds.

2. **Truncated `player.py`**
   - False positive caused by an incomplete source excerpt.
   - The uploaded file is complete (463 lines) and compiles.

3. **Truncated `tray.py`**
   - False positive caused by an incomplete source excerpt.
   - The uploaded file is complete (268 lines) and compiles.

4. **Truncated `settings_tab.py`**
   - False positive caused by an incomplete source excerpt.
   - The uploaded file is complete (540 lines) and compiles.

5. **Bearer-token regex range**
   - The claimed `.`-to-`~` range is not present in the actual regex.
   - In `[A-Za-z0-9._~+/-]`, `-` is the final character before `]`, so it is a literal hyphen, not a range operator.

6. **`FirstRunWizard._save_settings(extra=...)`**
   - False positive.
   - The real method signature is `def _save_settings(self, extra=None)`.

7. **Large `canvas.create_line(*pts)` argument list**
   - Not a practical issue here.
   - `speed_history` is a `deque(maxlen=80)`, so at most 160 coordinate scalars are passed.

8. **Image caches uninitialized during normal startup**
   - False for `AudioKnigiApp`; both caches are initialized in `app.py`.
   - Additional self-initialization was nevertheless added to the mixin.

9. **Queue runtime race**
   - Shared `runtime_*` state is architectural coupling, but the reported concurrent path is currently gated: one queue worker is allowed, `queue_running` is protected by a lock/token, and `set_busy(True)` prevents normal parallel analysis/download actions.
   - No reproducible race was found, so the downloader core was not refactored merely to satisfy a speculative warning.

10. **`pack(expand=True)` systematically pushing later buttons off-screen**
    - False as a general Tk claim.
    - Tk's packer reserves requested space for sibling widgets; an empirical 500px test with Entry-first plus three later buttons left all buttons at their full requested width.
    - Existing geometry/overflow tests also pass, so the layout was not reordered on this basis.

11. **Different Treeview click-region checks**
    - Not inherently inconsistent: some trees expose a visible tree column while the search table is configured as headings/cells.
    - No behavior regression was found.

12. **`after_cancel` called from another widget on the same Tk interpreter**
    - No failure was reproduced. Timer IDs are Tcl interpreter commands, so cancellation through another widget bound to the same interpreter is valid in this application.

## Validation

- `python -m compileall`: PASS
- Existing test suite before new audit regressions: 191/191 PASS
- Added audit regression tests: 9/9 PASS
- Combined suite after changes: 200/200 PASS
