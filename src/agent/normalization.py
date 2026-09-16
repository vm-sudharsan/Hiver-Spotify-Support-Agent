"""Deterministic conversion from prepared journey records to agent contracts."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import CanonicalConversation, Message
from .taxonomy import RECONSTRUCTION_STATUSES, require


def conversation_from_journey(record: Mapping[str, Any]) -> CanonicalConversation:
    journey_id = str(record.get("journey_id") or "")
    messages = tuple(
        Message(
            message_id=str(item.get("tweet_id") or ""),
            role=str(item.get("role") or ""),
            text=str(item.get("text") or ""),
            timestamp=str(item.get("created_at") or ""),
            source_reference=f"journey:{journey_id}/message:{item.get('tweet_id', '')}",
        )
        for item in record.get("messages", [])
    )
    status = str(record.get("reconstruction_status") or "uncertain")
    require(status, RECONSTRUCTION_STATUSES, "reconstruction_status")
    return CanonicalConversation(
        conversation_id=journey_id,
        messages=messages,
        reconstruction_status=status,
    )


def context_through_message(conversation: CanonicalConversation, evaluation_point_id: str) -> tuple[Message, ...]:
    """Return context through the evaluation point, excluding all future messages."""
    for index, message in enumerate(conversation.messages):
        if message.message_id == evaluation_point_id:
            if message.role != "customer":
                raise ValueError("evaluation point must identify a customer message")
            return conversation.messages[: index + 1]
    raise ValueError("evaluation point is not in the conversation")
