# Round 67 — Round 66 audit follow-up

Applied confirmed findings from the 2026-09-29 review:

- fixed a segmented-download deadlock: adaptively parked workers now exit once the monotonic Range-job queue is empty instead of sleeping forever after active workers consume the last jobs;
- preserved `0.0` as a valid `next_start` boundary in shared-source timeline diagnostics;
- removed the unreachable second whole-path collapse branch in support-bundle path sanitization;
- split string-form `selected_indices` such as `"1, 2, 3"` in unfinished `resume.json` manifests, matching queue parsing behavior;
- preserved explicit `created_at=0.0` values when loading current and legacy queue records;
- report an explicit DNS no-records error instead of `...: None` when both IPv4 and IPv6 policy resolution return no addresses.

Reviewed and intentionally unchanged:

- Qt download callbacks invoked from FFmpeg split worker threads are `Signal.emit` callbacks supplied by `DownloadWorker`, so Qt marshals them safely to the receiver thread;
- runtime localization already evaluates regex rules before prefixes, so overlapping download-status prefixes do not shadow the richer translations;
- broader German Du/Sie and Ukrainian terminology cleanup is editorial rather than a runtime defect and is deferred to a dedicated localization pass;
- CSV formula-prefix escaping is intentional export hardening;
- `safe_int(bool)` remains unchanged because persisted index consumers already reject booleans explicitly and changing the shared helper could alter unrelated established behavior;
- Qt 5 compatibility is outside the Qt 6 / PySide6 project contract.
