"""Deterministic automation and escalation policy."""
from __future__ import annotations

from dataclasses import dataclass

from .models import CaseState
from .taxonomy import INTENTS, STATES

REASON_CODES = (
    "PRIVATE_ACCOUNT_CONTEXT",
    "SECURITY_OR_ACCOUNT_ACCESS",
    "BILLING_PAYMENT_OR_REFUND",
    "REPEATED_FAILURE_OR_RELAPSE",
    "BROADER_INCIDENT",
    "SPECIALIST_OR_PRODUCT_INVESTIGATION",
    "INSUFFICIENT_EVIDENCE",
    "CONFLICTING_EVIDENCE",
    "HISTORICAL_POLICY_OR_CATALOG_LIMITATION",
    "OTHER_HIGH_RISK",
)


@dataclass(frozen=True)
class EscalationDecision:
    decision: str
    reason_codes: tuple[str, ...]
    reason: str
    risk: str

    def __post_init__(self) -> None:
        if self.decision not in {"AUTO_HANDLE", "ESCALATE"}:
            raise ValueError("decision must be AUTO_HANDLE or ESCALATE")
        if self.risk not in {"low", "medium", "high"}:
            raise ValueError("risk must be low, medium, or high")
        if any(code not in REASON_CODES for code in self.reason_codes):
            raise ValueError("reason codes must use the frozen escalation vocabulary")


def decide_escalation(
    case: CaseState,
    *,
    selected_action: str | None = None,
    safe_action_available: bool = True,
    conflicting_evidence: bool = False,
) -> EscalationDecision:
    """Apply hard escalation gates before any customer-facing response is drafted."""
    codes: list[str] = []
    action = selected_action or case.selected_next_action
    if case.current_state == STATES[5]:
        codes.append("PRIVATE_ACCOUNT_CONTEXT")
    if case.intent == INTENTS[6] or case.current_environment.get("security_risk") == "high":
        codes.append("SECURITY_OR_ACCOUNT_ACCESS")
    if case.intent == INTENTS[5] or case.current_environment.get("payment_risk") == "high":
        codes.append("BILLING_PAYMENT_OR_REFUND")
    if case.current_state == STATES[4] or len(set(case.failed_actions)) >= 2:
        codes.append("REPEATED_FAILURE_OR_RELAPSE")
    if case.current_state == STATES[6]:
        codes.append("SPECIALIST_OR_PRODUCT_INVESTIGATION")
    if action == "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE":
        codes.append("SPECIALIST_OR_PRODUCT_INVESTIGATION")
    if case.current_environment.get("broader_incident") == "yes":
        codes.append("BROADER_INCIDENT")
    if conflicting_evidence or case.evidence_strength == "conflicting":
        codes.append("CONFLICTING_EVIDENCE")
    if case.evidence_strength == "insufficient" and (case.intent_confidence is not None and case.intent_confidence < 0.5 or action is None):
        codes.append("INSUFFICIENT_EVIDENCE")
    if not safe_action_available:
        codes.append("OTHER_HIGH_RISK")

    unique_codes = tuple(dict.fromkeys(codes))
    risk = _risk(unique_codes)
    decision = "ESCALATE" if unique_codes else "AUTO_HANDLE"
    if unique_codes:
        reason = "Escalate because " + "; ".join(_explain(code) for code in unique_codes) + "."
    else:
        reason = "Auto-handle: no deterministic escalation gate was triggered."
    return EscalationDecision(decision, unique_codes, reason, risk)


def _risk(codes: tuple[str, ...]) -> str:
    if any(code in codes for code in {"PRIVATE_ACCOUNT_CONTEXT", "SECURITY_OR_ACCOUNT_ACCESS", "BILLING_PAYMENT_OR_REFUND", "OTHER_HIGH_RISK"}):
        return "high"
    if codes:
        return "medium"
    return "low"


def _explain(code: str) -> str:
    explanations = {
        "PRIVATE_ACCOUNT_CONTEXT": "private account context is required",
        "SECURITY_OR_ACCOUNT_ACCESS": "account or security handling is high risk",
        "BILLING_PAYMENT_OR_REFUND": "billing or payment handling is high risk",
        "REPEATED_FAILURE_OR_RELAPSE": "prior troubleshooting has repeatedly failed",
        "BROADER_INCIDENT": "the evidence suggests a broader incident",
        "SPECIALIST_OR_PRODUCT_INVESTIGATION": "specialist or product investigation is required",
        "INSUFFICIENT_EVIDENCE": "there is insufficient evidence for safe automation",
        "CONFLICTING_EVIDENCE": "available evidence conflicts",
        "HISTORICAL_POLICY_OR_CATALOG_LIMITATION": "historical evidence cannot establish current policy or catalog truth",
        "OTHER_HIGH_RISK": "no safe automated action is available",
    }
    return explanations[code]
