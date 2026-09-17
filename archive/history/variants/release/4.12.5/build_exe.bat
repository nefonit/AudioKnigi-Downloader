@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

title AudioKnigi Downloader - standalone EXE build

echo ==================================================
echo AudioKnigi Downloader - standalone EXE build
echo ==================================================
echo.

if not exist "requirements.txt" (
    echo ERROR: requirements.txt was not found in:
    echo %CD%
    goto :error
)

if not exist "build_ci.ps1" (
    echo ERROR: build_ci.ps1 was not found in:
    echo %CD%
    goto :error
)

rem --------------------------------------------------
rem Use ONE isolated Python environment for everything.
rem This prevents the py.exe / python.exe version mismatch.
rem --------------------------------------------------
set "VENV_DIR=%CD%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [0/4] Creating local Python virtual environment...

    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.13 -m venv "%VENV_DIR%" >nul 2>nul
    )

    if not exist "%VENV_PYTHON%" (
        where python >nul 2>nul
        if errorlevel 1 (
            echo ERROR: Neither a usable Python 3.13 launcher nor python.exe was found.
            goto :error
        )
        python -m venv "%VENV_DIR%"
        if errorlevel 1 goto :error
    )
)

echo Python used for the build:
"%VENV_PYTHON%" --version
if errorlevel 1 goto :error

echo.
echo [1/4] Installing/updating dependencies into .venv...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Verifying Prismatoid in the SAME Python environment...
"%VENV_PYTHON%" -c "import importlib.metadata as m; print('prismatoid:', m.version('prismatoid')); import prism; print('prism import: OK')"
if errorlevel 1 goto :error

echo.
echo [2/4] Checking FFmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo ERROR: FFmpeg was not found in PATH.
    goto :error
)
where ffprobe >nul 2>nul
if errorlevel 1 (
    echo ERROR: FFprobe was not found in PATH.
    goto :error
)

echo.
echo [3/4] Installing Playwright Chromium into the local .venv...
set "PLAYWRIGHT_BROWSERS_PATH=0"
"%VENV_PYTHON%" -m playwright install chromium
if errorlevel 1 goto :error

echo.
echo [4/4] Building executable...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_ci.ps1" -PythonExe "%VENV_PYTHON%" -SkipBrowserInstall
if errorlevel 1 goto :error

echo.
echo ==================================================
echo BUILD COMPLETE
echo File: dist\AudioKnigiDownloader.exe
echo ==================================================
pause
endlocal
exit /b 0

:error
echo.
echo ==================================================
echo BUILD FAILED
echo See the error messages above.
echo ==================================================
pause
endlocal
exit /b 1
