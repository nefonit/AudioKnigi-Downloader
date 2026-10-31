# V17 — relevance filtering for combined audiobook search

Based on V16. All 8 providers and existing search/download/analyze logic are retained.

## Why the fix
Public site searches may include sidebar recommendations, anthology full-text hits and related books. The previous search simply appended every provider result, so entering `Sherlock Holmes` could show `Арсен Люпен`, unrelated Uknig titles and Sherlock recordings in one source-ordered list.

## New behavior
- The main search list now shows locally **verified** matches against the **title, author, narrator**, sorted by relevance. Matching considers conservative Cyrillic–Latin spelling differences (e.g. `Sherlock Holmes` and `Шерлок Холмс`).
- Broad site suggestions with no verified metadata match are **retained**, not silently deleted. In **Advanced → Search → Filters**, enable **Show possible matches / Показывать возможные совпадения** to append them below verified matches. This option defaults to OFF.
- A generic-titled anthology containing a Sherlock story, e.g. `Театр у микрофона 18`, is treated as *possible* until metadata supplies matching title/author/narrator. Its content is not fetched for relevance scoring. The unrelated `Арсен Люпен` is likewise only available through that opt-in list.
- A direct Akniga collection URL continues to show all collection entries without relevance filtering.
- Manual sorting by title/author/narrator overrides the default relevance order until another search/toggle.

## Verification
Unit tests cover mixed scripts, unrelated Akniga and Uknig titles, two-level results, author search, cancellation, and collections. Tests were also run for source search, downloads, network, settings, localization and privacy.

## Limitations
- Scoring uses **visible metadata only**, not a full-text index or remote description for each result. This is deliberate to avoid delays/extra requests and wrong book associations.
- Search relevance may omit a valid match inside an anthology from the default list. Enable *Show possible matches* in Advanced search to inspect the complete raw site suggestions.
- Qt/PySide6 screen-reader behavior and live Windows search were not validated in the Linux test environment.
