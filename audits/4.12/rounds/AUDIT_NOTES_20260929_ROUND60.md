# Round 60 — residual external-audit hardening — 2026-09-29

Round 60 follows the Round 59 review of the uploaded external audit and closes the remaining concrete failure modes that were still present in current main.

## Confirmed and fixed

- UI scale migration now runs before the final 80–200 range clamp, so any migrated value is validated by the same current settings contract.
- FFprobe duration-probe cancellation now has single-owner process I/O: coordinator threads may request one termination, while only the worker that created the Popen owns communicate() and pipe cleanup. Repeated/concurrent stop requests cannot issue multiple kills.
- Queue persistence preserves optional template fields exactly. Missing/null remains None, and an explicitly stored empty string remains an empty string instead of being silently rewritten to a default template.
- Unfinished-download manifests now distinguish an omitted template field from an explicitly stored value. Omitted fields inherit the user's current global settings during recovery instead of overwriting them with hard-coded defaults.
- AudioKnigi search/detail requests use one bounded (4 s connect, 8 s read) timeout contract and the compatibility metadata wrapper now propagates cancel_event.

## Cancellation boundary

Python requests does not provide a safe mechanism for forcibly killing a thread that is blocked inside socket I/O. Round 60 therefore keeps cooperative cancel_event propagation and bounds the remaining AudioKnigi socket wait instead of attempting unsafe thread termination. The existing multi-source executor still returns promptly when providers cooperate with cancellation; a regression covers that behavior.

## Regression coverage

tests/integration/test_persistence_cancellation_hardening_20260929.py covers post-migration scale clamping, exact queue template round-trips, missing-vs-explicit resume template semantics, concurrent ffprobe stop ownership, bounded AudioKnigi search timeouts, prompt cooperative multi-source cancellation, and the Qt recovery merge contract.
