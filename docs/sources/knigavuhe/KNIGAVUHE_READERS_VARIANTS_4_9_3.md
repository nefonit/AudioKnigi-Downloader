# Knigavuhe search/readers/variants — 4.9.3

## Search behavior

Knigavuhe itself searches books, authors and performers. AudioKnigi Downloader now hydrates each Knigavuhe hit from the book page and separates:

- title;
- author;
- narrator/reader.

A result that matches the user's query only through the narrator is omitted. Matches in title or author remain. The Search table now contains separate «Автор» and «Чтец» columns.

## Alternative narrations

The Knigavuhe book-page block «Другие озвучки» is parsed into narration variants. When more than one recording exists, the Book tab shows a keyboard/screen-reader accessible readonly combobox «Озвучка». Selecting another item switches the URL and re-runs analysis for that concrete recording.

If the currently opened recording is rights-restricted, AudioKnigi Downloader does not attempt to bypass the restriction. If Knigavuhe exposes alternative recordings on that page, a metadata-only book view is shown and the user can choose another recording from «Озвучка».

## Validation

- compileall: passed
- pytest under Xvfb: 181 passed
- ci-selftest: passed for 4.9.3
