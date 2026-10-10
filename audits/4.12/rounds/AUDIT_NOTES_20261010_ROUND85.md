# AudioKnigi Downloader 4.12.42 — Round 85 audit follow-up

Date: 2026-10-10

## Confirmed fixes

- `download/network.py`: when a segmented attempt reports `RangeUnsupported`, discard any stale ordinary `.part` before falling back to `_download_single`; a stale single-stream offset must never be resumed after the server has rejected Range semantics.
- `download/media.py`: cancellation of `_probe_audio_info` now uses one cleanup owner so `ffprobe` is killed and reaped with `communicate()` in `finally`.
- `download/errors.py`: `SharedSourceTimelineError.issue` now always exposes normalized `track_indices`; the legacy/specific `track_index` field remains available when supplied.
- Qt/runtime localization: removed leading-space tray catalog duplicates and the leading-space DNS-advice key. Spacing is now composed explicitly by Python code, while localization keys contain only semantic text.

## Reviewed findings that did not justify runtime changes

- Range worker `jobs.task_done()` is already in `finally`, so `return` from the exception path still accounts for every dequeued job. The coordinator checks the preserved first error before the secondary `jobs.empty()` guard.
- The loudnorm parser already scans opening braces right-to-left and `JSONDecoder.raw_decode()` accepts valid JSON followed by diagnostic text. A regression test now covers a valid loudnorm object followed by a malformed trailing brace.
- `AppSettings.__setitem__` intentionally performs one-key schema normalization. Existing tests verify that unrelated deleted defaults are not resurrected and legacy aliases update only canonical fields. The reported concern is performance/architecture, not a correctness defect.
- A response cannot be registered before `requests.Session.get()` returns it; cancellation during connect/handshake is therefore bounded by the configured connect timeout. This is a requests API limitation rather than a leaked registered response.
- Qt accessibility self-test already passes an explicit filtered argv list (`[program, -platform, offscreen]`) to `create_application`, so custom self-test flags are not forwarded to Qt.
- Duration caches are bounded and local-file keys include resolved path, size and nanosecond mtime. The same-size/same-mtime replacement scenario is an unusual filesystem-coherency limitation and was not changed without evidence of a runtime failure.
- Runtime regex capture indices, CRLF matching, Smart Format/Auto-Chunker strings, and currently reported dynamic book-flow messages match their catalogs.
- Track-status translations intentionally exist at different localization layers for canonical status IDs and legacy visible literals; current precedence/tests show no conflicting rendered result.

## Regression coverage added

- stale `.part` removal before RangeUnsupported single-stream fallback;
- dequeued Range jobs remain protected by `finally: jobs.task_done()`;
- cancelled ffprobe is killed, communicated/reaped, unregistered and pipes are closed;
- loudnorm parsing survives malformed trailing braces after valid JSON;
- shared timeline errors expose normalized `track_indices`;
- tray/DNS localization no longer needs keys with leading whitespace.

## Validation baseline

- Total collected tests: **927**.
- Integration cases: **884**.
- Runnable tests in this environment: **925 / 925 passed**.
- The remaining **2** Qt accessibility self-tests fail only because PySide6 is not installed in the validation environment (`ModuleNotFoundError: PySide6`).
- Full Parity: **61 / 61 PASS**.
- Qt import/localization, exception, unused-import, undefined-global and historical-regression audits: **PASS**.
- `compileall`: **PASS**.
- Strict non-archive project JSON parse/duplicate-key check: **11 / 11 PASS**.
