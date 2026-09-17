# AudioKnigi Downloader 4.12.31 — deep concurrency and lifecycle hardening audit

## Scope

This audit follows the full-project review of the active 4.12.31 runtime. Historical code under `history/` remains archival and is not treated as executable current code. The hardening pass focused on concurrency, Tk thread ownership, shutdown, persistence, subprocess lifecycle, modal ownership and import-time robustness.

## Confirmed issues fixed

1. **Concurrent operation ownership**
   - Analysis, selected-part download, full download, recheck and queue paths previously shared `cancel_event`, `runtime_*` state and `current_book` without one cross-module owner.
   - Added an exclusive operation lock/generation token in `ActionsMixin` and initialized it in `AudioKnigiApp`.
   - A second operation cannot start while another operation owns shared state and cannot clear the first operation's cancellation event.
   - Auto-analysis-to-download uses an explicit ownership handoff instead of dropping and reacquiring the guard.

2. **Stale search results**
   - Search now uses `_search_generation`; only the latest generation can publish results.
   - Search-result actions refuse to replace the current book while the application is busy.

3. **Stale cover preview**
   - Cover loading now carries a cover generation and book identity.
   - A delayed cover from an older book is rejected before it can update the visible cover widget.

4. **Atomic `current_book` publication**
   - Analysis no longer assigns `current_book` from the worker before the UI catches up.
   - The model assignment and `_show_book()` publication now occur together through the UI event path after an operation-token validity check.

5. **Blocking FFprobe in the player**
   - Player duration probing moved off the Tk thread.
   - A player-load generation rejects stale duration probes if the user switches files before the worker completes.

6. **Non-cooperative audio probing**
   - `_probe_audio_info()` was migrated from blocking `subprocess.run()` to managed `Popen` polling.
   - Cancellation is checked during the probe and the process is registered for shutdown cancellation.

7. **Shutdown/network/subprocess lifecycle**
   - `on_close()` now signals cancellation, closes active HTTP responses, cancels active media subprocesses and gives registered workers a short cooperative shutdown window.
   - Background workers started through the shared helper are registered and removed automatically when they finish.

8. **History race**
   - History mutation/persistence is protected by a re-entrant history lock so UI actions and download completion cannot silently overwrite each other.

9. **Persistence success reporting**
   - `save_json()` now returns a success value and supports `raise_errors=True`.
   - Critical restore paths use strict writes so the UI does not report a successful restore when a required file cannot actually be written.

10. **Logging startup robustness**
    - Import-time logging setup now falls back safely if the configured application log directory/file cannot be created.
    - Logging failure no longer prevents application startup.
    - `audioknigi.__init__` lazily exposes `AudioKnigiApp`, so importing model/core modules does not eagerly import the full GUI and logging stack.

11. **Native file-dialog ownership**
    - All active `filedialog` calls now have an explicit `parent=`, completing the earlier modal-ownership hardening that already covered all `messagebox` calls.

12. **Screen-reader polling on the Tk thread**
    - Periodic reader detection no longer runs the heavier Windows process diagnostic directly on the Tk callback path.
    - Backend refresh runs in a daemon worker and publishes the result back through the UI scheduling path.

## Additional Tk-thread defect found during implementation

Two analysis-worker paths still called `_show_easy_action()` directly. They were converted to `self.ui(...)`, eliminating direct Tk/UI mutation from those background paths.

## Main implementation files

- `audioknigi/actions.py` — operation ownership, worker registry, shutdown coordination, atomic book publication, cover generation, modal ownership.
- `audioknigi/app.py` — shared locks/generations/registries.
- `audioknigi/search.py` — search generation and stale-result rejection.
- `audioknigi/player.py` — asynchronous duration probe and stale-player probe rejection.
- `audioknigi/downloader.py` — cancellable/registered subprocess handling and cooperative audio probe.
- `audioknigi/storage.py` — history locking, strict restore persistence and file-dialog parents.
- `audioknigi/core.py` — `save_json()` result/strict mode.
- `audioknigi/logging_utils.py` — fail-safe startup logging.
- `audioknigi/accessibility.py` — non-blocking periodic screen-reader refresh.
- `audioknigi/queue_manager.py` — queue ownership integration.
- `audioknigi/__init__.py` — lazy `AudioKnigiApp` import.

## Regression coverage

Added `tests/test_deep_audit_hardening_41231.py`, including focused checks for:

- double download start and cancellation-event clearing;
- exclusive operation ownership across operation kinds;
- stale search rejection;
- busy-state protection for search-result actions;
- stale cover rejection;
- UI-thread publication of `current_book`;
- asynchronous player duration probing;
- cooperative `Popen` audio probing;
- strict JSON persistence errors;
- lazy package import;
- logging import with an unwritable home;
- shutdown interruption of network/subprocess/workers;
- no `tasklist` work on the periodic Tk accessibility path.

`tests/test_modal_ownership_41231.py` was extended to assert that all active Tk file dialogs have explicit parents. Existing architecture/threading/audit tests were adapted to the new operation-token/worker-registry implementation without weakening their behavioural assertions.

## Validation

- `python -m compileall` for active application/tests: **PASS**.
- Focused deep-hardening regression set: **17/17 PASS**.
- Updated legacy/compatibility checks: **56/56 PASS**.
- Complete active regression suite after hardening: **461/461 PASS**.
- Full suite was completed in independent groups after the micro-hardening follow-up: **86 + 173 + 109 + 93 = 461/461 PASS**.

## Micro-hardening follow-up from external review

A later review raised four minor points. They were revalidated against the post-hardening source rather than accepted blindly:

- The reported missing `parent=self` in `choose_folder()` was already fixed; regression coverage confirms every active `filedialog` has an explicit owner.
- Temporary-source cleanup was refined to ignore `FileNotFoundError` specifically. This avoids debug noise when an earlier stage already removed/moved a source while preserving an accurate `removed_sources` count. A literal `unlink(missing_ok=True)` was intentionally not used because the existing post-call increment would otherwise count a non-existent file as removed.
- `i18n.tr()` keeps its current fail-visible `value.format(**kwargs)` + warning behavior. Instead of masking future translation mistakes, regression coverage now parses every translated value and verifies placeholder sets are consistent across RU/UK/DE/EN. Current result: 85 keys, zero parse errors, zero placeholder-set mismatches.
- The PyInstaller/Windows hidden-subprocess implementation was rechecked and already correctly uses `CREATE_NO_WINDOW` plus hidden `STARTUPINFO`; no code change was required.

Focused follow-up tests: **19/19 PASS** before the complete regression run.

## Result

All confirmed issues from the deep audit are addressed in the active 4.12.31 codebase. The project now has explicit ownership for shared long-running operations, stale-result protection for asynchronous UI data, cancellable media subprocesses, safer shutdown and persistence semantics, and stronger guarantees that Tk mutations remain on the UI path.
