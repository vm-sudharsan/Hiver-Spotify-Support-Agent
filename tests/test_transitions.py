from src.agent.models import Message, RetrievedJourney, CanonicalConversation
from src.agent.transitions import aggregate_transition_evidence


def test_transition_aggregation_keeps_source_journey_ids():
    conversation = CanonicalConversation(
        conversation_id="dev-1",
        messages=(
            Message("1", "customer", "The song is unavailable on my iPhone"),
            Message("2", "support", "Please send the song link and country"),
            Message("3", "customer", "I am in Ireland"),
        ),
    )
    hit = RetrievedJourney("dev-1", 1, 0.8)
    evidence = aggregate_transition_evidence({"dev-1": conversation}, (hit,), target_state="SYMPTOM_REPORTED")
    assert evidence
    assert evidence[0].action == "ASK_CATALOG_CONTEXT"
    assert evidence[0].journey_ids == ("dev-1",)
    assert evidence[0].evidence_strength == "weak"
