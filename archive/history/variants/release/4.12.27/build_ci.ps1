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
& $PythonExe -c "import importlib.metadata as m; from packaging.version import Version; v=Version(m.version('prismatoid')); assert v>=Version('0.18.1'); print('PyInstaller:', m.version('pyinstaller')); print('prismatoid:', v); from prism import BackendId, Context; assert BackendId.NVDA and BackendId.JAWS; print('prism NVDA/JAWS API: OK')"
if ($LASTEXITCODE -ne 0) {
    throw "Required Python packages are missing from Python $RequiredPythonVersion."
}

function Test-MediaToolExecutable {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Name
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    try {
        & $Path -hide_banner -version *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Test-IsChocolateyBinShim {
    param([Parameter(Mandatory=$true)][string]$Path)
    $chocoRoot = $env:ChocolateyInstall
    if ([string]::IsNullOrWhiteSpace($chocoRoot)) {
        $chocoRoot = "C:\ProgramData\chocolatey"
    }
    try {
        $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
        $chocoBin = [IO.Path]::GetFullPath((Join-Path $chocoRoot "bin")).TrimEnd('\') + '\'
        return $fullPath.StartsWith($chocoBin, [StringComparison]::OrdinalIgnoreCase)
    }
    catch {
        return $false
    }
}

function Resolve-RealMediaTool {
    param([Parameter(Mandatory=$true)][string]$Name)

    $candidatePaths = New-Object System.Collections.Generic.List[string]

    # A repository-local real binary is always acceptable.
    $localTool = Join-Path $PSScriptRoot ("tools\" + $Name + ".exe")
    if (Test-Path -LiteralPath $localTool -PathType Leaf) {
        $candidatePaths.Add($localTool)
    }

    # PATH candidates. Chocolatey's bin entry is a shim and must never be
    # copied into a PyInstaller one-file bundle.
    try {
        $cmd = Get-Command $Name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) {
            $candidatePaths.Add([string]$cmd.Source)
        }
    } catch {}

    try {
        $whereResults = & where.exe ($Name + ".exe") 2>$null
        foreach ($item in @($whereResults)) {
            if (-not [string]::IsNullOrWhiteSpace([string]$item)) {
                $candidatePaths.Add(([string]$item).Trim())
            }
        }
    } catch {}

    # Chocolatey keeps the actual FFmpeg binaries inside lib\ffmpeg*\tools.
    # Search there explicitly instead of packaging C:\ProgramData\chocolatey\bin\ffmpeg.exe.
    $chocoRoot = $env:ChocolateyInstall
    if ([string]::IsNullOrWhiteSpace($chocoRoot)) {
        $chocoRoot = "C:\ProgramData\chocolatey"
    }
    $chocoLib = Join-Path $chocoRoot "lib"
    if (Test-Path -LiteralPath $chocoLib -PathType Container) {
        try {
            $packageDirs = Get-ChildItem -LiteralPath $chocoLib -Directory -Filter "ffmpeg*" -ErrorAction SilentlyContinue
            foreach ($packageDir in @($packageDirs)) {
                $found = Get-ChildItem -LiteralPath $packageDir.FullName -File -Recurse -Filter ($Name + ".exe") -ErrorAction SilentlyContinue |
                    Sort-Object @{Expression={ if ($_.FullName -match "\\bin\\") { 0 } else { 1 } }}, LastWriteTime -Descending
                foreach ($file in @($found)) {
                    $candidatePaths.Add($file.FullName)
                }
            }
        } catch {}
    }

    $seen = @{}
    foreach ($candidate in $candidatePaths) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        try { $full = [IO.Path]::GetFullPath($candidate) } catch { continue }
        $key = $full.ToLowerInvariant()
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true

        if (Test-IsChocolateyBinShim -Path $full) {
            Write-Host "Skipping Chocolatey shim for $Name`: $full"
            continue
        }
        if (Test-MediaToolExecutable -Path $full -Name $Name) {
            return $full
        }
    }

    throw "Could not find a real $Name executable. A Chocolatey bin shim cannot be embedded into the portable EXE. Install FFmpeg or place real ffmpeg.exe/ffprobe.exe under .\tools."
}

$ffmpeg = Resolve-RealMediaTool -Name "ffmpeg"
$ffprobe = Resolve-RealMediaTool -Name "ffprobe"
Write-Host "Real FFmpeg for bundle: $ffmpeg"
Write-Host "Real FFprobe for bundle: $ffprobe"

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
