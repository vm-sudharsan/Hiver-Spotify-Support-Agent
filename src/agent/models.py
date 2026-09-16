"""Structured contracts shared by the SpotifyCares agent stages."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .taxonomy import (
    ACTIONS,
    ACTION_RESULTS,
    EVIDENCE_STRENGTHS,
    EXPLICITNESS,
    INTENTS,
    REQUIREMENTS,
    REQUIREMENT_STATUSES,
    RECONSTRUCTION_STATUSES,
    STATES,
    require,
)


@dataclass(frozen=True)
class Message:
    message_id: str
    role: str
    text: str
    timestamp: str = ""
    source_reference: str = ""

    def __post_init__(self) -> None:
        if not self.message_id or self.role not in {"customer", "support"}:
            raise ValueError("message_id and role must describe a customer or support message")


@dataclass(frozen=True)
class CanonicalConversation:
    conversation_id: str
    messages: tuple[Message, ...]
    source_dataset: str = "spotify_journeys"
    reconstruction_status: str = "complete"

    def __post_init__(self) -> None:
        require(self.reconstruction_status, RECONSTRUCTION_STATUSES, "reconstruction_status")
        if not self.conversation_id or not self.messages:
            raise ValueError("conversation_id and messages are required")

    @property
    def customer_message_ids(self) -> tuple[str, ...]:
        return tuple(message.message_id for message in self.messages if message.role == "customer")

    @property
    def support_message_ids(self) -> tuple[str, ...]:
        return tuple(message.message_id for message in self.messages if message.role == "support")


@dataclass(frozen=True)
class MissingInformationItem:
    requirement: str
    status: str
    why_needed: str = ""
    safely_requestable: str = "unknown"
    candidate_actions: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require(self.requirement, REQUIREMENTS, "requirement")
        require(self.status, REQUIREMENT_STATUSES, "status")
        if self.safely_requestable not in {"yes", "no", "unknown"}:
            raise ValueError("safely_requestable must be yes, no, or unknown")
        if any(action not in ACTIONS for action in self.candidate_actions):
            raise ValueError("candidate_actions must use the frozen action vocabulary")


@dataclass(frozen=True)
class AttemptedAction:
    action: str
    order: int
    source_message_id: str = ""
    explicitness: str = "ambiguous"
    result: str = "unknown"
    result_evidence: str = ""
    equivalence_group: str = ""

    def __post_init__(self) -> None:
        require(self.action, ACTIONS, "action")
        require(self.explicitness, EXPLICITNESS, "explicitness")
        require(self.result, ACTION_RESULTS, "result")
        if self.order < 1:
            raise ValueError("attempted action order must start at 1")


@dataclass(frozen=True)
class RetrievedJourney:
    journey_id: str
    rank: int
    retrieval_score: float
    split_membership: str = "development"
    evidence_strength: str = "insufficient"
    source_message_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.rank < 1 or not self.journey_id:
            raise ValueError("retrieved journeys need a positive rank and journey ID")
        require(self.evidence_strength, EVIDENCE_STRENGTHS, "evidence_strength")
        if self.split_membership == "golden":
            raise ValueError("golden journeys cannot enter the retrieval result")


@dataclass
class CaseState:
    conversation_id: str
    current_customer_message: Message
    intent: str | None = None
    intent_confidence: float | None = None
    current_state: str | None = None
    state_confidence: float | None = None
    missing_information: list[MissingInformationItem] = field(default_factory=list)
    attempted_actions: list[AttemptedAction] = field(default_factory=list)
    failed_actions: list[str] = field(default_factory=list)
    successful_actions: list[str] = field(default_factory=list)
    current_environment: dict[str, str] = field(default_factory=dict)
    evidence_strength: str = "insufficient"
    escalation_risk: str = "low"
    retrieved_journeys: list[RetrievedJourney] = field(default_factory=list)
    selected_next_action: str | None = None
    action_reason: str = ""
    automation_decision: str | None = None

    def validate(self) -> None:
        if self.current_customer_message.role != "customer":
            raise ValueError("current_customer_message must be a customer message")
        if self.intent is not None:
            require(self.intent, INTENTS, "intent")
        if self.current_state is not None:
            require(self.current_state, STATES, "current_state")
        if self.selected_next_action is not None:
            require(self.selected_next_action, ACTIONS, "selected_next_action")
        require(self.evidence_strength, EVIDENCE_STRENGTHS, "evidence_strength")
        if self.escalation_risk not in {"low", "medium", "high"}:
            raise ValueError("escalation_risk must be low, medium, or high")
        if self.automation_decision not in {None, "AUTO_HANDLE", "ESCALATE"}:
            raise ValueError("automation_decision must be AUTO_HANDLE or ESCALATE")
        for score in (self.intent_confidence, self.state_confidence):
            if score is not None and not 0 <= score <= 1:
                raise ValueError("confidence scores must be between 0 and 1")
        for action in self.failed_actions + self.successful_actions:
            require(action, ACTIONS, "action ledger entry")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
