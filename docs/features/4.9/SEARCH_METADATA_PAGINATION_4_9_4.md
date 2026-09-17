# Search metadata and pagination — 4.9.4

## audioknigi.com.ua

Search-card labels such as:

`Филатов Валерий – Лабиринт искажений`

are split for the result table into:

- Название: `Лабиринт искажений`
- Автор: `Филатов Валерий`

The original combined label is still used internally for relevance scoring, so searches by author continue to work.

## knigavuhe.org

The current search layout is parsed by its semantic CSS blocks:

- `.bookitem_name` → title
- `.icon_author` → author
- `.icon_reader` → reader
- `.bookitem_cover` is used only as a URL/cover fallback, never as the title source, because its visible text can be a genre.

This removes the previous genre/title ambiguity without needing to open every result page.

### Pagination

Knigavuhe currently exposes 10 books per search page and links additional pages with `?page=N` / `data-page=N`.

AudioKnigi:

1. loads page 1;
2. detects the last pagination page;
3. follows pages 2..N concurrently;
4. merges them back in page order;
5. canonicalizes and deduplicates book URLs;
6. filters matches that occur only in the reader field;
7. collapses separate recording URLs with the same title+author into one logical result.

The application keeps its existing 100-result ceiling, so at the current 10-books-per-page layout it follows up to 10 Knigavuhe pages. Alternative recordings remain accessible through the **Озвучка** selector after opening a book.

## Verification

Live checks on 2026-08-30:

- Knigavuhe query `филатов`: pagination detected through page 10.
- All 10 pages were traversed in the integration check.
- Reader-only result `Мастер и Маргарита` was excluded.
- Multiple `Про Федота-стрельца...` recording URLs were collapsed to one logical result.
- audioknigi.com.ua query `филатов`: title and author were separated correctly, e.g. `Лабиринт искажений` / `Филатов Валерий`.
