"""Explainable lexical intent classification over the frozen Spotify taxonomy."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .models import Message
from .taxonomy import INTENTS


@dataclass(frozen=True)
class IntentPrediction:
    intent: str | None
    confidence: float
    alternatives: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()


_RULES: dict[str, tuple[tuple[str, float], ...]] = {
    INTENTS[0]: (("playback", 3), ("skip", 3), ("skips", 3), ("skipping", 3), ("stutter", 3), ("pause", 2), ("buffer", 2), ("won't play", 3), ("not playing", 3)),
    INTENTS[1]: (("app", 2), ("browser", 2), ("crash", 3), ("battery", 3), ("ios", 2), ("android", 2), ("device", 1), ("platform", 2)),
    INTENTS[2]: (("artist", 2), ("album", 2), ("song", 2), ("track", 2), ("unavailable", 3), ("greyed", 3), ("catalog", 3), ("removed", 2)),
    INTENTS[3]: (("playlist", 3), ("library", 3), ("shuffle", 2), ("repeat", 2), ("organize", 2), ("local file", 2), ("save", 1)),
    INTENTS[4]: (("premium", 3), ("subscription", 3), ("trial", 2), ("upgrade", 2), ("plan status", 3)),
    INTENTS[5]: (("charged", 3), ("charge", 2), ("payment", 3), ("card", 3), ("refund", 3), ("billing", 3)),
    INTENTS[6]: (("log in", 3), ("login", 3), ("sign in", 3), ("password", 3), ("hacked", 4), ("account access", 4), ("changed my email", 4)),
    INTENTS[7]: (("family", 3), ("student", 3), ("verification", 2), ("invite", 2), ("eligibility", 3)),
    INTENTS[8]: (("download", 3), ("offline", 3), ("downloaded", 3)),
    INTENTS[9]: (("ad", 2), ("ads", 3), ("advert", 3), ("commercial", 3), ("free tier", 3)),
}


def _matches(text: str, phrase: str) -> bool:
    if " " in phrase:
        return phrase in text
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def classify_intent(messages: tuple[Message, ...] | list[Message]) -> IntentPrediction:
    """Classify using visible context; callers must pass no future messages."""
    visible = list(messages)
    if not visible:
        return IntentPrediction(None, 0.0)
    scores = {intent: 0.0 for intent in INTENTS}
    evidence: dict[str, list[str]] = {intent: [] for intent in INTENTS}
    for index, message in enumerate(visible):
        weight = 2.0 if message.role == "customer" and index == len(visible) - 1 else 1.0
        text = message.text.casefold()
        for intent, rules in _RULES.items():
            for phrase, value in rules:
                if _matches(text, phrase):
                    scores[intent] += value * weight
                    evidence[intent].append(phrase)
    ranked = sorted(scores, key=lambda intent: (-scores[intent], intent))
    if not ranked or scores[ranked[0]] == 0:
        return IntentPrediction(None, 0.0)
    top, second = scores[ranked[0]], scores[ranked[1]]
    confidence = min(0.99, top / (top + second + 1.0))
    return IntentPrediction(
        intent=ranked[0],
        confidence=round(confidence, 4),
        alternatives=tuple(intent for intent in ranked[1:3] if scores[intent] > 0),
        evidence=tuple(dict.fromkeys(evidence[ranked[0]])),
    )
