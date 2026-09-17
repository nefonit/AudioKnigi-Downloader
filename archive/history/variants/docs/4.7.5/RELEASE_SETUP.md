# Release setup

No additional secret is required for the standard GitHub release workflow. It uses GitHub's built-in `GITHUB_TOKEN` and `contents: write` for tag releases.

## First repository setup

1. Push the project to a GitHub repository.
2. Open **Actions** and confirm the CI workflow passes.
3. Create a release tag matching the package version:

```powershell
git tag v4.7.5
git push origin v4.7.5
```

4. The release workflow runs smoke tests, builds the Windows executable with PyInstaller and publishes the release artifact.

The application version is stored in `audioknigi/version.py`; `pyproject.toml` obtains the same value dynamically.
