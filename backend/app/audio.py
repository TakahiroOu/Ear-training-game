"""Mixes piano samples into one audio clip on the server.

Used for competitions: the browser gets only the sound, never the note names,
so the answer can't be read from the page's code.
"""

import io
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np

from app import config

RATE = 22050  # half of the samples' 44.1 kHz: plenty for piano, and half the download size
SECONDS = 3.0
FADE_SECONDS = 0.3


def sample_file(note):
    """'C#4' -> sounds/C4s.wav (the files put 's' for sharp at the end)"""
    name = note.replace("#", "")[:-1] + note[-1] + ("s" if "#" in note else "")
    return Path(config.SOUNDS_DIR) / f"{name}.wav"


@lru_cache(maxsize=64)
def load(note):
    """One note as mono samples between -1 and 1, at RATE."""
    with wave.open(str(sample_file(note))) as file:
        frames = np.frombuffer(file.readframes(file.getnframes()), dtype=np.int16)
        channels = file.getnchannels()
    mono = frames.reshape(-1, channels).mean(axis=1) / 32768
    usable = len(mono) // 2 * 2
    return mono[:usable].reshape(-1, 2).mean(axis=1)  # 44.1 kHz -> 22.05 kHz


def render(notes):
    """WAV bytes of the notes played together."""
    length = int(RATE * SECONDS)
    mix = np.zeros(length)
    for note in notes:
        samples = load(note)[:length]
        mix[: len(samples)] += samples

    fade = int(RATE * FADE_SECONDS)
    mix[-fade:] *= np.linspace(1, 0, fade)
    peak = np.abs(mix).max()
    if peak > 0.9:
        mix *= 0.9 / peak  # chords get louder: turn down instead of distorting

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes((mix * 32767).astype(np.int16).tobytes())
    return buffer.getvalue()
