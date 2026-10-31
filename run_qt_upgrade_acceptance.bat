@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON=%CD%\.venv-qt\Scripts\python.exe"
set "REPORT_DIR=%CD%\dist"

if "%~3"=="" goto :usage
if not exist "%PYTHON%" (
  echo ERROR: .venv-qt was not found. Build the project first with build_qt_exe.bat.
  exit /b 3
)
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"

if /I "%~1"=="before" (
  "%PYTHON%" tools\qt_upgrade_acceptance.py capture --app-dir "%~2" --exe "%~3" --output "%REPORT_DIR%\qt_upgrade_before.json"
  set "RC=%ERRORLEVEL%"
  endlocal & exit /b %RC%
)
if /I "%~1"=="after" (
  if not exist "%REPORT_DIR%\qt_upgrade_before.json" (
    echo ERROR: First run the before command to capture an old-version baseline.
    exit /b 3
  )
  "%PYTHON%" tools\qt_upgrade_acceptance.py compare --app-dir "%~2" --exe "%~3" --baseline "%REPORT_DIR%\qt_upgrade_before.json" --output "%REPORT_DIR%\qt_upgrade_after.json"
  set "RC=%ERRORLEVEL%"
  endlocal & exit /b %RC%
)

:usage
echo Use a disposable Windows APPDATA test profile, not real personal data.
echo Usage:
echo   run_qt_upgrade_acceptance.bat before "C:\AK-QA\Profile\AudioKnigiDownloader" "C:\Old\AudioKnigiDownloader_Qt.exe"
echo   run_qt_upgrade_acceptance.bat after  "C:\AK-QA\Profile\AudioKnigiDownloader" "C:\New\AudioKnigiDownloader_Qt.exe"
echo See docs\qa\UPGRADE_ACCEPTANCE_V37.md for instructions and review codes.
endlocal & exit /b 3
