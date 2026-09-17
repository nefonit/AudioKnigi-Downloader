# AudioKnigi Downloader 4.7.4 — audit disposition

## Fixed in 4.7.4

- Keyboard focus decoration in `easy_home.py` no longer raises runtime errors if a dynamic widget cannot accept CustomTkinter border options.
- Friendly download-speed preset follows manual `segment_count_var` changes; old trace callbacks are removed on rebuild.
- `queue_url_var`, `search_query_var` and queue drag state are created once by the app and reused by tabs.
- Queue/history Treeviews use `show="tree headings"`.
- Track context menu uses `app.tree` as an explicit Tk widget master.
- Child `<Unmap>` events cannot trigger minimize-to-tray.
- `extract_metadata_from_html(None, ...)` is safe.
- Audiobookshelf URLs without a scheme are normalized to `http://`; non-HTTP(S) schemes are rejected.
- Windows toast text is XML-escaped and Base64 transported; user/book text is not embedded in executable PowerShell syntax.
- `MappingDataclass` exposes only declared dataclass fields as mapping keys.
- Closing the first-run wizard does not set `first_run_complete`.
- Player-position lock initialization, snapshots and dictionary mutations are synchronized; asynchronous persistence and synchronous shutdown flush remain.
- Corrupt `bandwidth_limit` values recover to `0.0` instead of aborting UI settings restoration/startup.
- Template track title `0` is preserved; folder fallback remains inside a dedicated subfolder.
- Fallback widgets translate CustomTkinter `orientation` to ttk `orient` and preserve button `compound`.
- Tooltip teardown handles CustomTkinter internal widgets without leaving stale tips.
- Tray hide performs a late asynchronous stop retry for backends that ignore an early stop.
- Privacy log sanitization does not replace a filesystem root as the home directory.

## Verified as already correct / not a bug in the supplied 4.7.3 archive

- `AudioKnigiApp` inherits `CTk`/`Tk`; therefore `tk.Menu(app, ...)` was valid. 4.7.4 still uses the more explicit `app.tree` master.
- `dnd.py` is complete and compiles.
- `_disk_free_for_path` exists in `DownloaderMixin` and is used by `download_full`.
- `resource_path(...parent.parent)` is correct for this repository layout because `assets/` is at the project root, one level above the `audioknigi` package.
- `SearchMixin._search_worker` calls `set_status`, but `set_status` itself posts through the thread-safe UI event bus and does not mutate Tk directly from the worker.
- Audiobookshelf scan timeout was already 120 seconds in 4.7.3.
- Empty/directory cover paths were already rejected with `Path.is_file()`.
- The tray manager already used generation-local start/stop events; 4.7.4 adds another late-stop safeguard.
- Runtime Book/Track code already used typed attribute access in the main download paths.

## Regression coverage

`tests/test_audit_474.py` covers the audit-specific cases and is included in both CI and release workflows.
