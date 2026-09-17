# Search variants 4.9.5

Version 4.9.5 makes alternative narrations a first-class concept for both providers.

## Search table

The table now contains **Озвучек**. A value of `1` means one known recording; `2`, `3`, `4` etc. represent distinct recording pages.

## audioknigi.com.ua

The site publishes alternative narrations as separate `/audio-*` pages. Results with the same normalized **Title + Author** are collapsed into one logical book. Duplicate pages are kept as `NarrationVariant` objects. Their reader metadata is fetched concurrently only for duplicate groups. Opening the result registers the whole group so the normal **Озвучка** selector can switch between those pages.

## knigavuhe.org

The current new-design `Другие озвучки` block uses `/book/.../` links whose visible text is the reader name. The parser also supports the older layout where book title and reader were separate links. Parsing stops at comments/recommendations. Search rows are enriched from one detail page so the variant count includes alternatives that are not present as separate rows in search pagination.

When a reader appears on more than one distinct recording page, the selector uses labels such as `Илья Кривошеев — вариант 1` and `Илья Кривошеев — вариант 2`.

## Download isolation

With default folder naming, a multi-recording book is stored as `Book Title [Reader]`; repeated recordings by the same reader use `Reader - вариант N`. Custom folder templates remain unchanged and under user control.
