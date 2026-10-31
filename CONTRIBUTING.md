# Contributing to AudioKnigi Downloader

Start with `docs/INDEX.md` and the canonical `docs/architecture/PROJECT_STRUCTURE.md`. `docs/architecture/REPOSITORY_GUIDE_V19.md` is a historical snapshot; `docs/architecture/ROOT_MODULES_V22.md` maps all current backwards-compatible root aliases. Runtime modules belong in `audioknigi/`; avoid creating top-level `README_*.md` and new historical snapshot folders. Keep unit and integration fixtures deterministic and free of private user data.

Run `python -m pytest -q tests` for normal validation. Architecture tests check the current documentation links, directory catalog, provider/search layering, and stable compatibility paths. Prefer imports from the canonical implementation packages in new code; keep existing public aliases for older clients and PyInstaller. Windows Qt acceptance and screen reader checks are required before treating a Windows executable as release-ready. `build_qt_exe.bat` relies on pinned Windows Python 3.14.7, PyInstaller, FFmpeg and Microsoft Edge.

Never add saved cookies, tokens, personal logs, completed MP3 audio, temporary `.part` files, `.venv` or `dist/` to source releases. There is no declared top-level application license yet; a licensing decision is needed before public distribution.
