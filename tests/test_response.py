from src.agent.escalation import EscalationDecision
from src.agent.models import CaseState, Message
from src.agent.response import draft_response, validate_response
from src.agent.transitions import TransitionEvidence


def make_case():
    return CaseState(
        conversation_id="current",
        current_customer_message=Message("1", "customer", "Chrome player skips"),
        current_state="CONTEXT_COLLECTED",
        intent="Playback reliability",
    )


def test_response_follows_selected_action_and_keeps_evidence_internal():
    escalation = EscalationDecision("AUTO_HANDLE", (), "safe", "low")
    evidence = (TransitionEvidence("CONTEXT_COLLECTED", "BROWSER_REMEDIATION", 2, 1, 0, ("dev-1",), "moderate"),)
    draft = draft_response(make_case(), "BROWSER_REMEDIATION", escalation, evidence)
    assert "browser" in draft.text.lower()
    assert draft.selected_action == "BROWSER_REMEDIATION"
    assert draft.evidence_references == ("dev-1",)
    assert draft.grounded
    assert "dev-1" not in draft.text


def test_escalated_sensitive_case_uses_secure_handoff_language():
    escalation = EscalationDecision("ESCALATE", ("SECURITY_OR_ACCOUNT_ACCESS",), "security", "high")
    draft = draft_response(make_case(), "REQUEST_SECURE_ACCOUNT_DETAILS", escalation)
    assert "DM" in draft.text
    assert "publicly" in draft.text
    assert draft.automation_decision == "ESCALATE"
    assert draft.grounded


def test_response_validator_rejects_unsupported_claims():
    draft = draft_response(make_case(), "CONFIRM_AND_MONITOR", EscalationDecision("AUTO_HANDLE", (), "safe", "low"))
    unsafe = type(draft)("We guarantee this will be fixed.", draft.selected_action, draft.automation_decision, (), ())
    warnings = validate_response(unsafe)
    assert "unsupported guarantee" in warnings[0]
