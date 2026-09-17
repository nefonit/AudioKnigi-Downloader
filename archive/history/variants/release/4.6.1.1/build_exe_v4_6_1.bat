@echo off
chcp 65001 >nul
title AudioKnigi Downloader 4.6.1.1 - Сборка EXE

echo ==================================================
echo AudioKnigi Downloader 4.6.1.1 - standalone EXE
echo ==================================================
echo.

py -m pip install -r requirements_v4_6_1.txt
if errorlevel 1 goto :error

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo ОШИБКА: FFmpeg не найден в PATH.
  goto :error
)

powershell -NoProfile -ExecutionPolicy Bypass -File build_ci.ps1
if errorlevel 1 goto :error

echo.
echo ГОТОВО: dist\AudioKnigiDownloader.exe
pause
exit /b 0

:error
echo.
echo Сборка завершилась с ошибкой.
pause
exit /b 1
