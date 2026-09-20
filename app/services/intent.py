"""Интент звонка и разговорный ответ. Без сети."""

from __future__ import annotations

import re

from pydantic import BaseModel

INTENTS: dict[str, list[str]] = {
    "billing": ["bill", "invoice", "charge", "payment", "refund", "счёт", "счет", "оплата"],
    "technical": ["error", "crash", "login", "broken", "ошибка", "вход", "сломан"],
    "general": ["question", "help", "info", "вопрос", "помощь"],
}

REPLIES = {
    "billing": "I hear you about the bill. I checked the last charge and started a review. Anything else on this?",
    "technical": "Got it, a technical issue. Please restart the app and tell me the error text you see.",
    "general": "Thanks for calling. Could you tell me a bit more so I route you right?",
}

_WORD_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ]+")


class CallResult(BaseModel):
    intent: str
    confidence: float
    reply: str
    tts_estimate_sec: float


def classify(transcript: str) -> tuple[str, float, list[str]]:
    """Определить интент. Детерминировано."""
    words = set(_WORD_RE.findall(transcript.lower()))
    scores = {intent: sorted({kw for kw in keywords if kw in words}) for intent, keywords in INTENTS.items()}
    best = max(scores, key=lambda intent: (len(scores[intent]), intent))
    hits = len(scores[best])
    total = sum(len(hits_) for hits_ in scores.values())
    if hits == 0:
        return "general", 0.0, []
    return best, round(hits / total, 2), scores[best]


def handle_call(transcript: str, caller: str = "", chars_per_sec: float = 15.0) -> CallResult:
    """Обработать звонок: интент + ответ + оценка озвучки."""
    if not transcript or not transcript.strip():
        raise ValueError("transcript must not be empty")
    intent, confidence, _ = classify(transcript)
    name = caller.strip() or "friend"
    reply = f"{name}, {REPLIES[intent]}"
    estimate = round(len(reply) / chars_per_sec, 1) if chars_per_sec > 0 else 0.0
    return CallResult(intent=intent, confidence=confidence, reply=reply, tts_estimate_sec=estimate)
