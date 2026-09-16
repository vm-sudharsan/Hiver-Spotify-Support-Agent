"""Deterministic troubleshooting-state detection from visible conversation context."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .models import AttemptedAction, Message
from .taxonomy import REQUIREMENTS, STATES


@dataclass(frozen=True)
class StatePrediction:
    state: str
    confidence: float
    missing_information: tuple[str, ...] = ()
    reason: str = ""


def _has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def detect_state(
    messages: tuple[Message, ...] | list[Message],
    *,
    attempted_actions: tuple[AttemptedAction, ...] | list[AttemptedAction] = (),
) -> StatePrediction:
    """Detect the current state using only the supplied chronological context."""
    visible = list(messages)
    if not visible or visible[-1].role != "customer":
        raise ValueError("state detection requires context ending at a customer message")
    current = visible[-1].text
    customer_text = " ".join(message.text for message in visible if message.role == "customer")
    support_text = " ".join(message.text for message in visible if message.role == "support")
    all_text = f"{customer_text} {support_text}"
    failed_count = sum(
        _has(message.text, r"\b(no luck|didn['’]?t help|nothing changed|still (?:doesn['’]?t|not|no)|won['’]?t work|doesn['’]?t work|neither worked)\b")
        for message in visible
        if message.role == "customer"
    )
    failed_count += sum(action.result == "failed" for action in attempted_actions)

    if _has(support_text, r"developer|technical team|tech team|investigat|passed .* feedback"):
        return StatePrediction(STATES[6], 0.96, reason="support context indicates specialist or product investigation")
    if _has(support_text, r"\b(dm|direct message|private|secure)\b") and _has(support_text, r"username|email|account"):
        return StatePrediction(STATES[5], 0.96, ("SECURE_ACCOUNT_CONTEXT",), "support requests private account context")
    if _has(current, r"\b(hacked|password|account access|can['’]?t log ?in|cannot log ?in)\b"):
        return StatePrediction(STATES[5], 0.82, ("SECURE_ACCOUNT_CONTEXT",), "current message indicates account-access or security risk")
    if _has(current, r"\b(fixed|resolved|working now|works now|it works|solved)\b"):
        return StatePrediction(STATES[7], 0.94, reason="customer explicitly reports resolution")
    if _has(current, r"\b(seems to have worked|working so far|monitor|if it happens again|improved)\b"):
        return StatePrediction(STATES[8], 0.9, reason="customer reports improvement without definitive closure")
    if failed_count >= 2:
        return StatePrediction(STATES[4], 0.93, reason="multiple failed attempts are visible in the conversation")
    if failed_count == 1 and attempted_actions:
        return StatePrediction(STATES[3], 0.86, reason="customer reports a result after a recorded attempted action")
    if failed_count == 1 or _has(current, r"\b(worked|helped|better|still|again)\b"):
        return StatePrediction(STATES[3], 0.76, reason="customer message reports an action result or recurrence")
    if _has(support_text, r"\b(try|restart|reinstall|clear cache|log out|log in|another browser|another device|help link)\b"):
        return StatePrediction(STATES[2], 0.74, reason="preceding support context proposes a first-line action")

    missing = _missing_requirements(customer_text)
    if missing:
        return StatePrediction(STATES[0], 0.72, tuple(missing), "symptom is present but diagnostic context remains incomplete")
    if _has(all_text, r"device|operating system|\bios\b|android|browser|version|screenshot|error|wifi|network|country|song link|uri"):
        return StatePrediction(STATES[1], 0.7, reason="relevant diagnostic context is visible")
    return StatePrediction(STATES[0], 0.55, reason="only a customer symptom is visible")


def _missing_requirements(customer_text: str) -> list[str]:
    missing: list[str] = []
    if not _has(customer_text, r"device|phone|computer|desktop|iphone|android|browser|chrome|linux|windows|mac"):
        missing.append(REQUIREMENTS[0])
    if not _has(customer_text, r"error|screenshot|crash|skip|pause|stutter|greyed|unavailable|not working|won['’]?t work"):
        missing.append(REQUIREMENTS[1])
    return missing
