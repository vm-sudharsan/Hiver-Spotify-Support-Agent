from src.agent.action_policy import select_next_action
from src.agent.models import AttemptedAction, CaseState, Message, MissingInformationItem
from src.agent.transitions import TransitionEvidence


def test_policy_prefers_missing_information_action_for_symptom():
    case = CaseState(
        conversation_id="current",
        current_customer_message=Message("1", "customer", "My songs keep skipping"),
        intent="Playback reliability",
        current_state="SYMPTOM_REPORTED",
        missing_information=[MissingInformationItem("PLATFORM_CONTEXT", "missing", candidate_actions=("ASK_PLATFORM_CONTEXT",))],
    )
    decision = select_next_action(case)
    assert decision.selected_action == "ASK_PLATFORM_CONTEXT"
    assert decision.component_scores["missing_information_fit"] == 3.0


def test_policy_does_not_repeat_failed_action():
    case = CaseState(
        conversation_id="current",
        current_customer_message=Message("1", "customer", "Still broken"),
        current_state="REPEATED_FAILURE_OR_BROADER_INCIDENT",
        attempted_actions=[AttemptedAction("REINSTALL_OR_CLEAN_INSTALL", 1, result="failed")],
    )
    decision = select_next_action(case, candidates=("REINSTALL_OR_CLEAN_INSTALL", "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE"))
    assert decision.selected_action == "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE"
    assert "REINSTALL_OR_CLEAN_INSTALL" in decision.rejected_actions


def test_policy_uses_transition_evidence_as_inspectable_score():
    case = CaseState(
        conversation_id="current",
        current_customer_message=Message("1", "customer", "The artist is unavailable"),
        intent="Content or catalog availability",
        current_state="CONTEXT_COLLECTED",
    )
    evidence = (TransitionEvidence("CONTEXT_COLLECTED", "ASK_CATALOG_CONTEXT", 4, 0, 0, ("dev-1",), "strong"),)
    decision = select_next_action(case, evidence)
    assert decision.selected_action == "ASK_CATALOG_CONTEXT"
    assert decision.component_scores["transition_support"] == 2.0
    assert decision.evidence[0].journey_ids == ("dev-1",)
