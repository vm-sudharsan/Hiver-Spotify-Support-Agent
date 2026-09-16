"""Grounded, deterministic response drafting with a safe LLM-free fallback."""
from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Sequence

from .escalation import EscalationDecision
from .models import CaseState
from .taxonomy import ACTIONS
from .transitions import TransitionEvidence


@dataclass(frozen=True)
class ResponseDraft:
    text: str
    selected_action: str
    automation_decision: str
    evidence_references: tuple[str, ...]
    claims: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def grounded(self) -> bool:
        return not self.warnings


def draft_response(
    case: CaseState,
    selected_action: str,
    escalation: EscalationDecision,
    evidence: Sequence[TransitionEvidence] = (),
) -> ResponseDraft:
    """Draft a concise reply that executes one frozen action."""
    if selected_action not in ACTIONS:
        raise ValueError("selected_action must use the frozen action vocabulary")
    text = _escalation_text(escalation) if escalation.decision == "ESCALATE" else _action_text(selected_action)
    references = tuple(dict.fromkeys(journey_id for item in evidence for journey_id in item.journey_ids))
    claims = (f"selected_action:{selected_action}", f"automation_decision:{escalation.decision}")
    draft = ResponseDraft(text, selected_action, escalation.decision, references, claims)
    warnings = validate_response(draft)
    return ResponseDraft(draft.text, draft.selected_action, draft.automation_decision, draft.evidence_references, draft.claims, tuple(warnings))


def validate_response(draft: ResponseDraft) -> list[str]:
    """Detect unsupported guarantees or sensitive claims before a draft is shown."""
    warnings: list[str] = []
    forbidden = (
        (r"\bguarantee\w*\b|\bdefinitely\b|\bwill be fixed\b", "contains an unsupported guarantee"),
        (r"\b(refund|chargeback)\b.*\b(approved|issued|processed)\b", "claims a financial outcome"),
        (r"\bwe (fixed|resolved)\b", "claims a resolution not established by the case"),
        (r"\b(account|email|username)\s*[:=]", "exposes account data in the draft"),
    )
    for pattern, warning in forbidden:
        if re.search(pattern, draft.text, re.IGNORECASE):
            warnings.append(warning)
    if draft.selected_action not in ACTIONS:
        warnings.append("selected action is outside the frozen vocabulary")
    return warnings


def _action_text(action: str) -> str:
    templates = {
        "ASK_PLATFORM_CONTEXT": "Could you let us know which device and operating system you're using, along with your Spotify app or browser version? That will help us narrow this down.",
        "ASK_SYMPTOM_EVIDENCE": "Could you share the exact error or what happens when the issue occurs? A screenshot would also help if one is available.",
        "ASK_SCOPE_OR_ENVIRONMENT": "Does this happen on another device, browser, network, or with another artist as well? That comparison will help us narrow the cause.",
        "ASK_CATALOG_CONTEXT": "Could you send us the song or album link and tell us which country your account is set to? That will help us check the availability context.",
        "SESSION_RESET": "Please log out, restart the device, and sign back in, then let us know whether the issue changes.",
        "REINSTALL_OR_CLEAN_INSTALL": "Please try a clean reinstall using Spotify's official support steps, then let us know whether the issue remains.",
        "BROWSER_REMEDIATION": "Please try another supported browser or an incognito window, and clear the browser cache and cookies if the issue continues.",
        "NETWORK_REMEDIATION": "Could you compare the behavior on another network, such as mobile data versus Wi-Fi? That will help us narrow the connection path.",
        "PROVIDE_HELP_RESOURCE": "Please follow the relevant Spotify support steps for this issue and let us know which step you were able to try and what changed.",
        "REQUEST_SECURE_ACCOUNT_DETAILS": "Please send the requested account details through DM rather than posting them publicly so we can keep them private.",
        "MOVE_TO_DM_OR_SECURE_CHANNEL": "Could you continue with us in DM or the secure support channel? We need to keep the account-specific details private.",
        "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE": "We have enough visible context to pass this to the technical or product team for investigation. We cannot confirm a fix yet, but the troubleshooting history will help with the handoff.",
        "CONFIRM_AND_MONITOR": "Thanks for confirming. Please keep an eye on it and let us know if the issue comes back.",
    }
    return templates[action]


def _escalation_text(decision: EscalationDecision) -> str:
    if "PRIVATE_ACCOUNT_CONTEXT" in decision.reason_codes or "SECURITY_OR_ACCOUNT_ACCESS" in decision.reason_codes or "BILLING_PAYMENT_OR_REFUND" in decision.reason_codes:
        return "This needs account-specific handling, so please continue with us through DM or the secure support channel. Please do not post account, payment, or security details publicly."
    return "This needs human or specialist review because the visible troubleshooting evidence is not sufficient for safe automated handling. We will pass the case context to the appropriate support team without claiming a resolution."
