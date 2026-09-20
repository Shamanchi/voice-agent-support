"""Unit-тесты аудио и звонков: без сети, детерминированы."""

import io
import wave

import pytest

from app.services.audio import parse_wav
from app.services.intent import classify, handle_call


def _wav(seconds: float = 2.0, rate: int = 8000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * int(seconds * rate))
    return buffer.getvalue()


def test_wav_metadata() -> None:
    meta = parse_wav(_wav(2.0, 8000))
    assert meta.duration_sec == 2.0
    assert meta.channels == 1
    assert meta.sample_rate == 8000
    assert meta.sample_width == 2
    with pytest.raises(ValueError):
        parse_wav(b"")
    with pytest.raises(ValueError):
        parse_wav(b"not audio")


def test_classify_billing() -> None:
    intent, confidence, matched = classify("My bill is wrong, help with payment")
    assert intent == "billing"
    assert confidence == 0.67
    assert set(matched) == {"bill", "payment"}


def test_handle_call_reply() -> None:
    result = handle_call("My bill is wrong", "Ann")
    assert result.intent == "billing"
    assert result.reply.startswith("Ann,")
    assert result.tts_estimate_sec == round(len(result.reply) / 15.0, 1)
    with pytest.raises(ValueError):
        handle_call("   ")
