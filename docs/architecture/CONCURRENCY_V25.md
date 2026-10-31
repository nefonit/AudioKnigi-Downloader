# V25 — Shared cancellable futures

The active source parsers and book analysis service previously contained three
copies of identical completion polling logic. Two source parsers also duplicated
the same non-blocking executor shutdown helper.

The single implementation now lives in `audioknigi/engine/concurrency.py`:

- `iter_completed_cancellable(futures, cancel_event=None)`: yields completed
  futures, checks cancellation between 100 ms polling intervals, cancels
  pending futures and raises the existing `Cancelled` exception with the same
  Russian text. It does not force-cancel already running network operations.
- `shutdown_pool_now(pool, futures)`: cancels unfinished tasks and invokes
  `shutdown(wait=False, cancel_futures=True)`, preserving the previous
  non-blocking shutdown behavior.

`audioknigi.parsers.poleknig`,
`audioknigi.parsers.knigavuhe`, and
`audioknigi.services.book_analysis_service` retain their old private
helper names as direct imports pointing to the shared implementation.
This preserves existing call sites and any code importing the helpers.

No search algorithms, HTTP calls, page parsing rules, download engine logic,
Qt widgets, player behavior, timeouts, or public book models were changed.
Unit regressions cover completion, cancellation, shutdown and alias identity.

## Future audit priorities

The biggest remaining components are the Qt Help Center, the Poleknig
parser, and the HTTP download network mixin. Their size alone does not
justify a split. Extract logic only after identifying a clear responsibility
boundary and adding behavior-based regression tests.
