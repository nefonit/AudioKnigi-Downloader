# Round 79 — external audit follow-up

Applied confirmed findings from the 2026-10-05 review:

- primitive string/number selected indices no longer collide with methods such as `str.index`, and direct `_process_book_once` selection normalization accepts primitive and mapping-backed indices safely;
- expired-media inference reads mapping-backed track indices and source URLs without `AttributeError`;
- optional Audioknigi page metadata can no longer erase a title already recovered from PlayerJS/page title; playlist JSON objects with a list-valued `playlist` field are accepted, while other object shapes raise `SiteStructureChanged` instead of the misleading `Плейлист пуст.`;
- KnigaVuhe BookController pages fall back to stable page metadata for the author when the controller omits authors;
- resume manifests and transient full-source files use `unlink_with_retry` for Windows sharing/antivirus races;
- cover downloads reject declared `Content-Length` values above the 20 MiB cap before reading the body;
- embedded POSIX file redaction still masks real paths with spaces but no longer treats whitespace-led arithmetic/date fragments such as `10 / 2 / calc.py` as file paths;
- the three long search accessibility descriptions now have English, German and Ukrainian translations.

Reviewed and intentionally unchanged:

- `AppSettings.__contains__` intentionally reports physically stored canonical keys while deprecated aliases remain readable through `[]`/`.get()`; Round 76 tests protect this persistence contract;
- parameterized entries such as `Озвучка {index}` and `Найдено вариантов озвучки: {count}...` are called through `ui_text(..., **kwargs)` and are covered by regression tests; they are not dead runtime-exact entries;
- runtime regex rules are resolved before prefix fallbacks, so the reported prefix shadowing does not occur;
- `SearchResult.author_inferred` is a declared dataclass field; the reported constructor risk is not present;
- Round 78 already fixed zero-index playlist refresh/sidecars, unknown-duration sidecars, blank track-title collisions, exact `Другие озвучки` headings, German help `<kbd>` shortcuts, known-narrator fallback conflicts, and DPI-aware speed graph labels;
- the Easy-mode result-selection path writes the selected canonical URL into `easy_input`, so the download button remains enabled after analysis;
- source-health proxy isolation matches the global HTTP-session policy; the native media-key filter is already removed during lifecycle shutdown; event-sound percentage values are normalized before configuring the sound manager; and `_choose_output_dir` explicitly consumes Qt's `checked` argument;
- queue duplicate replacement, localized settings-page object IDs, filesystem fallback text `Без автора`, and unifying `parts`/`selected` download-mode names are broader UX/model migrations rather than correctness fixes;
- QueueTableWidget drop coordinates are left unchanged because QAbstractItemView drag/drop handling is viewport-oriented and no reproducible off-by-one failure is present in the current test environment.
