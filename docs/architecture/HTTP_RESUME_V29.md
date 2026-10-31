# V29 — Guard partial audio files against misaligned HTTP resumes

The single-stream downloader already handles HTTP 416 when an existing
`.part` file is exactly complete, and restarts once when it is stale.
That decision has been extracted without changing the accepted CDN variants:
`bytes */N`, `bytes 0-(N-1)/N` and `/N`.

**New safety guard:** a server returning HTTP 206 to a resumed
`Range: bytes=N-` request must provide a parseable `Content-Range` starting
at **exactly byte N**, with a non-reversed end and consistent known total.
A missing or mismatched range raises a clear error *before* opening the
`.part` file for appending. The existing partial bytes are preserved to
allow recovery or manual inspection; no potentially misaligned audio is
silently accepted.

This new validation lives in the HTTP- and Qt-independent module
`audioknigi/download/resume_validation.py`. Existing normal 200 responses
can still replace a stale partial from zero. HTTP 416 retries remain bounded
to one restart. The segmented Range downloader is not modified.

## Behavior-level regression coverage

`tests/unit/test_http_resume_v29.py` tests:
- old and nonstandard HTTP 416 Content-Range variants;
- complete `.part` promotion without refetching;
- aligned 206 append and aligned Content-Range whitespace variants;
- misaligned/missing 206 headers preserving partial bytes;
- a 200 response rewriting the partial safely;
- interrupted streaming, preserving bytes and resuming on the next call;
- bounded single restart following stale 416.

Existing HTTP/Range integration and historical tests continue to run.
All filenames, UI wording outside the new error, public imports and FFmpeg
paths remain unchanged.
