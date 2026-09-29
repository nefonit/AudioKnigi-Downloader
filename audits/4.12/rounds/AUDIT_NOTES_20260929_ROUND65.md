# Round 65 — PoleKnig search relevance hardening

Applied a focused search-quality fix based on live UI behavior:

- introduced explicit PoleKnig title relevance ranking;
- exact title matches rank before partial title matches;
- multi-word title searches no longer keep rows that only share one common query word;
- when credible title matches exist, unrelated author-name coincidences are suppressed;
- author searches remain intact when multiple rows or an exact author identity establish author intent;
- author catalogue expansion is skipped only for clear title intent;
- preserved the established compatibility case where a stable two-word title phrase is accompanied by extra catalogue/publisher terms, e.g. `гарри поттер аудиокнига росмэн`;
- added regressions for `Закон и порядок`, `Айвенго`, `Вальтер Скотт`, `Толстой`, exact-title ordering and legacy extra-term search.
