@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

title AudioKnigi Downloader - Python 3.14.7 standalone EXE build

set "REQUIRED_PYTHON=3.14.7"
set "VENV_DIR=%CD%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

echo ==================================================
echo AudioKnigi Downloader - standalone EXE build
echo Required build Python: %REQUIRED_PYTHON% x64
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
rem Reuse .venv only when it was created by exactly
rem CPython 3.14.7 x64. Any old 3.13/3.14.x or 32-bit
rem environment is removed automatically.
rem --------------------------------------------------
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
    if errorlevel 1 (
        echo Existing .venv does not use required Python %REQUIRED_PYTHON% x64.
        echo Existing environment reports:
        "%VENV_PYTHON%" --version 2>nul
        echo Removing old .venv...
        rmdir /s /q "%VENV_DIR%"
        if exist "%VENV_DIR%" (
            echo ERROR: Could not remove the old .venv directory.
            goto :error
        )
    )
)

if not exist "%VENV_PYTHON%" (
    echo [0/4] Locating CPython %REQUIRED_PYTHON% x64...
    set "BASE_MODE="

    rem Preferred: Windows Python launcher / Python Install Manager.
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.14 -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
        if not errorlevel 1 set "BASE_MODE=PY"
    )

    rem Fallback: python3.14.exe if it is on PATH.
    if not defined BASE_MODE (
        where python3.14 >nul 2>nul
        if not errorlevel 1 (
            python3.14 -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
            if not errorlevel 1 set "BASE_MODE=PYTHON314"
        )
    )

    rem Last fallback: python.exe, but only if it is exactly 3.14.7 x64.
    if not defined BASE_MODE (
        where python >nul 2>nul
        if not errorlevel 1 (
            python -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
            if not errorlevel 1 set "BASE_MODE=PYTHON"
        )
    )

    if not defined BASE_MODE (
        echo.
        echo ERROR: CPython %REQUIRED_PYTHON% x64 was not found.
        echo This project is intentionally pinned to Python %REQUIRED_PYTHON% for EXE builds.
        echo Install Python %REQUIRED_PYTHON% x64 and run this file again.
        echo.
        where py >nul 2>nul
        if not errorlevel 1 (
            echo Python installations visible to the launcher:
            py -0p 2>nul
        )
        goto :error
    )

    echo Creating local .venv with Python %REQUIRED_PYTHON% x64...
    if "%BASE_MODE%"=="PY" py -3.14 -m venv "%VENV_DIR%"
    if "%BASE_MODE%"=="PYTHON314" python3.14 -m venv "%VENV_DIR%"
    if "%BASE_MODE%"=="PYTHON" python -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
)

rem Final hard check. Never continue with the wrong interpreter.
"%VENV_PYTHON%" -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
if errorlevel 1 (
    echo ERROR: .venv is not Python %REQUIRED_PYTHON% x64 after creation.
    "%VENV_PYTHON%" --version 2>nul
    goto :error
)

echo Python used for the build:
"%VENV_PYTHON%" --version
"%VENV_PYTHON%" -c "import sys,struct; print('Executable:', sys.executable); print('Architecture:', struct.calcsize('P')*8, 'bit')"
if errorlevel 1 goto :error

echo.
echo [1/4] Installing/updating dependencies into .venv...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error
"%VENV_PYTHON%" -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Verifying PyInstaller and Prismatoid in the SAME Python environment...
"%VENV_PYTHON%" -c "import importlib.metadata as m; from packaging.version import Version; v=Version(m.version('prismatoid')); assert v>=Version('0.18.1'); print('PyInstaller:', m.version('pyinstaller')); print('prismatoid:', v); from prism import BackendId, Context; assert BackendId.NVDA and BackendId.JAWS; print('prism NVDA/JAWS API: OK')"
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
echo [4/4] Building executable with Python %REQUIRED_PYTHON%...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_ci.ps1" -PythonExe "%VENV_PYTHON%" -SkipBrowserInstall
if errorlevel 1 goto :error

echo.
echo ==================================================
echo BUILD COMPLETE - Python %REQUIRED_PYTHON% x64
echo File: dist\AudioKnigiDownloader.exe
echo ==================================================
pause
endlocal
exit /b 0

:error
echo.
echo ==================================================
echo BUILD FAILED
echo Required build Python: %REQUIRED_PYTHON% x64
echo See the error messages above.
echo ==================================================
pause
endlocal
exit /b 1
