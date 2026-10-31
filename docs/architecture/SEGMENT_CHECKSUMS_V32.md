# V32 — Persistent checksums for downloaded Range segments

The segmented downloader already protects against an unsupported Range
response and verifies the total assembled byte count. However a previously
saved segment can change *without changing size*. A size-only check cannot
detect that corruption.

**V32 adds SHA-256 checkpoints** in the engine-owned sidecar
`<target>.part.segments.sha256.json`. The sidecar contains a source/range
signature and per-segment byte length and digest, written atomically with a
lock between workers. A segment is reused on restart only if its current
length and SHA-256 match the checkpoint **and** the source/range signature.
Otherwise it is removed and downloaded again. Legacy files without a valid
checksum are safely redownloaded once; their bytes cannot be trusted.

Workers checkpoint both complete segments and partial bytes left by a
controlled transport error, so a subsequent run can resume from verified
partial offsets. A sudden process termination may leave uncheckpointed
bytes; those are redownloaded rather than silently trusted.

Before atomic final rename, assembly streams each source segment into
the staging file while recomputing its SHA-256. A changed file or size
mismatch raises an error and deletes only the incomplete assembly target;
the existing final audio file is not replaced. A future attempt will
recognize and redownload the now-mismatching segment.

The checksum ledger is cleared alongside the original segment metadata
after successful assembly, RangeUnsupported cleanup, or explicit source
cleanup. Source cleanup recognizes only engine-owned artifact names.
The V29/V30/V31 HTTP 206/416 validation, Retry-After, cancellation and
progress rules remain unchanged.

**Security limitation:** these checksums detect local modification since
the stored checkpoint; they do not authenticate a remote CDN or prove its
contents are correct. No remote checksum is available.

## Tests

`tests/unit/test_segment_checksums_v32.py` covers matched/missing/corrupted
checkpoints, altered same-size files, signature changes, legacy segments,
partial segment resume, concurrent writes, cleanup and changes detected
during assembly. The active integration suite and archived regressions
continue to run.
