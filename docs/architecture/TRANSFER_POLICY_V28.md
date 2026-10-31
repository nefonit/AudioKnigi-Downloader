# V28 — Extract HTTP transfer tuning policies

The HTTP/Range download mixin retains all actual requests, error handling,
retry logic, partial files (`.part`), segment accounting, range recovery,
cancellation of active network I/O and FFmpeg/HLS behavior.

The reusable, GUI-neutral transfer policies are now implemented in
`audioknigi/download/transfer_policy.py`:

- `BandwidthLimiter` — aggregate token bucket and cancellation-aware waits.
- `AdaptiveRangeController` — observed-speed based worker tuning, with
  existing slow/fast sample counts and cooldowns.
- `SlidingSpeedMeter` — moving speed window with counter-reset detection.

The policy implementation is moved verbatim. No download algorithm, sleep
interval, speed threshold, exception class, error message or resume-file
convention is changed.

## Compatibility

The original symbols continue to be directly imported by
`audioknigi.download.network`; the package exports in
`audioknigi.download` and historical `audioknigi.downloader` remain
available and refer to the *same classes*. Existing monkeypatches and
callers of `NetworkDownloadMixin` remain supported.

`tests/unit/test_transfer_policy_v28.py` verifies class alias identity,
cancel behavior, rate changes, adaptive worker decisions and reset-safe
speed metrics. The existing integration tests cover HTTP 416, segmented
resume, file cleanup and fallback, which are not modified by this step.

A later pass can investigate HTTP retry duplication, but that must be
supported by separate request-level regression cases. Do not mix changes
to active network I/O with this policy-only refactor.
