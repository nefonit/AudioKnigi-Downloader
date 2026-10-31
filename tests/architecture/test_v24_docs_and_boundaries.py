"""Current documentation and dependency-boundary contracts.

Historical migration notes and archived snapshots are intentionally excluded
from the active documentation-link check.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]

CURRENT_DOCUMENTS = (
    "README.md",
    "CONTRIBUTING.md",
    "docs/INDEX.md",
    "docs/PROJECT_STRUCTURE.md",
    "docs/architecture/PROJECT_STRUCTURE.md",
    "docs/architecture/MODULE_MAP_V20.md",
    "docs/architecture/MODULE_MAP_V21.md",
    "docs/architecture/ROOT_MODULES_V22.md",
    "docs/architecture/REPOSITORY_GUIDE_V19.md",
    "docs/development/LOCALIZATION.md",
    "docs/development/RELEASE_LICENSING.md",
    "docs/development/SETTINGS_SCHEMA.md",
    "docs/user/DIAGNOSTICS.md",
    "docs/testing/README.md",
    "docs/qa/README.md",
)

LOCAL_MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]+\]\(([^)\n]+)\)")
RUNTIME_LAYERS = (
    "domain", "engine", "parsers", "providers", "download", "services",
)


def _imports(path: Path):
    return ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))


def test_current_documentation_relative_links_exist():
    for relative in CURRENT_DOCUMENTS:
        document = ROOT / relative
        assert document.is_file(), relative
        for match in LOCAL_MARKDOWN_LINK.finditer(document.read_text(encoding="utf-8")):
            target = match.group(1).strip().split(maxsplit=1)[0].strip("<>")
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue  # External links, e-mail addresses, or local anchors.
            linked = (document.parent / unquote(parts.path)).resolve()
            assert linked.is_relative_to(ROOT), f"{relative}: link escapes repository: {target}"
            assert linked.exists(), f"{relative}: missing link target: {target}"


def test_current_docs_index_runtime_directories_exist():
    index = (ROOT / "docs/INDEX.md").read_text(encoding="utf-8")
    assert "## Runtime domains" in index
    domains = index.split("## Runtime domains", 1)[1].split("\n## ", 1)[0]
    listed = re.findall(r"(?m)^-\s+\x60([^\x60]+/)\x60", domains)
    assert listed, "No runtime documentation directories found in docs/INDEX.md"
    for directory in listed:
        path = (ROOT / "docs" / directory).resolve()
        assert path.is_relative_to(ROOT), directory
        assert path.is_dir(), f"Non-existent docs/INDEX.md runtime directory: {directory}"


def test_provider_modules_do_not_import_search_orchestration():
    """Provider discovery cannot depend on the service that consumes it."""
    provider_root = ROOT / "audioknigi/providers"
    for path in provider_root.rglob("*.py"):
        for node in _imports(path):
            if isinstance(node, ast.Import):
                for item in node.names:
                    assert not item.name.startswith("audioknigi.services.search_service"), path
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module not in {
                    "services.search_service", "audioknigi.services.search_service",
                }, path
                if module in {"services", "audioknigi.services"}:
                    assert all(item.name != "search_service" for item in node.names), path


def test_headless_core_layers_have_no_direct_qt_imports():
    """The dependency boundary belongs in the Qt package, not the core."""
    for layer in RUNTIME_LAYERS:
        for path in (ROOT / "audioknigi" / layer).rglob("*.py"):
            for node in _imports(path):
                if isinstance(node, ast.Import):
                    for item in node.names:
                        assert not (
                            item.name == "PySide6" or item.name.startswith("PySide6.")
                            or item.name == "audioknigi.qt"
                            or item.name.startswith("audioknigi.qt.")
                        ), f"Qt import from headless module: {path}: {item.name}"
                elif isinstance(node, ast.ImportFrom):
                    name = node.module or ""
                    assert not (
                        name == "PySide6" or name.startswith("PySide6.")
                        or name == "audioknigi.qt" or name.startswith("audioknigi.qt.")
                        or (node.level and name.split(".", 1)[0] == "qt")
                    ), f"Qt import from headless module: {path}: {name}"
