# Repository guide — V19

> **Historical V19 reference.** For the current architecture and import paths, use [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) and [ROOT_MODULES_V22.md](ROOT_MODULES_V22.md). The source ZIP profiles below remain supported, but their V19 example filenames are not version requirements.

## Start here

1. **Application**: `audioknigi_qt.py` is the compatible Qt entrypoint; `run.bat` and `run_qt.bat` launch on Windows. Do not move these.
2. **Runtime**: `audioknigi/` is the only application package. Providers are under `providers/`, downloads under `download/`, business services under `services/`, Qt views under `qt/`, localization under `locales/`. Do not add runtime code to the root.
3. **Resources**: `assets/` contains real runtime icons and sound assets; keep them.
4. **Tests**: `tests/unit`, `tests/integration`, `tests/architecture`, `tests/fixtures`; developer distribution only.
5. **Build**: root Windows entrypoints (`build_qt_exe.bat`, `build_qt_ci.ps1`), requirements files, `.github/workflows` and `tools/` in developer source. The compact production source includes only build-critical `tools/` files.
6. **Documentation**: `docs/user`, `docs/development`, `docs/architecture`; dated feature notes were moved into `docs/releases/`. `README.md`, `CHANGELOG.md`, and `THIRD_PARTY_NOTICES.md` remain at root.
7. **Historical evidence**: `archive/` and `audits/` are not runtime dependencies. They remain in the developer source for historical checks. Neither directory is shipped in the production-source distribution.

## Package profiles

| Content | Developers | Production source |
|---|---|---|
| Runtime package, entrypoints, assets, requirements | yes | yes |
| Windows build scripts, build-critical tools, third-party notices | yes | yes |
| Active tests, source packager, CI workflows | yes | no |
| Architecture and historical documentation | yes | no |
| `archive/` historical source variants + tests | yes | no |
| `audits/` incremental reports | yes | no |
| Local settings, logs, caches, virtual environments, build artifacts | no | no |

The **production-source** ZIP is source code, not a signed EXE. Install dependencies (`requirements.txt`) before running Python, and follow the Windows build instructions in `README.md` to produce an EXE. Builds require the pinned Windows Python version and FFmpeg/FFprobe. No installed dependencies or licensed binaries are bundled here. Review application-license and third-party-notice obligations before distributing.

## Packaging

```powershell
python tools/package_source_release.py --root . --profile developer --output AudioKnigi_V19_Developers.zip
python tools/package_source_release.py --root . --profile production --output AudioKnigi_V19_Production_Source.zip
```

Both profiles exclude runtime user state and generated data; the production profile additionally excludes tests, archives, audits, CI and development-only tools. `tools/package_source_release.py` itself stays in the developer package.

## Search number column

Both Qt search tables reserve enough width for five-digit row numbers. The first column uses a fixed, font-aware width rather than sampling only the first 20/60 rows, preventing `100` and subsequent numbers from being elided as `...`. Sorting and screen-reader roles remain unchanged.
