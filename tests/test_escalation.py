from src.agent.escalation import decide_escalation
from src.agent.models import CaseState, Message


def case(**kwargs):
    return CaseState(
        conversation_id="current",
        current_customer_message=Message("1", "customer", "Current message"),
        **kwargs,
    )


def test_private_account_context_always_escalates_high_risk():
    decision = decide_escalation(case(current_state="PRIVATE_ACCOUNT_CONTEXT_REQUIRED"))
    assert decision.decision == "ESCALATE"
    assert "PRIVATE_ACCOUNT_CONTEXT" in decision.reason_codes
    assert decision.risk == "high"


def test_security_and_billing_are_explicit_gates():
    decision = decide_escalation(
        case(
            intent="Account access, identity, and security",
            current_environment={"security_risk": "high"},
        )
    )
    assert decision.decision == "ESCALATE"
    assert "SECURITY_OR_ACCOUNT_ACCESS" in decision.reason_codes


def test_repeated_failure_escalates_even_with_a_confident_case():
    decision = decide_escalation(
        case(
            current_state="REPEATED_FAILURE_OR_BROADER_INCIDENT",
            intent_confidence=0.99,
            state_confidence=0.99,
            failed_actions=["SESSION_RESET", "REINSTALL_OR_CLEAN_INSTALL"],
        ),
        selected_action="ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE",
    )
    assert decision.decision == "ESCALATE"
    assert "REPEATED_FAILURE_OR_RELAPSE" in decision.reason_codes
    assert "SPECIALIST_OR_PRODUCT_INVESTIGATION" in decision.reason_codes


def test_safe_low_risk_case_can_auto_handle():
    decision = decide_escalation(
        case(
            intent="Playback reliability",
            current_state="CONTEXT_COLLECTED",
            evidence_strength="moderate",
            intent_confidence=0.8,
        ),
        selected_action="BROWSER_REMEDIATION",
    )
    assert decision.decision == "AUTO_HANDLE"
    assert decision.reason_codes == ()
    assert decision.risk == "low"


def test_insufficient_or_conflicting_evidence_escalates_when_needed():
    decision = decide_escalation(
        case(intent_confidence=0.2, evidence_strength="conflicting"),
        conflicting_evidence=True,
        safe_action_available=False,
    )
    assert decision.decision == "ESCALATE"
    assert "CONFLICTING_EVIDENCE" in decision.reason_codes
    assert "OTHER_HIGH_RISK" in decision.reason_codes
