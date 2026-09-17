$ErrorActionPreference = "Stop"

$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
Write-Host "FFmpeg: $ffmpeg"
Write-Host "FFprobe: $ffprobe"

$env:PLAYWRIGHT_BROWSERS_PATH = "0"
python -m playwright install chromium

$arguments = @(
  "-m", "PyInstaller",
  "--noconfirm",
  "--clean",
  "--onefile",
  "--windowed",
  "--name", "AudioKnigiDownloader",
  "--collect-all", "playwright",
  "--collect-all", "PIL",
  "--collect-all", "mutagen",
  "--collect-all", "pygame",
  "--collect-all", "tkinterdnd2",
  "--collect-all", "customtkinter",
  "--collect-all", "pystray",
  "--collect-all", "prism",
  "--copy-metadata", "prismatoid",
  "--additional-hooks-dir=.",
  "--icon", "assets\app_icon.ico",
  "--add-data", "assets;assets",
  "--add-binary", "$ffmpeg;.",
  "--add-binary", "$ffprobe;.",
  "audioknigi_gui.py"
)
python @arguments

if (-not (Test-Path "dist\\AudioKnigiDownloader.exe")) {
  throw "PyInstaller не создал dist\\AudioKnigiDownloader.exe"
}

& "dist\\AudioKnigiDownloader.exe" --version
