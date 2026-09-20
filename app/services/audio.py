"""Разбор WAV-заголовков стандартной библиотекой. Без сети."""

from __future__ import annotations

import io
import wave

from pydantic import BaseModel


class AudioMeta(BaseModel):
    duration_sec: float
    channels: int
    sample_rate: int
    sample_width: int


def parse_wav(raw: bytes) -> AudioMeta:
    """Прочитать метаданные WAV. Детерминировано."""
    if not raw:
        raise ValueError("empty audio data")
    try:
        with wave.open(io.BytesIO(raw), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            if rate <= 0:
                raise ValueError("invalid sample rate")
            return AudioMeta(
                duration_sec=round(frames / rate, 2),
                channels=wav.getnchannels(),
                sample_rate=rate,
                sample_width=wav.getsampwidth(),
            )
    except wave.Error as exc:
        raise ValueError(f"cannot decode WAV: {exc}") from exc
