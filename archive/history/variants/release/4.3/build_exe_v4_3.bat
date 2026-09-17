@echo off
chcp 65001 >nul
title AudioKnigi Downloader 4.3 - Сборка EXE

echo ==================================================
echo AudioKnigi Downloader 4.3
echo ==================================================
echo.

echo [1/4] Устанавливаю зависимости...
py -m pip install -r requirements_v4_3.txt
if errorlevel 1 goto :error

echo.
echo [2/4] Устанавливаю Chromium только для Playwright fallback...
py -m playwright install chromium
if errorlevel 1 goto :error

echo.
echo [3/4] Проверяю FFmpeg / FFprobe...
where ffmpeg >nul 2>nul
if errorlevel 1 echo ВНИМАНИЕ: ffmpeg не найден в PATH.
where ffprobe >nul 2>nul
if errorlevel 1 echo ВНИМАНИЕ: ffprobe не найден в PATH.

echo.
echo [4/4] Собираю EXE...
py -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name AudioKnigiDownloader ^
  --collect-all playwright ^
  --collect-all PIL ^
  --collect-all mutagen ^
  --collect-all pygame ^
  --collect-all customtkinter ^
  --collect-all pystray ^
  audioknigi_gui_v4_3.py

if errorlevel 1 goto :error

echo.
echo ==================================================
echo ГОТОВО:
echo dist\AudioKnigiDownloader\AudioKnigiDownloader.exe
echo ==================================================
pause
exit /b 0

:error
echo.
echo ==================================================
echo ОШИБКА СБОРКИ
echo ==================================================
pause
exit /b 1
