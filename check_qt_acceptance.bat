@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "QT_PYTHON=%CD%\.venv-qt\Scripts\python.exe"
set "QT_EXE=%CD%\dist\AudioKnigiDownloader_Qt.exe"
if not exist "%QT_PYTHON%" (
  echo ERROR: .venv-qt is not found. Run build_qt_exe.bat first.
  exit /b 2
)
if not exist "%QT_EXE%" (
  echo ERROR: dist\AudioKnigiDownloader_Qt.exe is not found. Run build_qt_exe.bat first.
  exit /b 3
)
"%QT_PYTHON%" tools\qt_windows_acceptance.py --status --exe "%QT_EXE%" --report "%CD%\dist\qt_windows_acceptance.json"
set "RC=%ERRORLEVEL%"
pause
endlocal & exit /b %RC%
