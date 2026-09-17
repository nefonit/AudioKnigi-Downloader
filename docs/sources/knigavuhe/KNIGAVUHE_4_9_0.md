# Knigavuhe.org integration — 4.9.0

## Scope

- Added `knigavuhe.org` as a second supported source alongside `audioknigi.com.ua`.
- The Search tab queries both providers concurrently and labels every result with its source.
- Main URL input, queue, clipboard detection and Drag-and-Drop accept Knigavuhe book links.

## Parsing strategy

1. Preferred path: parse the JSON argument passed to `BookController.enter(...)`.
   This supplies title, authors, readers, cover, primary playlist and `merged_playlist`.
2. Fallback path: if BookController data is absent, scan page scripts for direct MP3 URLs, matching the simpler Python downloader supplied for this integration.
3. Pages explicitly marked by Knigavuhe as restricted at a rights-holder's request are rejected with a clear message; no restriction bypass is attempted.

## Download reliability

`Track.fallback_file` stores the corresponding URL from `merged_playlist`. If the primary audio source fails, the downloader removes the partial source file and retries the same chapter through the alternate URL. Existing resume, Range, tagging, M4B and library workflows remain unchanged.

## Compatibility

- Existing `Track` positional constructor order is preserved by adding `fallback_file` as the final optional field.
- Existing `SearchResult(title, url)` calls remain valid because `source` has a default value.
- Existing audioknigi.com.ua parser and Playwright fallback remain untouched for that provider.

## Verification

- `python -m compileall audioknigi tests`: passed.
- `python audioknigi_gui.py --ci-selftest`: passed (`4.9.0`).
- Full GUI/headless regression suite under Xvfb: 173 passed.
- Current Knigavuhe public search endpoint `/search/?q=...` and `/book/...` page structure were verified on 2026-08-30.
