# AudioKnigi Downloader — audit follow-up Round 9 (2026-09-16)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND8_20260916`.

## Confirmed and fixed

- **Cloudflare proxy authority / IPv6:** centralized CONNECT/Host authority parsing. Bracketed IPv6 with an explicit port is supported, while an unbracketed numeric IPv6 literal such as `::1` is no longer mistaken for `host:port`.
- **DoH CNAME cycles:** a deterministic CNAME-loop error is re-raised immediately instead of being retried against every Cloudflare bootstrap address and hidden behind a generic resolver error.
- **Playwright session continuity:** added a shared browser-profile adapter and now restore persisted User-Agent / browser headers plus unexpired cookies in the PoleKnig and audioknigi.com.ua Playwright fallbacks.
- **Full-MP3 default template:** `{Track_Number}` and `{Track_Number}.mp3` are treated as equivalent default templates, so one-file mode keeps a book-title filename.
- **Range resume integrity:** each segmented transfer now writes a `.segments.json` signature containing source URL, total size, task count and byte ranges. Existing segment files are discarded when the signature does not match, preventing old chunks from a refreshed/fallback object being assembled into a new file. Cleanup removes the signature as well.
- **Playlist/BOM precision:** audioknigi playlist JSON accepts whitespace before a BOM, and valid `start/end` markers take precedence over a rounded duration field.
- **Track splitting:** when a non-final chapter has `start` but no usable `end/duration`, its duration is inferred from the following chapter start. The final chapter may intentionally continue to EOF.
- **loudnorm complex graphs:** trailing whitespace and semicolons are normalized before appending the measurement chain.
- **Audioknigi dash titles:** dash splitting is now conservative and only treats a plausible person-like prefix as an author. Numeric/series prefixes such as `1984` and `S.T.A.L.K.E.R.` remain part of the title.
- **Legacy queue template inheritance:** absent legacy `use_templates`/template keys deserialize to `None`, preserving the “inherit global settings” state instead of forcing templates off. Explicit stored values are still preserved.
- **History backup consistency:** history snapshots/restores are guarded by `HISTORY_LOCK` in addition to the existing atomic JSON file replacement.
- **Player Stop → exit resume:** after Qt resets a stopped player position to zero, persistence falls back to `_resume_after_stop_ms`, preventing a timer/shutdown write from deleting the just-saved resume point.
- **Easy-mode stale input:** changing the Easy input away from the currently analyzed book disables the Easy download action instead of allowing the previous book to be downloaded accidentally.
- **Output-folder synchronization:** manual path edits now debounce an unfinished-download rescan instead of leaving the banner stale until the folder chooser is used.
- **Accessibility lifetime and audit:** localized text context-menu callbacks use a weak reference to the main window. Visible `cancel_search`, `easy_cancel_search`, and `toggle_session_log` controls are now part of the required/focusable audit contract; hidden compatibility download buttons remain required for compatibility but are no longer declared keyboard-focus targets.
- **Windows media keys:** HWND normalization goes through `ctypes.c_void_p(...).value` before creating the WinAPI handle wrapper.
- **Runtime localization:** generic dynamic strings beginning with `Ошибка: ` now use the runtime-prefix catalog.

## Reviewed but not changed

- **`socket.create_connection()` and IPv6:** the report claimed a 4-element IPv6 sockaddr is required at this call site. Python's `socket.create_connection((host, port))` accepts a host/port pair and performs its own address handling, so no replacement was made there; the actual proxy-authority parsing ambiguity was fixed instead.
- **DoH `last_error is None`:** a successful DNS response, including an empty answer, returns from `_query_cloudflare_json`; the generic bootstrap-failure path is reached after exceptions, so the reported normal empty-answer `None` failure path does not match the current control flow.
- **Full-MP3 title refresh orphan:** the current retry path cleans the old `source_target` before refreshing playlist/title state, so the claimed guaranteed orphan was not reproduced.
- **PoleKnig final compact chapter:** a final shared-source chapter without an explicit end is validly represented as “start to EOF”; the download splitter supports that. No fabricated duration was introduced.
- **Package `__all__` service exports / private `_track_index`:** these are API/style concerns, not runtime failures. `DownloadRequest._track_index()` exists and is covered by previous hardening.
- **Proxy client socket leak:** `socketserver` owns and closes the accepted client request socket after the handler returns; only the separately-created upstream socket requires explicit handler cleanup.
- **`atomic_write_text` locked temp handle:** `Path.write_text()` closes its handle before `os.replace`; the `finally` block already removes a remaining temp path after replace failure.
- **Adaptive speed sample cleanup / first Range error:** current code already drains stale meter samples in a loop and preserves/raises the first worker error before the unfinished-jobs guard. These report items describe older code.
- **Backup cache overwrite:** the Qt restore workflow already suspends player persistence and reloads in-memory player/queue/history state after `restore_backup`; the additional history lock in this round is consistency hardening, not a cache fix.
- **Missing-media modal close deadlock:** current cancellation resolves the shared prompt and rejects the active box; the modal also has a cancellation watcher. No new blocking `thread.wait()` was added.
- **Sequential provider search, event-sound `deleteLater`, QAccessible binding behavior, emergency `os._exit`:** these are performance/platform/last-resort design concerns without a reproducible correctness failure in this environment. They were not changed blindly.
- **Queue row insertion / multi-URL race:** Python `list.insert(len(list), item)` appends after a pop, and queue addition runs synchronously before scheduling the next dropped URL. The specific corruption described in the report was not reproduced.
- **UI-scale 125% migration:** explicit saves are already stamped with the migration marker (fixed in Round 2), so deliberate modern 125% settings are not reset by the current save path.

## Verification

- `pytest -q`: **271 passed**.
- Focused Round 9 regressions: **9 passed**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`).
- Undefined-global audit: **OK (77 modules)**.
- Unused-import audit: **OK (32 implementation modules)**.
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`; static UI literals, help topics, onboarding and accessible names complete.
- Full parity audit: **PASS 61/61**.
- Qt import audit: **OK (73 project modules reachable, no legacy frontend path)**.
- Historical regression audit: **PASS**, 270 historical checks passed; known shape incompatibilities remain explicitly tracked.

Windows/PySide6 frozen-runtime behavior still needs the real Windows build/self-test; Linux CI here can validate source/import/static contracts but cannot substitute for the user's Windows Qt/PyInstaller run.
