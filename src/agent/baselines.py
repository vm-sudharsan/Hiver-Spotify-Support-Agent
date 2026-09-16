"""Trivial and simple non-LLM baselines for later evaluation."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Any

from .action_policy import select_next_action
from .escalation import decide_escalation
from .intent import classify_intent
from .ledger import extract_attempted_actions, failed_actions
from .models import CaseState, CanonicalConversation
from .normalization import context_through_message
from .state import detect_state
from .taxonomy import ACTIONS, INTENTS


class BaselineDataError(ValueError):
    """Raised when a baseline cannot be fitted without inventing labels."""


@dataclass(frozen=True)
class BaselinePrediction:
    intent: str | None
    state: str | None
    action: str | None
    escalation: str


@dataclass(frozen=True)
class MajorityBaseline:
    majority_intent: str
    majority_action: str
    majority_escalation: str

    @classmethod
    def fit(
        cls,
        records: Sequence[Mapping[str, Any]],
        *,
        golden_journey_ids: set[str] | None = None,
    ) -> "MajorityBaseline":
        golden_ids = golden_journey_ids or set()
        overlap = golden_ids.intersection(str(record.get("journey_id")) for record in records)
        if overlap:
            raise BaselineDataError("golden journeys cannot be used to fit a baseline")
        intents: list[str] = []
        actions: list[str] = []
        escalations: list[str] = []
        for record in records:
            intent = record.get("intent")
            action = record.get("primary_observed_next_action") or record.get("observed_next_action")
            escalation = record.get("escalation_eligible")
            if intent in INTENTS:
                intents.append(intent)
            if action in ACTIONS:
                actions.append(action)
            if escalation in {"yes", "no", "uncertain"}:
                escalations.append(escalation)
        if not intents or not actions or not escalations:
            raise BaselineDataError(
                "development records contain no complete human-labelled baseline fields; "
                "fit after human annotations exist rather than inventing labels"
            )
        return cls(_majority(intents), _majority(actions), _majority(escalations))

    def predict(self) -> BaselinePrediction:
        return BaselinePrediction(
            self.majority_intent,
            None,
            self.majority_action,
            "ESCALATE" if self.majority_escalation == "yes" else "AUTO_HANDLE",
        )


class SimpleBaseline:
    """A transparent lexical classifier plus deterministic rules, with no retrieval."""

    def predict(
        self,
        conversation: CanonicalConversation,
        *,
        evaluation_point_id: str | None = None,
    ) -> BaselinePrediction:
        point = evaluation_point_id or conversation.customer_message_ids[-1]
        context = context_through_message(conversation, point)
        intent = classify_intent(context)
        state = detect_state(context)
        attempted = extract_attempted_actions(context)
        case = CaseState(
            conversation_id=conversation.conversation_id,
            current_customer_message=context[-1],
            intent=intent.intent,
            intent_confidence=intent.confidence,
            current_state=state.state,
            state_confidence=state.confidence,
            attempted_actions=list(attempted),
            failed_actions=list(failed_actions(attempted)),
        )
        action = select_next_action(case)
        escalation = decide_escalation(case, selected_action=action.selected_action)
        return BaselinePrediction(intent.intent, state.state, action.selected_action, escalation.decision)


def _majority(values: Sequence[str]) -> str:
    return Counter(values).most_common(1)[0][0]
