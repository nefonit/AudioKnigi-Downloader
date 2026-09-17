import shutil
import subprocess
import tempfile
from pathlib import Path

from audioknigi import AudioKnigiApp, Book, Track

ffmpeg = shutil.which("ffmpeg")
ffprobe = shutil.which("ffprobe")
if not ffmpeg or not ffprobe:
    raise SystemExit("Нужны ffmpeg и ffprobe в PATH")

root = Path(tempfile.mkdtemp(prefix="audioknigi_test_"))
book_dir = root / "SmokeBook"
book_dir.mkdir(parents=True, exist_ok=True)
source = book_dir / "_source.mp3"

subprocess.run([
    ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
    "-c:a", "libmp3lame", "-b:a", "128k", str(source)
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

app = AudioKnigiApp()
app.runtime_output_dir = str(root)
app.runtime_output_mode = "mp3"
app.runtime_audio_preset = "64k_mono"
app.runtime_normalization_mode = "single"
app.runtime_normalize_audio = True
app.runtime_embed_tags = False
app.runtime_delete_source = False
app.runtime_naming_mode = "number"
app.runtime_segment_count = 1

url = "https://example.invalid/source.mp3"
tracks = [
    Track(index=1, title="01", file=url, start=0, end=2, duration=2),
    Track(index=2, title="Глава 2", file=url, start=2, end=4, duration=2),
]
book = Book(url="https://audioknigi.com.ua/test", title="SmokeBook", tracks=tracks)
app._process_book(book, [1, 2])

assert (book_dir / "01.mp3").exists()
assert (book_dir / "02.mp3").exists()
assert not any(path.suffix.lower() == ".m4b" for path in book_dir.iterdir())

for name in ("01.mp3", "02.mp3"):
    probe = subprocess.run([
        ffprobe, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(book_dir / name)
    ], capture_output=True, text=True, check=True)
    assert float(probe.stdout.strip()) > 1.0

print("MP3 + loudnorm/transcode: OK")
print("MP3-ONLY AUDIO SMOKETEST: OK")
app.destroy()
