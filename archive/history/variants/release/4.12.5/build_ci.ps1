param(
    [string]$PythonExe = "",
    [switch]$SkipBrowserInstall
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $localPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $localPython) {
        $PythonExe = $localPython
    } else {
        $PythonExe = (Get-Command python -ErrorAction Stop).Source
    }
}

$PythonExe = (Resolve-Path -LiteralPath $PythonExe).Path
Write-Host "Python: $PythonExe"
& $PythonExe --version
if ($LASTEXITCODE -ne 0) { throw "Python failed to start." }

# Make sure PyInstaller sees the same installed distribution metadata.
& $PythonExe -c "import importlib.metadata as m; print('PyInstaller:', m.version('pyinstaller')); print('prismatoid:', m.version('prismatoid')); import prism; print('prism: OK')"
if ($LASTEXITCODE -ne 0) { throw "Required Python packages are missing from the build interpreter." }

$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
Write-Host "FFmpeg: $ffmpeg"
Write-Host "FFprobe: $ffprobe"

# PLAYWRIGHT_BROWSERS_PATH=0 makes the browser live inside the local venv's
# Playwright package. Because the venv is in the project directory, this is
# writable and PyInstaller can collect the bundled browser files.
$env:PLAYWRIGHT_BROWSERS_PATH = "0"
if (-not $SkipBrowserInstall) {
    & $PythonExe -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw "Playwright Chromium installation failed." }
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

& $PythonExe @arguments
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed with exit code $LASTEXITCODE." }

$exe = Join-Path $PSScriptRoot "dist\AudioKnigiDownloader.exe"
if (-not (Test-Path $exe)) {
  throw "PyInstaller did not create dist\AudioKnigiDownloader.exe"
}

Write-Host "Smoke test: $exe --version"
& $exe --version
if ($LASTEXITCODE -ne 0) { throw "The built EXE failed the --version smoke test." }
