# PoleKnig integration — 4.11.0

AudioKnigi Downloader now supports `https://poleknig.com/` as a third source.

## Supported flow

- direct book links: `https://poleknig.com/books/<id>`
- search: `GET https://poleknig.com/?q=<query>`
- pagination: `p=<page>` with the application-wide 100-result ceiling
- search table metadata: title, author, reader, narration count, source, URL
- multiple separate recording pages of the same Title + Author are collapsed into one logical search row and exposed through the existing **Озвучка** selector
- PlayerJS public playlists are converted into the existing `Track` model, so MP3/M4B, queue, resume, tags, covers, templates and library handling continue through the common downloader pipeline

## PlayerJS parsing

The provider supports the common PlayerJS 19.x forms used for audio:

- `file: "https://.../track.mp3"`
- `file: "[Chapter 1]url1,[Chapter 2]url2"`
- `file` / `playlist` arrays of objects with `title`, `file`/`url`, and optional duration
- external `.json` / `.txt` public playlists
- direct public MP3/M4A/AAC/OGG/WAV references already present in the page source

If static HTML does not expose a public playlist, Playwright performs a best-effort fallback and inspects only browser-visible audio/PlayerJS resource URLs. It does not decode DRM or bypass access restrictions.

## Rights-holder removals

Pages containing the site's “Удалено правообладателем” marker are returned as restricted metadata-only books. AudioKnigi Downloader does not attempt to circumvent that state.

## Verification

- PoleKnig-specific tests: 6/6
- full regression suite: 238/238
- `compileall`: OK
- CI self-test: 4.11.0 OK

The public page/search structure was checked against the live site. The execution environment used for packaging could not make a raw HTTP request to PoleKnig's media scripts, so the first real Windows download should be tested against one currently available book; the parser includes both static PlayerJS and Playwright fallback paths for that reason.
