# Knigavuhe search title fix — 4.9.2

## Reported symptom

Search requests to knigavuhe.org succeeded and book URLs were correct, but the UI title column could show a genre from the same search card, for example:

- `/book/leonid-filatov/` -> `Биографии`
- `/book/pro-fedota-strelca-udalogo-molodca/` -> `Для детей`
- audiobook drama pages -> `Аудиоспектакли`

## Root cause

The Knigavuhe search result card contains many nearby links (book, author, genre, reader, comments).  URL canonicalization fixed the comments-link issue, but card-local text remains ambiguous in the site's current markup.

## Fix

Search now treats the canonical `/book/<slug>/` URL as the identity of a result and hydrates the displayed title from that book's own HTML `<title>` before returning results to the UI.

- detail-page title requests run concurrently (max 6 workers);
- result ordering is preserved;
- a failure to resolve one title keeps the card-derived fallback instead of failing the whole search;
- no audio files are downloaded during title hydration.

## Verification

- dedicated regression reproducing the screenshot: passed;
- Knigavuhe tests: 10 passed;
- complete suite under Xvfb: 177 passed;
- `compileall`: passed;
- `audioknigi_gui.py --ci-selftest`: passed for 4.9.2.
