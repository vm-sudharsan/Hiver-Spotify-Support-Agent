"""Explainable Next Best Support Action ranking."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence

from .ledger import filter_actions
from .models import CaseState
from .taxonomy import ACTIONS, INTENTS, STATES
from .transitions import TransitionEvidence


@dataclass(frozen=True)
class ActionDecision:
    selected_action: str
    score: float
    reason: str
    evidence: tuple[TransitionEvidence, ...]
    alternatives: tuple[str, ...]
    component_scores: dict[str, float]
    rejected_actions: dict[str, str]


def select_next_action(
    case: CaseState,
    transition_evidence: Sequence[TransitionEvidence] = (),
    *,
    candidates: Iterable[str] = ACTIONS,
) -> ActionDecision:
    """Rank only frozen actions and never directly repeat a failed action."""
    candidate_tuple = tuple(candidates)
    filtered = filter_actions(candidate_tuple, case.attempted_actions)
    eligible = filtered.eligible_actions
    if not eligible:
        eligible = ("ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE",)
    evidence_by_action = {
        action: [item for item in transition_evidence if item.action == action]
        for action in eligible
    }
    scores: dict[str, dict[str, float]] = {}
    for action in eligible:
        supporting = evidence_by_action[action]
        scores[action] = {
            "transition_support": min(4.0, sum(item.support_count for item in supporting) / 2.0),
            "state_fit": _state_fit(case.current_state, action),
            "missing_information_fit": _missing_fit(case, action),
            "intent_fit": _intent_fit(case.intent, action),
            "progression_signal": _progression_fit(case.current_state, action),
        }
    totals = {action: round(sum(parts.values()), 4) for action, parts in scores.items()}
    ranked = sorted(eligible, key=lambda action: (-totals[action], ACTIONS.index(action)))
    selected = ranked[0]
    components = scores[selected]
    supporting = tuple(sorted(evidence_by_action[selected], key=lambda item: (-item.support_count, item.action)))
    reason = _reason(selected, components, supporting, filtered.rejected_actions)
    return ActionDecision(
        selected_action=selected,
        score=totals[selected],
        reason=reason,
        evidence=supporting,
        alternatives=tuple(ranked[1:4]),
        component_scores=components,
        rejected_actions=filtered.rejected_actions,
    )


def _state_fit(state: str | None, action: str) -> float:
    preferred = {
        "SYMPTOM_REPORTED": {"ASK_PLATFORM_CONTEXT", "ASK_SYMPTOM_EVIDENCE", "ASK_SCOPE_OR_ENVIRONMENT", "ASK_CATALOG_CONTEXT"},
        "CONTEXT_COLLECTED": {"SESSION_RESET", "REINSTALL_OR_CLEAN_INSTALL", "BROWSER_REMEDIATION", "NETWORK_REMEDIATION", "PROVIDE_HELP_RESOURCE"},
        "FIRST_LINE_ACTION_PROPOSED": {"CONFIRM_AND_MONITOR", "ASK_SYMPTOM_EVIDENCE"},
        "ACTION_RESULT_REPORTED": {"REINSTALL_OR_CLEAN_INSTALL", "ASK_SCOPE_OR_ENVIRONMENT", "MOVE_TO_DM_OR_SECURE_CHANNEL", "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE"},
        "REPEATED_FAILURE_OR_BROADER_INCIDENT": {"ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE", "MOVE_TO_DM_OR_SECURE_CHANNEL", "REQUEST_SECURE_ACCOUNT_DETAILS"},
        "PRIVATE_ACCOUNT_CONTEXT_REQUIRED": {"MOVE_TO_DM_OR_SECURE_CHANNEL", "REQUEST_SECURE_ACCOUNT_DETAILS"},
        "SPECIALIST_OR_PRODUCT_INVESTIGATION": {"ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE", "CONFIRM_AND_MONITOR"},
        "RESOLVED": {"CONFIRM_AND_MONITOR"},
        "MONITORING": {"CONFIRM_AND_MONITOR"},
    }
    return 5.0 if action in preferred.get(state, set()) else 0.0


def _missing_fit(case: CaseState, action: str) -> float:
    return 3.0 if any(action in item.candidate_actions and item.status in {"missing", "private", "conflicting"} for item in case.missing_information) else 0.0


def _intent_fit(intent: str | None, action: str) -> float:
    fits = {
        INTENTS[2]: {"ASK_CATALOG_CONTEXT": 3.0},
        INTENTS[5]: {"REQUEST_SECURE_ACCOUNT_DETAILS": 3.0, "MOVE_TO_DM_OR_SECURE_CHANNEL": 2.0},
        INTENTS[6]: {"REQUEST_SECURE_ACCOUNT_DETAILS": 3.0, "MOVE_TO_DM_OR_SECURE_CHANNEL": 2.0},
        INTENTS[7]: {"REQUEST_SECURE_ACCOUNT_DETAILS": 2.0, "MOVE_TO_DM_OR_SECURE_CHANNEL": 2.0},
        INTENTS[8]: {"PROVIDE_HELP_RESOURCE": 1.0},
    }
    return fits.get(intent, {}).get(action, 0.0)


def _progression_fit(state: str | None, action: str) -> float:
    if state in {STATES[4], STATES[5], STATES[6]} and action in {ACTIONS[9], ACTIONS[10], ACTIONS[11]}:
        return 2.0
    return 0.0


def _reason(action: str, components: dict[str, float], evidence: Sequence[TransitionEvidence], rejected: dict[str, str]) -> str:
    reasons = [name.replace("_", " ").lower() for name, score in components.items() if score > 0]
    evidence_text = f"{sum(item.support_count for item in evidence)} historical transition observations" if evidence else "no direct historical transition evidence"
    rejected_text = f"; avoided {', '.join(sorted(rejected))} after reported failure" if rejected else ""
    return f"Selected {action} from {', '.join(reasons) or 'the available safe actions'}; {evidence_text}{rejected_text}."
