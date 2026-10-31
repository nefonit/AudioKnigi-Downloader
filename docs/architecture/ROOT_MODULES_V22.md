# V22 — audioknigi package-root ownership

The package root contains only the `__init__.py` public package bootstrap and compatibility aliases.

| Public alias | Actual implementation |
|---|---|
| `audioknigi.brand` | `audioknigi.identity.brand` |
| `audioknigi.metadata` | `audioknigi.identity.metadata` |
| `audioknigi.version` | `audioknigi.identity.version` |
| `audioknigi.cover_fetch` | `audioknigi.engine.cover_fetch` |
| `audioknigi.crash_report` | `audioknigi.diagnostics.crash_report` |
| `audioknigi.downloader` | `audioknigi.download.downloader` |
| `audioknigi.i18n` | `audioknigi.localization.i18n` |
| `audioknigi.integrations` | `audioknigi.connectors.audiobookshelf` |
| `audioknigi.logging_utils` | `audioknigi.diagnostics.logging_utils` |
| `audioknigi.qt_runtime_audit` | `audioknigi.qt.runtime_audit` |
| `audioknigi.templates` | `audioknigi.download.naming` |
| `audioknigi.download_engine` | `audioknigi.download.engine` |

The V20 aliases for site parsers, models, core, DNS and source URLs remain unchanged. Old and new imports must resolve to identical module objects. Python dynamic source inspection should use the actual source files.
