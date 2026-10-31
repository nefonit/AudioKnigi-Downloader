# Akniga collections — experiment V7

This release adds a *catalogue-only* handler for URLs of the form
`https://akniga.org/collection/<slug>/`. A collection is not a single
book and must not be sent to the HLS player analyzer.

* Paste a collection URL in Easy mode, the advanced book URL field, or
  Search. The application loads the collection into the existing accessible
  search-results table. Select a single book to analyze its chapters.
* Queue insertion of a collection URL likewise opens book selection; it
  **does not enqueue all books**.
* The source search filter now includes Akniga as an individual source.
* Collection requests fetch only public book catalogue HTML. No media
  tokens, audio playlists, or downloads are requested at this stage.
* The parser supports Akniga's article card layout and a conservative main-
  content link fallback. It reports missing/changed markup rather than
  pretending the collection is empty.
* Live site response to the exact user-provided collection URL could not be
  verified in the build environment. Local fixtures are synthetic.

To test on Windows, keep Cloudflare One enabled for Akniga access, paste:
`https://akniga.org/collection/v-derevne-yavno-tvoritsya-kakaya-to-hren/`.
Select a result and inspect its chapters; do not expect a collection itself
as a single playable audiobook.
