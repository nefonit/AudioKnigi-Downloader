@echo off
setlocal
cd /d "%~dp0"
set "QT_PYTHON=%CD%\.venv-qt\Scripts\python.exe"
if not exist "%QT_PYTHON%" set "QT_PYTHON=python"
"%QT_PYTHON%" -c "import PySide6" >nul 2>nul
if errorlevel 1 (
  echo PySide6 is not installed in the selected Qt environment.
  echo Run: python -m pip install -r requirements-qt.txt
  echo Or run build_qt_exe.bat to create the isolated .venv-qt build environment.
  exit /b 2
)
"%QT_PYTHON%" tools\qt_import_audit.py >nul
if errorlevel 1 (
  echo Qt runtime-boundary audit failed. Run tools\qt_import_audit.py --verbose for details.
  exit /b 3
)
"%QT_PYTHON%" audioknigi_qt.py %*
endlocal
