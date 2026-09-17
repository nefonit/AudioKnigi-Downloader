# Audit of reported issues — AudioKnigi Downloader 4.12.2

The complete uploaded 4.12.1 ZIP was inspected. The source-fragment reports mixed real edge cases with truncation artifacts. `python -m compileall` succeeds, so the reported `book = self._`, dependency-text prefixes, unfinished `_current_tree_track`, unfinished queue drag method, and truncated `ui_kit.py` are not present in the actual archive.

## Confirmed and fixed

- **Accessibility root label lookup:** `_nearby_label()` now exits before `nametowidget()` when a root widget has no parent name.
- **Repeated AccessibilityManager installation:** `install()` is idempotent and does not create parallel 5-second screen-reader poll chains.
- **Screen-reader duplicate debounce:** suppressed duplicate focus messages now refresh the debounce timestamp, preventing speech every ~400 ms during a 200 ms focus storm.
- **Dependency panel:** tray availability uses nested `getattr`, so a partially constructed tray object cannot raise `AttributeError`.
- **Clipboard offer dialog:** a modal-open guard prevents FocusIn events from scheduling another clipboard prompt while `askyesno()` is active.
- **Drag-and-Drop startup safety:** the main drop handler uses `getattr(..., False)` for `busy`.
- **Knigavuhe metadata hydration:** a missing author is resolved even if the search card already contains a narrator; this prevents valid author matches from being filtered out.
- **Help Center aliases:** all ten short topic names are mapped (`download`, `search`, `queue`, `settings`, `m4b`, `quality`, `files`, `transfer`, `failure`, `shortcuts`).
- **First-run localization:** the new 4.12 onboarding start screen is translated in Russian, Ukrainian, German and English, including the post-wizard hint.
- **Player resume at the beginning:** seeking below three seconds clears an older saved position rather than preserving a stale resume point.
- **M4B/M4A/AAC playback:** the normal Play action now uses the same external-player route as `player_play_file()`.
- **History cover lookup:** an empty `folder` no longer means `Path("")`/current working directory, so a random `cover.jpg` beside the app cannot become every history entry's cover.
- **PoleKnig title candidates:** real descriptive titles are preferred over catalogue badges such as `Новинка`, `Хит`, `Глава 1`, etc.
- **PoleKnig unquoted PlayerJS arrays:** fallback parsing uses balanced object literals and tolerates nested objects and braces inside strings/comments.
- **CTkOptionMenu runtime width:** `configure(width=...)` now converts historical pixel widths to native ttk character units just like the constructor.
- **CTkScrollableFrame geometry reconfiguration:** `pack_configure`, `grid_configure`, and `place_configure` proxy to the outer public viewport.
- **pygame close path:** shutdown now checks the `mixer` attribute defensively before stopping/quitting it.

## Reported as critical, but not present in the real ZIP

- `ActionsMixin._analysis_worker` is complete; it does not end at `book = self._`.
- No `requirements.txt` line is concatenated with a Python import. `prismatoid>=0.17.3; platform_system == "Windows"` is correctly located in `requirements.txt`.
- `_current_tree_track()` is complete.
- `NarrationVariant` does have `available: bool | None = None`.
- `Book` does have `restricted: bool = False`.
- `_download_with_resume()` exists in `DownloaderMixin` and `_download_source_with_fallback()` is complete.
- `_queue_drag_release()` contains the complete move/refresh/selection logic.
- `ui_kit.py` is complete and contains `apply_tree_zebra()`.
- `customtkinter` is intentionally not a dependency. The `CTk*` names are compatibility wrappers implemented by this project on top of native Tk/ttk; `bootstyle`, `fg_color`, and similar historical arguments are translated/filtered by `ui_kit.py`.
- The player timer is started by `AudioKnigiApp` (`after(500, self._player_tick)`).

## Reviewed and intentionally unchanged

- The simple-mode confirmation card and its status anchor are siblings in the same container and both use `pack`, so the reported `pack`/`grid` conflict is not present in the current UI.
- PoleKnig metadata hydration does **not** launch 100 simultaneous requests; its executor is bounded (currently at most 8 workers). A broad search can still require many total detail requests because Author/Reader metadata is intentionally shown for results. This can be revisited with caching/lazy hydration if the live site starts returning 429 responses.
- `safe_name()` checking the first dot-separated component is conservative for Windows reserved device names (for example `CON.txt` is reserved); changing it to the final suffix is not safer.
- `set_button_active()` keeps a legacy color fallback after the native ttk style path. Under the current native wrapper the style path succeeds, so the fallback is harmless and preserves compatibility.
- The current DPI/scaling path multiplies the startup Tk DPI baseline and then reapplies accessible ttk styles. Existing scale/theme regression tests remain green; there is no demonstrated double-scaling defect to justify changing this behavior.
- The Windows PowerShell toast fallback remains best-effort behind `plyer` and is exception-isolated; lack of an AUMID on a particular Windows build cannot crash the application.

## Verification

- 15 new focused tests for the 4.12.2 changes pass.
- 275 pytest regression tests pass when GUI-heavy groups are isolated to avoid cumulative Tk interpreter teardown effects under Xvfb.
- 25 legacy executable smoketest files pass with `PYTHONPATH=.` under Xvfb.
- `python -m compileall -q .` passes.
- `python audioknigi_gui.py --ci-selftest` reports `CI SELFTEST: OK (4.12.2)`.
