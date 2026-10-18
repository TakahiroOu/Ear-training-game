"""Convert the piano samples in sounds/ (WAV) to MP3 for the web app.

WAV files are uncompressed (~20 MB in total), which is slow to download in a browser.
MP3 at 128 kbit/s sounds the same for this game and is about 10x smaller.

Usage (from the project folder):
    python scripts/convert_sounds.py

Needs ffmpeg. If the `ffmpeg` command isn't found, set FFMPEG to the full path of ffmpeg.exe.
"""

import os
import shutil
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT / "sounds"
TARGET = PROJECT / "frontend" / "public" / "sounds"


def main():
    ffmpeg = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found. Install it (winget install ffmpeg) or set FFMPEG.")

    TARGET.mkdir(parents=True, exist_ok=True)
    wav_files = sorted(SOURCE.glob("*.wav"))
    for wav in wav_files:
        mp3 = TARGET / (wav.stem + ".mp3")
        subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "128k", str(mp3)],
            check=True,
        )
        print(f"{wav.name} -> {mp3.name}")
    print(f"Converted {len(wav_files)} files into {TARGET}")


if __name__ == "__main__":
    main()
