# Qt Migration Phase 18 — resource lifecycle and shutdown hardening

Phase 18 is a Qt-only follow-up to the post-Phase-17 code audit. It preserves the 61/61 legacy capability inventory while hardening resource ownership, network profile refresh, cancellation, URL validation and application shutdown.

## Confirmed fixes

1. `_run_ffmpeg()` and `_run_ffmpeg_capture()` unregister their `Popen` objects in `finally` and kill/communicate any still-running child before leaving.
2. `_download_segment()` obtains `get_http_session()` at each Range subrequest boundary so a browser-session generation refresh can take effect without waiting for the whole logical segment.
3. Automatic shared-source fallback updates `DownloadRequest.book` and selected indices before retrying.
4. Browser session persistence uses one condition block for profile write + generation invalidation.
5. Knigavuhe/PoleKnig cancellable pools poll at 100 ms independently of network future completion and use non-waiting shutdown on cancellation paths.
6. `is_supported_url()` validates a concrete book path, not only a supported hostname.
7. Queue serialization tolerates `None` lists; `needs_analysis` entries cannot be prioritized.
8. `closeEvent()` recognizes an existing exit request and rechecks running workers without opening a second hidden modal.
9. Missing-media cancellation exits `QMessageBox.exec()` with `reject()` without force-closing the C++ object; `clickedButton()` is guarded against deleted-object RuntimeError.
10. Windows system cues run on a daemon worker queue.
11. `MappingDataclass` field cache is safe for the non-dataclass base class.
12. Accessible polite follow-ups reuse the configured delay instead of forcing 400 ms.

## Audit claims rejected after source verification

- `text/x-python` is a dump MIME label. Real files remain `services/queue_service.py` and `services/search_service.py`.
- `task_requires_analysis` already exists and is exported from `queue_service.__all__`.
- `_split_track()` cannot reference `out` after `_track_path()` fails: that exception leaves the function before the FFmpeg block.
- `_hydrate_search_result_titles(..., cancel_event=...)` and `_hydrate_narration_variant_readers(..., cancel_event=...)` have compatible signatures.
- The final shared-source compact marker intentionally runs to EOF when the source provides no subsequent boundary; fabricating an end timestamp would risk truncating the last chapter.
- FFmpeg input-side `-ss` plus output-side `-t` remains unchanged; Phase 17 already verified this is a duration, not an absolute output timestamp.

## Release gates

- Active Qt-only tests: 91/91 before final stage documentation.
- Strict functional parity: 61/61.
- Qt import boundary: 39 project modules / 0 legacy frontend paths.
- `compileall`: PASS.
- Windows live NVDA/JAWS acceptance remains required on the exact final EXE.
