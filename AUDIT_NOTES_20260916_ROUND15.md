# AudioKnigi Downloader — audit follow-up Round 15 (2026-09-16)

Base: `AudioKnigi_Downloader_v4_12_42_REPORT_FIXES_ROUND14_20260916`.

The second pasted audit supplied during this round was byte-for-byte identical to the first one (same SHA-256), so it introduced no additional findings.

## Confirmed and fixed

- **Source-cache cleanup is now ownership-safe.** `_clear_stale_source_downloads()` no longer uses the broad `_source*.mp3*` / `_repair_*.mp3*` globs. It removes only engine-owned `_source`, numbered `_source_N`, and `_repair_source_N` artifacts plus their known `.part/.assembling/.segments.json/.segNNN` companions. A legitimate file such as `_source of wisdom.mp3` is preserved.
- **Atomic text sidecars tolerate transient Windows sharing violations.** `atomic_write_text()` retries `os.replace()` on `PermissionError` with a short bounded backoff, covering antivirus/indexer races while retaining atomic replacement semantics.
- **Audio-info cache eviction is defensive.** Bounded cache eviction uses a defaulted `next(iter(...), None)` path instead of assuming a key always exists.
- **Incomplete two-pass loudnorm statistics degrade safely.** Missing first-pass fields no longer abort the book. The engine logs a localized warning and falls back to the safe single-pass loudnorm filter, matching the existing non-finite-statistics fallback policy.
- **Range progress localization accepts spacing variations.** The `Range X/Y • ...` runtime rule now tolerates one or more spaces around bullets and `ETA`, like the already-flexible single-download progress rule.
- **Duration-probe cancellation kills registered ffprobe children before waiting for the pool.** `BookAnalysisService` tracks its duration-probe subprocesses, kills live children on cancellation, then performs the bounded executor shutdown so cancellation does not wait on a remote ffprobe timeout.
- **Legacy queue recovery preserves old cover/normalization state.** Flat legacy tasks now decode a base64 `cover_cache` (including optional data-URI prefix) and map `normalize_audio=true` to `normalization_mode="single"` when the canonical mode is absent.
- **Full-MP3 queue rows report one output file.** `_queue_parts_count()` returns `1` for `download_mode="full_mp3"` instead of displaying the source chapter count.
- **Clipboard prompt suppression compares canonical supported URLs.** An internally copied URL remains suppressed even if HTTP/HTTPS, trailing slash, or canonicalization changes the textual representation.
- **History deletion refreshes accessibility metadata.** After removing a history record, the table is reloaded before focus restoration so every shifted row receives a fresh `AccessibleDescriptionRole` instead of retaining stale row metadata.

## Reviewed but not changed

- **PoleKnig `last_page` UnboundLocalError claim:** not reachable in the current function. Any exception before `last_page` assignment immediately returns `[current]`; execution cannot continue to `if last_page > 1` with an unbound variable.
- **PoleKnig list-comprehension `v` claim:** `v` is the local target of `for i, v in enumerate(...)`; it is declared by the comprehension and is not an undefined name.
- **`availability="available"` syntax:** standard Python keyword-argument syntax, not a formatting/syntax bug.
- **DoH cache mutation claim:** reads and mutations of `_CACHE` are already serialized by `_CACHE_LOCK`; the reported concurrent dictionary mutation path is not present.
- **`{Output_Dir}` in `render_folder()`:** intentionally not expanded to the absolute base path inside the relative folder template. Substituting `base_dir` there would duplicate the output root when the rendered relative template is joined back to `base`.
- **Requests streaming timeout claim:** `timeout=(connect, read)` applies the read timeout to socket read operations throughout `iter_content()`, not only to the first response byte. An extra wall-clock deadline was not added because it would also terminate legitimately slow transfers.
- **Adaptive Range parked-worker deadlock claim:** active workers keep consuming the shared queue until it is empty; parking only higher worker IDs does not make the active workers exit while unclaimed jobs remain. No `jobs.join()` dependency exists.
- **Support-bundle queue container claim:** the current `QueueStore.save()` persists `qt_queue.json` as a top-level list, which is exactly the format consumed by the support-bundle summary. No versioned `{items: ...}` wrapper is currently written.
- **Headless-engine UI-thread claim:** `_DownloadEngine` has no `_refresh_book_timing_ui`; therefore the optional `hasattr()` guarded callbacks in `BookFlowMixin` are not executed by the headless Qt worker engine.
- **Queue status localization:** the UI renders persisted status strings through `_rt(...)`/canonical status handling; Russian persistence text does not force Russian display in non-Russian UI.
- **Global media-key teardown:** normal `closeEvent()` already calls `media_filter.shutdown()` before accepting/destroying the window, and deferred process exit has a bounded emergency fallback.
- **Missing-media modal shutdown:** `_request_download_cancel()` resolves the active prompt and calls `box.reject()` before deferred exit hides the main window, which is the existing anti-deadlock contract.
- **System-sound shutdown:** the `MessageBeep` worker is explicitly a daemon thread; a blocked OS audio call cannot keep the Python process alive by itself.
- **Search/track header localization after language change:** the product currently tells the user that the language change is fully applied after restart. Immediate dynamic header relabeling was therefore not introduced as a separate partial-live-language mode.
- **WMF stop/resume timing proposal:** not changed without a reproduced Windows failure. Earlier Windows-hardening contracts deliberately retained the current direct seek behavior; speculative timer/state changes could reintroduce older regressions.

## Verification

- Focused Round 15 regressions: **10 passed**.
- `pytest -q`: **332 passed**.
- Historical regression audit: **PASS**, 270 historical checks passed with 113 known shape incompatibilities tracked.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=111`).
- Undefined-global audit: **OK (77 modules)**.
- Unused-import audit: **OK (32 implementation modules)**.
- Qt localization audit: **OK** for `ru`, `uk`, `de`, `en`; static UI literals, help, onboarding and accessible names complete.
- Full parity audit: **PASS 61/61**.
- Qt import audit: **OK (73 project modules reachable, no legacy frontend path)**.

The real frozen Windows/PySide6/PyInstaller gate still requires the Windows build environment; source/static Linux checks do not replace it.
