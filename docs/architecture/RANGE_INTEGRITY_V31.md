# V31 — Prevent oversized HTTP 206 segment bodies

The segmented downloader accepts legitimate short HTTP 206 responses (some
CDNs cap their returned Range windows). It continues asking for missing bytes
from the exact saved offset. The existing `Content-Range` header checks
ensure that the advertised start matches the request and the advertised end
does not exceed the requested logical segment.

**V31 adds two more integrity checks:**

1. For `Content-Range: bytes A-B/T`, a known total `T` must exceed `B`.
   Inconsistent advertised totals are rejected before opening the segment.
2. Each streamed response must contain **no more than B-A+1 bytes**. A
   surplus byte, whether in the first chunk or a later chunk, raises
   `RangeUnsupported` instead of being silently appended.

The second check rolls the segment file back to its **size before that
response**. Previously downloaded and validated response bytes remain
intact. The coordinator's progress counter is reversed for bytes written
and then rolled back, preventing temporary overcounts.

A malformed response makes the segmented coordinator abort and use its
existing RangeUnsupported fallback path; the fallback still cleans up
untrusted segment files and uses ordinary single-stream downloading. No
change was made to the five-failure retry policy, HTTP 416 processing, HLS,
FFmpeg, cancellation, general UI messages or the public download API.

## Regression coverage

`tests/unit/test_range_integrity_v31.py` exercises correct exact and short
206 responses, oversized first/late chunks, rollback after a partial write,
preexisting segment preservation, invalid total sizes and the existing
end-of-request boundary. HTTP I/O is mocked; no external CDN is contacted.
