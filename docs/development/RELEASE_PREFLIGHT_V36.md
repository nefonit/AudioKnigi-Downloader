# V36 — Production source and Windows release-candidate preflight

## Audit findings fixed

1. **Sensitive files in source ZIPs.** V32/V33 added new local state
   artifacts that the source packager did not yet exclude: `*.lastgood.json`,
   `*.corrupt-<digest>.json`, segment files and checksum manifests. The
   default local Qt build environment `.venv-qt/` was not excluded either.
   Source archives now omit those files in both developer and production
   profiles, anywhere in the tree. They also omit runtime cookies, playback
   positions, session state, crash reports, environment secrets and symlinks.
   Executable code, locale catalogs, legal notices and build entrypoints
   remain in the production source package.
2. **Metadata dependency parity.** `pyproject.toml` declared the same
   runtime dependencies as `requirements.txt` except `beautifulsoup4`.
   The wheel/editable install now declares this source parser explicitly.
   Release pinning remains in `requirements-release.txt`.
3. **Incomplete Windows artifact.** The build script generated
   `THIRD_PARTY_NOTICES.md` and `RELEASE_LICENSING.md` alongside the
   EXE, but the GitHub release workflow uploaded neither. The workflow now
   includes both and refuses an incomplete artifact.
4. **No post-build candidate verification.** The release workflow now runs
   `tools/release_candidate_audit.py` to verify EXE SHA-256 and size
   against the build manifest, version-tag consistency, automated frozen
   self-test statuses and presence of legal notices before uploading an
   artifact clearly named `-candidate`.

## Release gates still open

This is **not** approval to publish a public stable installer/EXE. The
repository does not currently provide a declared top-level application
license. The bundled FFmpeg/Qt obligations must be checked for the exact
Windows binaries. Manual NVDA and JAWS acceptance on the hashed EXE is
still required. No real Windows install/upgrade or forced-process-kill
experiment was conducted in V36.

The built artifact's existing manifest intentionally retains
`manual_screen_reader_acceptance: required` and
`licensing_review: required`. The preflight validates and preserves
these statuses; it does not promote the candidate to a certified release.

## Regression coverage

`tests/unit/test_release_preflight_v36.py` builds both archive profiles
from a synthetic project with fake private state, checks symlink handling,
tests failed/tampered release manifests and hash mismatches, asserts legal
files and tagged-version consistency, and verifies that all runtime
requirements are represented in `pyproject.toml`.
