"""PySide6/Qt Widgets interface for the production Qt-only runtime."""

# Historical compatibility marker consumed by frozen-build acceptance reports.
QT_MIGRATION_STAGE = "phase-39"
# Current runtime/release marker for post-migration builds.
QT_RUNTIME_STAGE = "qt-only-4.12.42"

__all__ = ["QT_RUNTIME_STAGE", "QT_MIGRATION_STAGE"]
