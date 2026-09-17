# Search Fix — 4.8.2

The AudioKnigi.com.ua header search form currently submits:

```text
GET /search?text=<query>
```

Version 4.8.2 mirrors that contract directly. The previous downloader used an older DLE-style `story=` endpoint, which could return a generic page containing unrelated audiobook links.

## Result rules

1. Only links whose path is `/audio-<id>...` on `audioknigi.com.ua` are considered.
2. Visible anchor text, link metadata and image alt text are all accepted as possible book labels.
3. Every word from the user's query must occur in the human-readable book label. This allows `Сандерсон`, `Брендон Сандерсон`, or a title fragment while rejecting unrelated sidebar recommendations.
4. Repeated cover/title links to the same URL are merged.
5. Site descriptive prefixes such as `Слушать онлайн аудиокниги ...` are removed before display.
6. The UI enforces the site's minimum search length of three characters.
