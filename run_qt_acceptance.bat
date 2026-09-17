@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "QT_PYTHON=%CD%\.venv-qt\Scripts\python.exe"
set "QT_EXE=%CD%\dist\AudioKnigiDownloader_Qt.exe"

if not exist "%QT_PYTHON%" (
  echo ERROR: .venv-qt is not found.
  echo First run build_qt_exe.bat.
  exit /b 2
)
if not exist "%QT_EXE%" (
  echo ERROR: dist\AudioKnigiDownloader_Qt.exe is not found.
  echo First run build_qt_exe.bat.
  exit /b 3
)

echo ==================================================
echo AudioKnigi Downloader Qt - Windows NVDA/JAWS acceptance
echo The report is tied to the SHA-256 of this exact EXE.
echo ==================================================
echo.
"%QT_PYTHON%" tools\qt_windows_acceptance.py --exe "%QT_EXE%" --report "%CD%\dist\qt_windows_acceptance.json" %*
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo ACCEPTANCE COMPLETE: PASS
) else (
  echo ACCEPTANCE NOT COMPLETE. See dist\qt_windows_acceptance.json
)
pause
endlocal & exit /b %RC%
