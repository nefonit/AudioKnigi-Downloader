# Build-startup fix — round 4 (2026-09-15)

## Reported failure

The Windows `build_qt_exe.bat` source accessibility preflight failed before PyInstaller with a circular import:

`book_analysis_service -> download.common -> download.__init__ -> source_analysis -> book_analysis_service`

The failure surfaced as `ImportError: cannot import name 'AnalysisOptions' from partially initialized module 'audioknigi.services.book_analysis_service'`.

## Root cause

Importing the leaf module `audioknigi.download.common` necessarily initializes the `audioknigi.download` package first. Its `__init__.py` eagerly imported every facade mixin, including `SourceAnalysisMixin`. `source_analysis.py` imports `BookAnalysisService`, so importing `book_analysis_service.py` recursively entered itself before `AnalysisOptions` had been defined.

## Fix

`audioknigi.download.__init__` no longer eagerly imports `SourceAnalysisMixin`. That single facade export is resolved through module-level `__getattr__` when callers request it. The public API and `__all__` entry remain unchanged. Other download facade exports remain eager.

This keeps PyInstaller/static discoverability (the import is still present in source), avoids moving/duplicating subprocess helpers, and allows service modules to import `download.common` independently.

## Regression coverage

A new test launches a clean Python interpreter and imports `BookAnalysisService`, `AnalysisOptions`, `QueueStore`, and `QueueTask` in the same order that exposed the build failure. A second test verifies that `from audioknigi.download import SourceAnalysisMixin` still resolves to the direct implementation class.

## Verification

- Clean service/queue/facade/downloader imports: PASS.
- New Round 4 regressions: 2 passed.
- Full pytest suite: 230 passed, 0 failed.
- Exception audit: PASS (`reviewed_broad_exception_passes=113`).
- Historical regression audit: PASS (`passed=271`, `known_shape_incompatibilities=112`).
- Undefined-global audit: OK (77 modules).
- Unused-import audit: OK (32 implementation modules).
- Qt localization audit: OK for `ru`, `uk`, `de`, `en`.
- Full parity audit: PASS 61/61.
- Static Qt import-boundary audit: OK (73 project modules reachable, no legacy frontend path).

The actual Windows Qt accessibility/PyInstaller self-test cannot be executed in this Linux environment because PySide6 is not installed here. The exact circular import path that failed in the supplied Windows log was reproduced independently and now passes.
