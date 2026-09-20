"""API-тесты без сети: TestClient."""

import io
import wave

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def _wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 8000)
    return buffer.getvalue()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_audio_info(client: TestClient) -> None:
    resp = client.post("/api/v1/audio-info", files={"file": ("a.wav", _wav(), "audio/wav")})
    assert resp.status_code == 200
    assert resp.json()["duration_sec"] == 1.0


def test_call(client: TestClient) -> None:
    resp = client.post("/api/v1/call", json={"transcript": "My bill is wrong", "caller": "Ann"})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "billing"
    assert resp.json()["audio"] is None


def test_call_audio(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/call-audio",
        files={"file": ("a.wav", _wav(), "audio/wav")},
        data={"transcript": "App crash on login", "caller": "Bob"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["intent"] == "technical"
    assert payload["audio"]["duration_sec"] == 1.0


@pytest.mark.integration()
def test_call_audio_requires_transcript(client: TestClient) -> None:
    """Интеграционный по маркеру: аудио без транскрипта, без сети."""
    resp = client.post(
        "/api/v1/call-audio",
        files={"file": ("a.wav", _wav(), "audio/wav")},
        data={"transcript": "   "},
    )
    assert resp.status_code == 422
