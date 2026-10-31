# V30 — Transient HTTP Range retry behavior

The segmented Range worker already retries temporary HTTP 429 and 5xx
responses up to five consecutive requests without progress, while HTTP
404/410 propagate immediately for source refresh. Responses that carry
partial audio bytes remain recoverable at the newly saved file offset.

V30 adds a small pure policy module at
`audioknigi/download/range_retry.py`. It interprets Retry-After as
seconds or an HTTP-date and may lengthen the existing exponential-like
0.15–1.0 second delay, **never beyond the existing one-second cap**.
Invalid, past, non-finite or negative values use the old delay. This keeps
user/peer cancellation latency bounded and avoids server-provided
indefinite waits.

When an HTTP 429 or 5xx response has a Retry-After header, the next
Range request observes that bounded hint. The existing five-failure limit,
512-request ceiling, exception types, UI wording, response cleanup and
cancel-event logic remain unchanged. Other network errors retain the
original delay; 404/410 are not retried.

## Regression tests

`tests/unit/test_range_retry_v30.py` verifies default and hinted delays,
HTTP-date parsing, temporary status sequences (429, 500, 502, 503),
preservation of pre-existing segment bytes, immediate 404/410 propagation,
interrupted streaming followed by an offset-correct retry, the five-failure
limit and cancellation during the retry wait. All tests use local fake
responses without contacting any real service.

The ordinary single-stream HTTP 206/416 resume checks introduced in V29
are unaffected. No other download or media-processing paths change.
