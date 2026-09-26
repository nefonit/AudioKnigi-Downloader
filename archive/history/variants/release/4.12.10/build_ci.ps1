param(
    [string]$PythonExe = "",
    [switch]$SkipBrowserInstall
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$RequiredPythonVersion = "3.14.7"
$RequiredArchitecture = 64

function Resolve-BuildPython {
    param([string]$RequestedPython)

    if (-not [string]::IsNullOrWhiteSpace($RequestedPython)) {
        return (Resolve-Path -LiteralPath $RequestedPython).Path
    }

    $localPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $localPython) {
        return (Resolve-Path -LiteralPath $localPython).Path
    }

    # This fallback is used by CI after actions/setup-python. The version is
    # still checked below and the build aborts unless it is exactly 3.14.7 x64.
    return (Get-Command python -ErrorAction Stop).Source
}

$PythonExe = Resolve-BuildPython -RequestedPython $PythonExe
Write-Host "Python executable: $PythonExe"

$pythonFacts = & $PythonExe -c "import sys,struct; print('.'.join(map(str,sys.version_info[:3]))+'|'+str(struct.calcsize('P')*8))"
if ($LASTEXITCODE -ne 0) {
    throw "Python failed to start."
}

$parts = ($pythonFacts | Select-Object -Last 1).Trim().Split('|')
if ($parts.Count -ne 2) {
    throw "Could not determine the Python version/architecture used for the build."
}

$actualVersion = $parts[0]
$actualArchitecture = [int]$parts[1]
Write-Host "Python version: $actualVersion"
Write-Host "Python architecture: $actualArchitecture-bit"

if ($actualVersion -ne $RequiredPythonVersion) {
    throw "Wrong build Python: $actualVersion. AudioKnigi Downloader EXE builds require exactly Python $RequiredPythonVersion. Run build_exe.bat/build_exe_fixed.bat to recreate .venv."
}
if ($actualArchitecture -ne $RequiredArchitecture) {
    throw "Wrong Python architecture: $actualArchitecture-bit. The Windows EXE build requires Python $RequiredPythonVersion x64."
}

# Make sure PyInstaller sees the same installed distribution metadata.
& $PythonExe -c "import importlib.metadata as m; print('PyInstaller:', m.version('pyinstaller')); print('prismatoid:', m.version('prismatoid')); import prism; print('prism: OK')"
if ($LASTEXITCODE -ne 0) {
    throw "Required Python packages are missing from Python $RequiredPythonVersion."
}

$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
Write-Host "FFmpeg: $ffmpeg"
Write-Host "FFprobe: $ffprobe"

# Keep Playwright's browser inside the selected environment. With the local
# .venv this is writable and PyInstaller can collect the browser files.
$env:PLAYWRIGHT_BROWSERS_PATH = "0"
if (-not $SkipBrowserInstall) {
    & $PythonExe -m playwright install chromium
    if ($LASTEXITCODE -ne 0) {
        throw "Playwright Chromium installation failed under Python $RequiredPythonVersion."
    }
}

$arguments = @(
  "-m", "PyInstaller",
  "--noconfirm",
  "--clean",
  "--onefile",
  "--windowed",
  "--name", "AudioKnigiDownloader",
  "--collect-all", "playwright",
  "--collect-all", "PIL",
  "--collect-all", "mutagen",
  "--collect-all", "pygame",
  "--collect-all", "tkinterdnd2",
  "--collect-all", "ttkbootstrap",
  "--collect-all", "pystray",
  "--collect-all", "prism",
  "--copy-metadata", "prismatoid",
  "--additional-hooks-dir=.",
  "--icon", "assets\app_icon.ico",
  "--add-data", "assets;assets",
  "--add-binary", "$ffmpeg;.",
  "--add-binary", "$ffprobe;.",
  "audioknigi_gui.py"
)

Write-Host "Building AudioKnigiDownloader.exe with Python $RequiredPythonVersion x64..."
& $PythonExe @arguments
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE."
}

$exe = Join-Path $PSScriptRoot "dist\AudioKnigiDownloader.exe"
if (-not (Test-Path $exe)) {
    throw "PyInstaller did not create dist\AudioKnigiDownloader.exe"
}

Write-Host "Smoke test: $exe --version"
& $exe --version
if ($LASTEXITCODE -ne 0) {
    throw "The built EXE failed the --version smoke test."
}

Write-Host "Build completed successfully with Python $RequiredPythonVersion x64."
