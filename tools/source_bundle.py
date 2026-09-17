from __future__ import annotations

"""Source aggregation helpers for architecture/static audits after modularization."""

from pathlib import Path


def source_paths(root: Path, rel: str) -> tuple[Path, ...]:
    root = Path(root)
    if rel == "audioknigi/qt/main_window.py":
        paths = [root / rel, root / "audioknigi/qt/main_window_pages.py", root / "audioknigi/qt/player_mixin.py"]
        paths.extend(sorted((root / "audioknigi/qt/mixins").glob("*.py")))
        return tuple(p for p in paths if p.is_file())
    if rel == "audioknigi/downloader.py":
        paths = [root / rel]
        paths.extend(sorted((root / "audioknigi/download").glob("*.py")))
        return tuple(p for p in paths if p.is_file())
    if rel == "audioknigi/i18n.py":
        paths = [root / rel]
        paths.extend(sorted((root / "audioknigi/locales").glob("*.json")))
        return tuple(p for p in paths if p.is_file())
    return (root / rel,)


def read_source_bundle(root: Path, rel: str) -> str:
    parts: list[str] = []
    for path in source_paths(root, rel):
        try:
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(parts)
