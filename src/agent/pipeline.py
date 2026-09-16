"""Traceable deterministic SpotifyCares support-agent pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .action_policy import ActionDecision, select_next_action
from .escalation import EscalationDecision, decide_escalation
from .intent import IntentPrediction, classify_intent
from .ledger import extract_attempted_actions, failed_actions
from .models import CaseState, MissingInformationItem
from .normalization import context_through_message, conversation_from_journey
from .response import ResponseDraft, draft_response
from .retrieval import DevelopmentJourneyRetriever, build_query
from .state import StatePrediction, detect_state
from .transitions import TransitionEvidence, aggregate_transition_evidence


_REQUIREMENT_ACTIONS = {
    "PLATFORM_CONTEXT": ("ASK_PLATFORM_CONTEXT",),
    "SYMPTOM_EVIDENCE": ("ASK_SYMPTOM_EVIDENCE",),
    "SCOPE_OR_ENVIRONMENT": ("ASK_SCOPE_OR_ENVIRONMENT",),
    "CATALOG_CONTEXT": ("ASK_CATALOG_CONTEXT",),
    "SECURE_ACCOUNT_CONTEXT": ("REQUEST_SECURE_ACCOUNT_DETAILS", "MOVE_TO_DM_OR_SECURE_CHANNEL"),
    "PRIOR_ATTEMPTS_AND_TIMING": ("ASK_SYMPTOM_EVIDENCE",),
}


@dataclass(frozen=True)
class AgentResult:
    conversation_id: str
    evaluation_point_message_id: str
    intent: IntentPrediction
    state: StatePrediction
    attempted_actions: tuple[Any, ...]
    retrieved_journeys: tuple[Any, ...]
    transition_evidence: tuple[TransitionEvidence, ...]
    action: ActionDecision
    escalation: EscalationDecision
    response: ResponseDraft

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_agent(
    record: dict[str, Any],
    retriever: DevelopmentJourneyRetriever,
    *,
    evaluation_point_id: str | None = None,
    top_k: int = 5,
) -> AgentResult:
    """Run the complete deterministic pipeline on one prepared journey."""
    conversation = conversation_from_journey(record)
    point = evaluation_point_id or conversation.customer_message_ids[-1]
    context = context_through_message(conversation, point)
    intent = classify_intent(context)
    state = detect_state(context)
    attempted = extract_attempted_actions(context)
    missing = [
        MissingInformationItem(
            requirement=requirement,
            status="missing",
            why_needed="Diagnostic context is not visible before the evaluation point.",
            candidate_actions=_REQUIREMENT_ACTIONS[requirement],
        )
        for requirement in state.missing_information
    ]
    current_customer = context[-1]
    case = CaseState(
        conversation_id=conversation.conversation_id,
        current_customer_message=current_customer,
        intent=intent.intent,
        intent_confidence=intent.confidence,
        current_state=state.state,
        state_confidence=state.confidence,
        missing_information=missing,
        attempted_actions=list(attempted),
        failed_actions=list(failed_actions(attempted)),
        successful_actions=[item.action for item in attempted if item.result in {"improved", "resolved"}],
    )
    hits = tuple(retriever.search(build_query(case, context), top_k=top_k, exclude_journey_ids={conversation.conversation_id}))
    historical = {hit.journey_id: retriever.conversation(hit.journey_id) for hit in hits}
    transitions = aggregate_transition_evidence(historical, hits, target_state=state.state)
    action = select_next_action(case, transitions)
    escalation = decide_escalation(case, selected_action=action.selected_action, safe_action_available=bool(action.selected_action))
    response = draft_response(case, action.selected_action, escalation, transitions)
    return AgentResult(
        conversation_id=conversation.conversation_id,
        evaluation_point_message_id=point,
        intent=intent,
        state=state,
        attempted_actions=attempted,
        retrieved_journeys=hits,
        transition_evidence=transitions,
        action=action,
        escalation=escalation,
        response=response,
    )
