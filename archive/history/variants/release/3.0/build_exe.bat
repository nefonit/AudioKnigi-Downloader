@echo off
chcp 65001 >nul
title Сборка AudioKnigi Downloader EXE

echo ==============================================
echo AudioKnigi Downloader - сборка EXE
echo ==============================================
echo.

py -m pip install --upgrade pip
py -m pip install -r requirements.txt

echo.
echo Устанавливаю Chromium для Playwright...
py -m playwright install chromium

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
  audioknigi_gui_v3_0.py

echo.
echo ==============================================
echo Готово.
echo EXE находится в:
echo dist\AudioKnigiDownloader\AudioKnigiDownloader.exe
echo ==============================================
pause
