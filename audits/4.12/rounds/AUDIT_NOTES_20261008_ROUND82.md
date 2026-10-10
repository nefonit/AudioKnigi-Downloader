# Round 82 — post-consolidation audit follow-up

Applied low-risk findings from the 2026-10-08 review:

- made the stale-part HTTP 416 recovery contract explicit: `_download_single()` may discard a bad `.part` and restart from byte zero only once; a 416 on that retry is surfaced as the normal HTTP/network failure and cannot recurse again;
- corrected search-result count wording at the producer boundary for Russian singular/few/many forms and added matching runtime translations so English uses `1 book`, German uses `1 Buch`, and Ukrainian uses the corresponding singular/few forms;
- added the new regressions to the consolidated domain modules (`test_network.py` and `test_localization.py`) rather than creating a new round-named test module.

Reviewed and intentionally unchanged:

- Python compatibility: project metadata already requires Python >= 3.11, so `dataclass(slots=True)` and `ThreadPoolExecutor.shutdown(cancel_futures=True)` are within the supported runtime contract;
- `Book.tracks` is a typed runtime model contract (`Track` objects); Mapping tolerance in selected boundary helpers remains defensive compatibility rather than a promise that the full mutable download pipeline accepts arbitrary dicts;
- `AppSettings.__contains__` intentionally reflects physically stored canonical keys while legacy aliases remain readable through `[]`/`.get()`;
- Windows diagnostic path redaction remains privacy-first for ambiguous directory-like text;
- duplicate exact/legacy and regex/prefix localization entries are intentional compatibility fallbacks with deterministic resolver priority;
- `parts` versus `selected` download-mode naming is a broader model migration and is deferred;
- conservative multi-author parsing, backup rollback, CSV formula escaping, Windows-default DoH, strict `MappingDataclass`, template traversal protection, subprocess hiding, thread-local HTTP sessions, UI scaling, and event-sound volume normalization were reviewed as correct/intentional.
