# V18 — corrected Izib search titles

Based on V17. No network, download, HLS, search ranking, or Qt interface changes.

## Fixed

Izib highlights search terms with nested HTML tags. Using `get_text(" ", strip=True)`
inserted spaces **inside Russian inflected words** and before punctuation.

Examples (before → after):

- `Архив Шерлок а Холмс а` → `Архив Шерлока Холмса`
- `Воспоминания о Шерлок е Холмс е` → `Воспоминания о Шерлоке Холмсе`
- `Шерлок Холмс . Дыхание бога` → `Шерлок Холмс. Дыхание бога`

The Izib card and book-detail title/author/narrator extraction now preserves
literal text-node spacing, inserts a separator for real `<br>` elements, and
normalizes spaces before punctuation. No Russian-specific string replacements;
the same method works for other authors and search queries.

## Verification

- New HTML regression tests for exact user-reported cases, `<br>` / `<wbr>`,
  metadata fields, plus the existing Izib search and book-detail parsers.
- Live Izib HTML and Windows screen reader behavior are **not** tested here;
  compare a fresh `Sherlock Holmes` or `шерлок холмс` search in V18.
- This does not deduplicate different recordings of the same book; separate
  audiobook URLs are intentional search results.
