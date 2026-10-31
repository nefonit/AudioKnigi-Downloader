"""V20 modular packaging and legacy-import compatibility invariants."""
from importlib import import_module
from pathlib import Path

def test_modules_are_owned_by_focused_packages():
    root = Path(__file__).resolve().parents[2] / "audioknigi"
    for dest in ("parsers/akniga.py", "parsers/knigavuhe.py",
                 "parsers/poleknig.py", "engine/core.py", "domain/models.py",
                 "network/dns.py", "providers/source_urls.py"):
        assert (root / dest).is_file(), dest

def test_old_and_new_imports_refer_to_one_module():
    pairs = {"akniga": "parsers.akniga", "knigavuhe": "parsers.knigavuhe",
             "poleknig": "parsers.poleknig", "core": "engine.core",
             "network_dns": "network.dns", "models": "domain.models",
             "sources": "providers.source_urls"}
    for old, new in pairs.items():
        assert import_module(f"audioknigi.{old}") is import_module(f"audioknigi.{new}")

def test_runtime_paths_still_resolve_into_existing_tree():
    from audioknigi.core import APP_DIR
    assert APP_DIR.is_dir()

def test_provider_registry_is_lazy_and_still_available():
    from audioknigi.providers import registered_providers
    assert callable(registered_providers)
