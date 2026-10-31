"""V21 source ownership and backwards-compatible facade tests."""
from pathlib import Path
from audioknigi.providers import extra_sources
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, DownloadService

ROOT = Path(__file__).resolve().parents[2]

def test_provider_modules_are_independent():
    path = ROOT / "audioknigi/providers/sources_ext"
    for source in ("izib", "yakniga", "uknig", "librivox", "akniga_catalog"):
        assert (path / (source + ".py")).is_file()

def test_extra_sources_old_entrypoints_are_preserved():
    for name in ("fetch_izibuk", "search_izibuk", "fetch_yakniga", "search_yakniga",
                 "fetch_uknig", "search_uknig", "fetch_librivox", "search_librivox",
                 "fetch_akniga_collection", "search_akniga", "parse_akniga_collection"):
        assert callable(getattr(extra_sources, name))

def test_download_service_uses_extracted_contracts():
    from audioknigi.download.contracts import DownloadCallbacks as CB, DownloadResult as DR, DuplicatePreflight as DP
    from audioknigi.download.service import DownloadService as DS
    assert (CB, DR, DP, DS) == (DownloadCallbacks, DownloadResult, DuplicatePreflight, DownloadService)
