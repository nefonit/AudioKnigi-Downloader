param(
    [string]$PythonExe = "",
    [switch]$SkipEdgeCheck
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
    $localPython = Join-Path $PSScriptRoot ".venv-qt\Scripts\python.exe"
    if (Test-Path $localPython) {
        return (Resolve-Path -LiteralPath $localPython).Path
    }
    return (Get-Command python -ErrorAction Stop).Source
}

function Get-Sha256Hex {
    param([Parameter(Mandatory=$true)][string]$Path)

    # Do not depend on Get-FileHash. Some locked-down/embedded Windows
    # PowerShell environments do not expose Microsoft.PowerShell.Utility
    # even though the .NET cryptography APIs are available.
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($Path)
        try {
            $bytes = $sha256.ComputeHash($stream)
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha256.Dispose()
    }
    return (-join ($bytes | ForEach-Object { $_.ToString("x2") }))
}

$PythonExe = Resolve-BuildPython -RequestedPython $PythonExe
Write-Host "Qt build Python: $PythonExe"

$pythonFacts = & $PythonExe -c "import sys,struct; print('.'.join(map(str,sys.version_info[:3]))+'|'+str(struct.calcsize('P')*8))"
if ($LASTEXITCODE -ne 0) { throw "Python failed to start." }
$parts = ($pythonFacts | Select-Object -Last 1).Trim().Split('|')
if ($parts.Count -ne 2) { throw "Could not determine Python version/architecture." }
if ($parts[0] -ne $RequiredPythonVersion) {
    throw "Wrong Qt build Python: $($parts[0]). Required: $RequiredPythonVersion."
}
if ([int]$parts[1] -ne $RequiredArchitecture) {
    throw "Wrong Qt build architecture: $($parts[1])-bit. Required: 64-bit."
}

Write-Host "Qt package preflight..."
& $PythonExe -c "import importlib.metadata as m, PySide6; from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput; from PySide6.QtWidgets import QSystemTrayIcon; print('PyInstaller:',m.version('pyinstaller')); print('PySide6:',PySide6.__version__); print('Qt Multimedia/tray: OK')"
if ($LASTEXITCODE -ne 0) { throw "Qt build dependencies are incomplete." }

Write-Host "Static Qt import-boundary audit..."
& $PythonExe "tools\qt_import_audit.py" --verbose
if ($LASTEXITCODE -ne 0) { throw "Qt import-boundary audit failed." }

function Test-MediaToolExecutable {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Name
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    try {
        & $Path -hide_banner -version *> $null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Test-IsChocolateyBinShim {
    param([Parameter(Mandatory=$true)][string]$Path)
    $chocoRoot = $env:ChocolateyInstall
    if ([string]::IsNullOrWhiteSpace($chocoRoot)) { $chocoRoot = "C:\ProgramData\chocolatey" }
    try {
        $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
        $chocoBin = [IO.Path]::GetFullPath((Join-Path $chocoRoot "bin")).TrimEnd('\') + '\'
        return $fullPath.StartsWith($chocoBin, [StringComparison]::OrdinalIgnoreCase)
    } catch { return $false }
}

function Resolve-RealMediaTool {
    param([Parameter(Mandatory=$true)][string]$Name)
    $candidatePaths = New-Object System.Collections.Generic.List[string]
    $localTool = Join-Path $PSScriptRoot ("tools\" + $Name + ".exe")
    if (Test-Path -LiteralPath $localTool -PathType Leaf) { $candidatePaths.Add($localTool) }
    try {
        $cmd = Get-Command $Name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) { $candidatePaths.Add([string]$cmd.Source) }
    } catch {}
    try {
        $whereResults = & where.exe ($Name + ".exe") 2>$null
        foreach ($item in @($whereResults)) {
            if (-not [string]::IsNullOrWhiteSpace([string]$item)) { $candidatePaths.Add(([string]$item).Trim()) }
        }
    } catch {}

    $chocoRoot = $env:ChocolateyInstall
    if ([string]::IsNullOrWhiteSpace($chocoRoot)) { $chocoRoot = "C:\ProgramData\chocolatey" }
    $chocoLib = Join-Path $chocoRoot "lib"
    if (Test-Path -LiteralPath $chocoLib -PathType Container) {
        try {
            $packageDirs = Get-ChildItem -LiteralPath $chocoLib -Directory -Filter "ffmpeg*" -ErrorAction SilentlyContinue
            foreach ($packageDir in @($packageDirs)) {
                $found = Get-ChildItem -LiteralPath $packageDir.FullName -File -Recurse -Filter ($Name + ".exe") -ErrorAction SilentlyContinue |
                    Sort-Object @{Expression={ if ($_.FullName -match "\\bin\\") { 0 } else { 1 } }}, LastWriteTime -Descending
                foreach ($file in @($found)) { $candidatePaths.Add($file.FullName) }
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
        if (Test-MediaToolExecutable -Path $full -Name $Name) { return $full }
    }
    throw "Could not find a real $Name executable. Install FFmpeg or place real $Name.exe under .\tools."
}

$ffmpeg = Resolve-RealMediaTool -Name "ffmpeg"
$ffprobe = Resolve-RealMediaTool -Name "ffprobe"
Write-Host "FFmpeg bundled from: $ffmpeg"
Write-Host "FFprobe bundled from: $ffprobe"

# Keep the Playwright Python/Node driver, but never bundle its Chromium cache.
Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH -ErrorAction SilentlyContinue
$localBrowserDir = (& $PythonExe -c "import pathlib,playwright; print(pathlib.Path(playwright.__file__).resolve().parent / 'driver' / 'package' / '.local-browsers')" | Select-Object -Last 1).Trim()
if (Test-Path -LiteralPath $localBrowserDir -PathType Container) {
    Write-Host "Removing Playwright browser cache from Qt build environment: $localBrowserDir"
    Remove-Item -LiteralPath $localBrowserDir -Recurse -Force
}
if (-not $SkipEdgeCheck) {
    Write-Host "Playwright compact-mode preflight: installed Microsoft Edge..."
    & $PythonExe -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(channel='msedge',headless=True); print('Microsoft Edge:',b.version); b.close(); p.stop()"
    if ($LASTEXITCODE -ne 0) {
        throw "Microsoft Edge could not be launched by Playwright. Qt compact builds do not bundle Chromium."
    }
}

Write-Host "Source Qt window/accessibility preflight (offscreen)..."
& $PythonExe "audioknigi_qt.py" "--qt-accessibility-selftest"
if ($LASTEXITCODE -ne 0) {
    throw "Source Qt window/accessibility self-test failed before PyInstaller. Fix the source startup/runtime error first."
}

$pyinstallerBootstrap = Join-Path $PSScriptRoot "tools\pyinstaller_bootstrap.py"
if (-not (Test-Path -LiteralPath $pyinstallerBootstrap -PathType Leaf)) {
    throw "PyInstaller bootstrap was not found: $pyinstallerBootstrap"
}
Write-Host "PyInstaller bootstrap preflight..."
& $PythonExe $pyinstallerBootstrap "--bootstrap-selftest"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller bootstrap self-test failed." }

$arguments = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name", "AudioKnigiDownloader_Qt",
    "--collect-all", "playwright",
    "--copy-metadata", "playwright",
    "--copy-metadata", "PySide6",
    "--hidden-import", "PySide6.QtMultimedia",
    "--hidden-import", "PySide6.QtWidgets",
    "--icon", "assets\app_icon.ico",
    "--add-data", "assets;assets",
    "--add-data", "audioknigi\locales;audioknigi\locales",
    "--add-binary", "$ffmpeg;.",
    "--add-binary", "$ffprobe;.",
    "--exclude-module", "tkinter",
    "--exclude-module", "_tkinter",
    "--exclude-module", "ttkbootstrap",
    "--exclude-module", "tkinterdnd2",
    "--exclude-module", "pygame",
    "--exclude-module", "pystray",
    "--exclude-module", "plyer",
    "--exclude-module", "prism",
    "--exclude-module", "tk_uia",
    "audioknigi_qt.py"
)

Write-Host "Building compact Qt executable..."
& $PythonExe $pyinstallerBootstrap @arguments
if ($LASTEXITCODE -ne 0) { throw "Qt PyInstaller build failed with exit code $LASTEXITCODE." }

$exe = Join-Path $PSScriptRoot "dist\AudioKnigiDownloader_Qt.exe"
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw "PyInstaller did not create dist\AudioKnigiDownloader_Qt.exe"
}

# Keep release/legal notices visible next to the standalone executable.
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "THIRD_PARTY_NOTICES.md") -Destination (Join-Path $PSScriptRoot "dist\THIRD_PARTY_NOTICES.md") -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "docs\development\RELEASE_LICENSING.md") -Destination (Join-Path $PSScriptRoot "dist\RELEASE_LICENSING.md") -Force

# Analysis-00.toc also serializes build metadata such as the `excludes` list.
# A raw text search therefore sees names like `tkinter` even when PyInstaller
# correctly excluded them.  Parse the TOC and inspect only real collected
# module/extension entries.
$toc = Join-Path $PSScriptRoot "build\AudioKnigiDownloader_Qt\Analysis-00.toc"
if (-not (Test-Path -LiteralPath $toc -PathType Leaf)) { throw "PyInstaller Analysis-00.toc was not found." }
Write-Host "Frozen Qt module-boundary audit..."
& $PythonExe "tools\qt_frozen_module_audit.py" $toc
if ($LASTEXITCODE -ne 0) { throw "Qt frozen module-boundary audit failed with exit code $LASTEXITCODE." }
Write-Host "Frozen module-boundary check: OK"

$runtimeReport = Join-Path $PSScriptRoot "dist\qt_runtime_frozen_selftest.txt"
Remove-Item -LiteralPath $runtimeReport -Force -ErrorAction SilentlyContinue
$env:AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT = $runtimeReport
Write-Host "Frozen Qt runtime self-test..."
$runtimeProcess = Start-Process -FilePath $exe -ArgumentList "--qt-runtime-selftest" -Wait -PassThru
$runtimeExit = $runtimeProcess.ExitCode
Remove-Item Env:AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT -ErrorAction SilentlyContinue
if ($runtimeExit -ne 0) { throw "Frozen Qt runtime self-test failed with exit $runtimeExit." }
if (-not (Test-Path -LiteralPath $runtimeReport)) { throw "Frozen Qt runtime self-test report was not created." }
$runtimeText = Get-Content -LiteralPath $runtimeReport -Raw
if (-not $runtimeText.StartsWith("OK")) { throw "Frozen Qt runtime self-test did not report OK." }
Write-Host $runtimeText

$accessibilityReport = Join-Path $PSScriptRoot "dist\qt_accessibility_frozen_selftest.txt"
Remove-Item -LiteralPath $accessibilityReport -Force -ErrorAction SilentlyContinue
$env:AUDIOKNIGI_QT_ACCESSIBILITY_SELFTEST_REPORT = $accessibilityReport
Write-Host "Frozen Qt accessibility contract self-test..."
$accessibilityProcess = Start-Process -FilePath $exe -ArgumentList "--qt-accessibility-selftest" -Wait -PassThru
$accessibilityExit = $accessibilityProcess.ExitCode
Remove-Item Env:AUDIOKNIGI_QT_ACCESSIBILITY_SELFTEST_REPORT -ErrorAction SilentlyContinue
if ($accessibilityExit -ne 0) { throw "Frozen Qt accessibility self-test failed with exit $accessibilityExit." }
if (-not (Test-Path -LiteralPath $accessibilityReport)) { throw "Frozen Qt accessibility self-test report was not created." }
$accessibilityText = Get-Content -LiteralPath $accessibilityReport -Raw
if (-not $accessibilityText.StartsWith("OK")) { throw "Frozen Qt accessibility self-test did not report OK." }
Write-Host $accessibilityText

$playwrightReport = Join-Path $PSScriptRoot "dist\playwright_edge_qt_frozen_selftest.txt"
Remove-Item -LiteralPath $playwrightReport -Force -ErrorAction SilentlyContinue
$env:AUDIOKNIGI_PLAYWRIGHT_SELFTEST_REPORT = $playwrightReport
Write-Host "Frozen Qt Playwright/Edge self-test..."
$playwrightProcess = Start-Process -FilePath $exe -ArgumentList "--playwright-edge-selftest" -Wait -PassThru
$playwrightExit = $playwrightProcess.ExitCode
Remove-Item Env:AUDIOKNIGI_PLAYWRIGHT_SELFTEST_REPORT -ErrorAction SilentlyContinue
if ($playwrightExit -ne 0) { throw "Frozen Qt Playwright/Edge self-test failed with exit $playwrightExit." }
if (-not (Test-Path -LiteralPath $playwrightReport)) { throw "Frozen Qt Playwright self-test report was not created." }
$playwrightText = Get-Content -LiteralPath $playwrightReport -Raw
if (-not $playwrightText.StartsWith("OK")) { throw "Frozen Qt Playwright self-test did not report OK." }
Write-Host $playwrightText

$exeItem = Get-Item -LiteralPath $exe
$exeSizeMB = [math]::Round(($exeItem.Length / 1MB), 1)
$exeHash = (Get-Sha256Hex -Path $exe).ToLowerInvariant()
$appVersion = ((& $PythonExe -c "from audioknigi.core import APP_VERSION; print(APP_VERSION)") | Select-Object -Last 1).Trim()
$migrationStage = ((& $PythonExe -c "from audioknigi.qt import QT_MIGRATION_STAGE; print(QT_MIGRATION_STAGE)") | Select-Object -Last 1).Trim()
$candidateManifest = [ordered]@{
    schema = 1
    app_version = $appVersion
    migration_stage = $migrationStage
    platform = "windows"
    exe = [IO.Path]::GetFileName($exe)
    exe_sha256 = $exeHash
    size_bytes = [int64]$exeItem.Length
    built_at_utc = [DateTime]::UtcNow.ToString("o")
    automated = [ordered]@{
        runtime = "pass"
        accessibility = "pass"
        playwright_edge = "pass"
        import_boundary = "pass"
        frozen_module_boundary = "pass"
    }
    manual_screen_reader_acceptance = "required"
    licensing_review = "required"
}
$candidatePath = Join-Path $PSScriptRoot "dist\qt_release_candidate.json"
$candidateManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $candidatePath -Encoding utf8
Write-Host "Qt EXE size: $exeSizeMB MB"
Write-Host "Qt EXE SHA-256: $exeHash"
Write-Host "Release-candidate manifest: $candidatePath"
Write-Host "Qt build completed with a clean import graph, frozen accessibility contract, bundled FFmpeg/FFprobe, Qt Multimedia/tray and system Edge Playwright fallback."
Write-Host "Run run_qt_acceptance.bat with NVDA and JAWS for this exact EXE hash before release sign-off."
