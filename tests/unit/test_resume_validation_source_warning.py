"""Ensure HTTP resume helpers do not emit invalid-escape compiler warnings."""
from __future__ import annotations

from pathlib import Path
import warnings


def test_resume_validation_module_compiles_without_escape_warnings():
    source_file = (
        Path(__file__).resolve().parents[2]
        / "audioknigi" / "download" / "resume_validation.py"
    )
    source = source_file.read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        warnings.simplefilter("error", SyntaxWarning)
        compile(source, str(source_file), "exec")
