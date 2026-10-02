# Round 71 — Round 70 audit follow-up

Applied confirmed findings from the 2026-09-30 follow-up review:

- PlayerJS playlist parsing now ignores zero/non-positive `duration` placeholders and continues checking `length` / `time` before falling back to explicit `end - start`;
- AudioKnigi hydration defensively keeps `ThreadPoolExecutor(max_workers)` at least 1 if the hydration limit is configured/monkeypatched to zero;
- clipboard auto-prompt duplicate suppression compares canonical supported URLs, so a trailing slash/canonicalization difference cannot re-prompt for the same book;
- the primary download action explicitly rejects an analyzed book with zero tracks before selecting the all-tracks path;
- the missing dynamic `Smart Format: источник уже MP3 ...` message now has German, English and Ukrainian runtime-regex translations.

Reviewed and intentionally unchanged:

- a middle chapter of one shared physical source with no usable duration and no next `start` boundary still raises `SharedSourceTimelineError`; silently reading that chapter to EOF would duplicate the remainder of the audiobook into the current chapter;
- Windows support-bundle path matching remains deliberately privacy-first: file-like paths with spaces must be fully redacted even when this can remove adjacent diagnostic words;
- the `_download_single` HTTP-416 restart remains bounded to one practical restart and its outer transfer reset is cleanup telemetry, not a recursion leak;
- AudioKnigi detail hydration remains bounded and cancellable inside provider search; moving it into the provider enrichment phase would be an architectural/progress-model change rather than a correctness fix;
- queue mode `parts` is already a supported legacy alias normalized to `selected` by `_normalize_queue_download_mode`, with an existing regression test;
- CSV `None` values are validly serialized as empty cells by `csv.DictWriter`;
- PoleKnig `last_page` cannot be read unbound because every exception in its initialization block returns immediately;
- thread-local HTTP sessions intentionally refresh lazily by profile generation so active streaming downloads are not torn down;
- `safe_int(bool)`, packaged locale path placement, provider/service coupling, `dataChanged(..., [])`, and duplicated runtime localization rows remain established contracts or maintenance concerns;
- WebP cover lookup, full-MP3 result indices, duplicate-preflight `stat()` races, tiny progress painting, Advanced Search/Book field isolation, settings bulk replacement, history-clear safety and scale-aware cover icons were already fixed in Round 70.
