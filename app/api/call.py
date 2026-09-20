"""Эндпоинты звонков и аудио."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.audio import AudioMeta, parse_wav
from app.services.intent import CallResult, handle_call

router = APIRouter()


class CallRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=5000)
    caller: str = Field(default="", max_length=100)


class CallResponse(BaseModel):
    intent: str
    confidence: float
    reply: str
    tts_estimate_sec: float
    audio: AudioMeta | None = None


def _respond(text: str, name: str, meta: AudioMeta | None, settings: Settings) -> CallResponse:
    try:
        result: CallResult = handle_call(text.strip(), name.strip(), settings.chars_per_sec)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CallResponse(
        intent=result.intent,
        confidence=result.confidence,
        reply=result.reply,
        tts_estimate_sec=result.tts_estimate_sec,
        audio=meta,
    )


@router.post("/audio-info", response_model=AudioMeta)
async def audio_info(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> AudioMeta:
    raw = await file.read()
    if len(raw) > settings.max_audio_mb * 1024 * 1024:
        raise HTTPException(status_code=422, detail=f"audio exceeds {settings.max_audio_mb} MB")
    try:
        return parse_wav(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/call", response_model=CallResponse)
async def call(request: CallRequest, settings: Settings = Depends(get_settings)) -> CallResponse:
    return _respond(request.transcript, request.caller, None, settings)


@router.post("/call-audio", response_model=CallResponse)
async def call_audio(
    file: UploadFile = File(...),
    transcript: str = Form(default=""),
    caller: str = Form(default=""),
    settings: Settings = Depends(get_settings),
) -> CallResponse:
    raw = await file.read()
    if len(raw) > settings.max_audio_mb * 1024 * 1024:
        raise HTTPException(status_code=422, detail=f"audio exceeds {settings.max_audio_mb} MB")
    try:
        meta = parse_wav(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not transcript.strip():
        raise HTTPException(status_code=422, detail="transcript must not be empty")
    return _respond(transcript, caller, meta, settings)
