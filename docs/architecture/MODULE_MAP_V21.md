# V21: providers and download entrypoints

> **Historical V21 snapshot.** V22 subsequently moved `download_engine.py` to `download/engine.py` behind a compatibility alias. For current owners, consult [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) and [ROOT_MODULES_V22.md](ROOT_MODULES_V22.md).

All the auxiliary source parsers were extracted from the original 715-line `providers/extra_sources.py` into `providers/sources_ext/`.

| New module | Responsibility |
|---|---|
| `sources_ext/izib.py` | Izib player and search cards |
| `sources_ext/akniga_catalog.py` | Akniga catalogue search and collections |
| `sources_ext/yakniga.py` | Yakniga read-only GraphQL and HTML description |
| `sources_ext/uknig.py` | Uknig playlist and book description |
| `sources_ext/librivox.py` | LibriVox API and Archive.org catalogue |
| `providers/extra_sources.py` | Shared HTTP and compatibility exports |
| `download/contracts.py` | Callback/result/preflight contracts |
| `download/service.py` | Public headless download orchestration |
| `download_engine.py` | Compatible internal execution engine (retained) |

## Compatibility rules

- All legacy `extra_sources` functions and helpers remain importable.
- The per-source modules call shared HTTP and cancellation helpers through the old facade, including on test monkeypatches.
- The `DownloadService` methods resolve `_DownloadEngine` lazily to honor patched engines.
- The runtime version is unchanged; this refactoring does not add providers or network calls.
- The heavyweight `_DownloadEngine` and whole-book workflow remain in `download_engine.py` for now; moving them requires independent source-shape, Windows and archive compatibility verification.
