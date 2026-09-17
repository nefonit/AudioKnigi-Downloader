@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

rem Phase 13 Qt-only launcher.  The legacy Tk UI has been retired from this tree.
set "QT_EXE=%CD%\dist\AudioKnigiDownloader_Qt.exe"
if exist "%QT_EXE%" (
  start "" "%QT_EXE%" %*
  endlocal
  exit /b 0
)

set "QT_PYTHON=%CD%\.venv-qt\Scripts\python.exe"
if exist "%QT_PYTHON%" (
  "%QT_PYTHON%" audioknigi_qt.py %*
  set "RC=%ERRORLEVEL%"
  endlocal & exit /b %RC%
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3.14 audioknigi_qt.py %*
  set "RC=%ERRORLEVEL%"
  endlocal & exit /b %RC%
)
python audioknigi_qt.py %*
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
