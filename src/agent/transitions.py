"""Heuristic historical state-to-action transition evidence."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

from .ledger import extract_attempted_actions
from .models import CanonicalConversation, RetrievedJourney
from .state import detect_state
from .taxonomy import ACTION_RESULTS, EVIDENCE_STRENGTHS, STATES


@dataclass(frozen=True)
class TransitionEvidence:
    state: str
    action: str
    support_count: int
    successful_count: int
    failed_count: int
    journey_ids: tuple[str, ...]
    evidence_strength: str

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError("transition state must use the frozen state vocabulary")
        if self.support_count < 1:
            raise ValueError("transition evidence needs at least one supporting observation")
        if self.evidence_strength not in EVIDENCE_STRENGTHS:
            raise ValueError("transition evidence strength is invalid")


def aggregate_transition_evidence(
    journeys: Mapping[str, CanonicalConversation],
    retrieved: Sequence[RetrievedJourney],
    *,
    target_state: str | None = None,
) -> tuple[TransitionEvidence, ...]:
    """Aggregate observed action transitions from retrieved full journeys.

    The extraction is deliberately conservative: customer result wording is kept as
    observed ledger evidence and is never upgraded to a confirmed resolution.
    """
    observations: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for hit in retrieved:
        conversation = journeys.get(hit.journey_id)
        if conversation is None:
            continue
        ledger = extract_attempted_actions(conversation.messages)
        for item in ledger:
            source_index = next(
                (index for index, message in enumerate(conversation.messages) if message.message_id == item.source_message_id),
                None,
            )
            if source_index is None:
                continue
            customer_indices = [
                index for index, message in enumerate(conversation.messages[:source_index])
                if message.role == "customer"
            ]
            if not customer_indices:
                continue
            context = conversation.messages[: customer_indices[-1] + 1]
            state = detect_state(context).state
            if target_state is not None and state != target_state:
                continue
            observations[(state, item.action)].append((hit.journey_id, item.result))

    evidence: list[TransitionEvidence] = []
    for (state, action), values in observations.items():
        journey_ids = tuple(dict.fromkeys(journey_id for journey_id, _ in values))
        successful = sum(result in {"improved", "resolved"} for _, result in values)
        failed = sum(result == "failed" for _, result in values)
        evidence.append(
            TransitionEvidence(
                state=state,
                action=action,
                support_count=len(values),
                successful_count=successful,
                failed_count=failed,
                journey_ids=journey_ids,
                evidence_strength=_strength(len(values), successful, failed),
            )
        )
    return tuple(sorted(evidence, key=lambda item: (-item.support_count, item.state, item.action)))


def _strength(support_count: int, successful_count: int, failed_count: int) -> str:
    if support_count >= 3 and not (successful_count and failed_count):
        return "strong"
    if support_count >= 2:
        return "moderate"
    if support_count == 1:
        return "weak"
    return "insufficient"
