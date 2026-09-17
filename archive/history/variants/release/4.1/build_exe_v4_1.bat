@echo off
chcp 65001 >nul
title AudioKnigi Downloader 4.1 - Сборка EXE

echo ==================================================
echo AudioKnigi Downloader 4.1
echo ==================================================
echo.

py -m pip install --upgrade pip
if errorlevel 1 goto :error

py -m pip install -r requirements_v4_1.txt
if errorlevel 1 goto :error

echo.
echo Playwright нужен только как fallback.
echo Устанавливаю Chromium для fallback...
py -m playwright install chromium
if errorlevel 1 goto :error

echo.
echo Собираю EXE...
py -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name AudioKnigiDownloader ^
  --collect-all playwright ^
  --collect-all PIL ^
  --collect-all mutagen ^
  --collect-all pygame ^
  audioknigi_gui_v4_1.py

if errorlevel 1 goto :error

echo.
echo ГОТОВО:
echo dist\AudioKnigiDownloader\AudioKnigiDownloader.exe
pause
exit /b 0

:error
echo.
echo ОШИБКА СБОРКИ
pause
exit /b 1
