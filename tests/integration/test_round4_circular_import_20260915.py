from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_book_analysis_service_can_be_imported_from_clean_interpreter():
    root = Path(__file__).resolve().parents[2]
    code = (
        "from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService; "
        "from audioknigi.services.queue_service import QueueStore, QueueTask; "
        "print(AnalysisOptions.__name__, BookAnalysisService.__name__, QueueStore.__name__, QueueTask.__name__)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "AnalysisOptions BookAnalysisService QueueStore QueueTask" in proc.stdout


def test_download_package_keeps_source_analysis_mixin_public_export():
    from audioknigi.download import SourceAnalysisMixin
    from audioknigi.download.source_analysis import SourceAnalysisMixin as DirectMixin

    assert SourceAnalysisMixin is DirectMixin
