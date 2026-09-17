@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

title AudioKnigi Downloader Qt - clean standalone EXE build

set "REQUIRED_PYTHON=3.14.7"
set "VENV_DIR=%CD%\.venv-qt"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

echo ==================================================
echo AudioKnigi Downloader Qt - clean standalone build
echo Required build Python: %REQUIRED_PYTHON% x64
echo ==================================================
echo.

if not exist "requirements-qt-build.txt" (
    echo ERROR: requirements-qt-build.txt was not found.
    goto :error
)
if not exist "build_qt_ci.ps1" (
    echo ERROR: build_qt_ci.ps1 was not found.
    goto :error
)
if not exist "tools\qt_import_audit.py" (
    echo ERROR: tools\qt_import_audit.py was not found.
    goto :error
)
if not exist "tools\pyinstaller_bootstrap.py" (
    echo ERROR: tools\pyinstaller_bootstrap.py was not found.
    goto :error
)

rem Use an isolated Qt build environment so release dependencies stay deterministic.
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
    if errorlevel 1 (
        echo Existing .venv-qt uses a different Python. Recreating it...
        rmdir /s /q "%VENV_DIR%"
        if exist "%VENV_DIR%" goto :error
    )
)

if not exist "%VENV_PYTHON%" (
    echo [0/4] Locating CPython %REQUIRED_PYTHON% x64...
    set "BASE_MODE="
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.14 -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
        if not errorlevel 1 set "BASE_MODE=PY"
    )
    if not defined BASE_MODE (
        where python3.14 >nul 2>nul
        if not errorlevel 1 (
            python3.14 -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
            if not errorlevel 1 set "BASE_MODE=PYTHON314"
        )
    )
    if not defined BASE_MODE (
        where python >nul 2>nul
        if not errorlevel 1 (
            python -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
            if not errorlevel 1 set "BASE_MODE=PYTHON"
        )
    )
    if not defined BASE_MODE (
        echo ERROR: CPython %REQUIRED_PYTHON% x64 was not found.
        goto :error
    )

    echo Found required Python via: !BASE_MODE!

    if "!BASE_MODE!"=="PY" py -3.14 -m venv "%VENV_DIR%"
    if "!BASE_MODE!"=="PYTHON314" python3.14 -m venv "%VENV_DIR%"
    if "!BASE_MODE!"=="PYTHON" python -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
)

"%VENV_PYTHON%" -c "import sys,struct; raise SystemExit(0 if sys.version_info[:3]==(3,14,7) and struct.calcsize('P')*8==64 else 1)" >nul 2>nul
if errorlevel 1 goto :error

echo [1/4] Installing ONLY Qt build dependencies into .venv-qt...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error
"%VENV_PYTHON%" -m pip install --upgrade -r requirements-qt-build.txt
if errorlevel 1 goto :error

echo.
echo [2/4] Static Qt runtime-boundary audit...
"%VENV_PYTHON%" tools\qt_import_audit.py --verbose
if errorlevel 1 goto :error

echo.
echo [3/4] Verifying Qt Multimedia and native tray imports...
"%VENV_PYTHON%" -c "import PySide6; from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput; from PySide6.QtWidgets import QSystemTrayIcon; print('PySide6:',PySide6.__version__); print('Qt Multimedia/tray: OK')"
if errorlevel 1 goto :error

echo.
echo [4/4] Building and frozen-self-testing Qt executable...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_qt_ci.ps1" -PythonExe "%VENV_PYTHON%"
if errorlevel 1 goto :error

echo.
echo ==================================================
echo QT BUILD COMPLETE
echo File: dist\AudioKnigiDownloader_Qt.exe
echo Candidate manifest: dist\qt_release_candidate.json
echo Next gate: run_qt_acceptance.bat ^(NVDA + JAWS on this exact EXE^)
echo ==================================================
pause
endlocal
exit /b 0

:error
echo.
echo ==================================================
echo QT BUILD FAILED
echo Existing source and user data were not modified.
echo ==================================================
pause
endlocal
exit /b 1
