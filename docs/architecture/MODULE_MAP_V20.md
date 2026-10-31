# V20 — module map

This is a structural refactor, not a feature release. Existing entry points stay stable.

| Responsibility | Implementation | Legacy alias |
|---|---|---|
| Akniga parser | `audioknigi/parsers/akniga.py` | `audioknigi.akniga` |
| Knigavuhe parser | `audioknigi/parsers/knigavuhe.py` | `audioknigi.knigavuhe` |
| Poleknig parser | `audioknigi/parsers/poleknig.py` | `audioknigi.poleknig` |
| Source URLs | `audioknigi/providers/source_urls.py` | `audioknigi.sources` |
| Data models | `audioknigi/domain/models.py` | `audioknigi.models` |
| Core sessions | `audioknigi/engine/core.py` | `audioknigi.core` |
| DNS / proxy | `audioknigi/network/dns.py` | `audioknigi.network_dns` |
| Download components | `audioknigi/download/` | Existing package |
| Download orchestration | `audioknigi/download_engine.py` | Unchanged for audit and ABI compatibility |
| Source registry/search | `audioknigi/providers/` | Existing package |
| UI and accessibility | `audioknigi/qt/` | Existing package |
| Use cases/persistence | `audioknigi/services/` | Existing package |

## Rules

1. Keep old and new imports pointing to the same module object; never duplicate module state.
2. File locations in the headless runtime must continue to use the project root.
3. Do not eagerly import registry in `providers/__init__.py`; it creates an import cycle with source URLs.
4. Update source-inspection tests to inspect implementation files. Archived assertions are preserved; only their temporary source paths are remapped.
5. Static compatibility imports enable PyInstaller to include moved code when freezing Windows builds.
6. Further splits of `providers/extra_sources.py` and `download_engine.py` require separate migration tests.
