"""Composable Qt main-window behavior mixins."""

from .search import SearchUiMixin
from .queue import QueueUiMixin
from .history import HistoryUiMixin
from .clipboard import ClipboardUiMixin
from .analysis_download import AnalysisDownloadUiMixin
from .settings import SettingsUiMixin
from .accessibility_ui import AccessibilityUiMixin
from .lifecycle import LifecycleUiMixin

__all__ = ["SearchUiMixin", "QueueUiMixin", "HistoryUiMixin", "ClipboardUiMixin",
           "AnalysisDownloadUiMixin", "SettingsUiMixin", "AccessibilityUiMixin", "LifecycleUiMixin"]
