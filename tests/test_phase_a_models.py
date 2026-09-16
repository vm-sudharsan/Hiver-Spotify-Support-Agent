from src.agent.models import (
    AttemptedAction,
    CaseState,
    Message,
    MissingInformationItem,
    RetrievedJourney,
)
from src.agent.normalization import context_through_message, conversation_from_journey
from src.agent.taxonomy import ACTIONS, INTENTS, STATES


def test_frozen_vocabularies_have_expected_sizes():
    assert len(INTENTS) == 10
    assert len(STATES) == 9
    assert len(ACTIONS) == 13
    assert "DIAGNOSTIC_CONTEXT_NEEDED" not in STATES


def test_journey_normalization_preserves_source_text_and_roles():
    record = {
        "journey_id": "journey-1",
        "reconstruction_status": "complete",
        "messages": [
            {"tweet_id": "1", "role": "customer", "text": "  Exact text  ", "created_at": "t1"},
            {"tweet_id": "2", "role": "support", "text": "Reply", "created_at": "t2"},
        ],
    }
    conversation = conversation_from_journey(record)
    assert conversation.messages[0].text == "  Exact text  "
    assert conversation.customer_message_ids == ("1",)
    assert conversation.support_message_ids == ("2",)


def test_future_messages_are_excluded_from_current_context():
    record = {
        "journey_id": "journey-1",
        "reconstruction_status": "complete",
        "messages": [
            {"tweet_id": "1", "role": "customer", "text": "Initial"},
            {"tweet_id": "2", "role": "support", "text": "Future advice"},
            {"tweet_id": "3", "role": "customer", "text": "Current"},
            {"tweet_id": "4", "role": "support", "text": "Later outcome"},
        ],
    }
    context = context_through_message(conversation_from_journey(record), "3")
    assert [message.message_id for message in context] == ["1", "2", "3"]
    assert all("Later outcome" not in message.text for message in context)


def test_case_state_rejects_failed_action_outside_frozen_actions():
    state = CaseState(
        conversation_id="journey-1",
        current_customer_message=Message("3", "customer", "Still broken"),
        intent=INTENTS[0],
        current_state=STATES[4],
        failed_actions=[ACTIONS[4]],
    )
    state.validate()
    state.failed_actions.append("invented_action")
    try:
        state.validate()
    except ValueError as exc:
        assert "frozen vocabulary" in str(exc)
    else:
        raise AssertionError("invalid action ledger entry was accepted")


def test_structured_items_round_trip_as_valid_contracts():
    missing = MissingInformationItem("PLATFORM_CONTEXT", "missing", candidate_actions=(ACTIONS[0],))
    attempted = AttemptedAction(ACTIONS[4], 1, source_message_id="2", result="failed")
    retrieved = RetrievedJourney("dev-1", 1, 0.8)
    state = CaseState(
        conversation_id="journey-1",
        current_customer_message=Message("3", "customer", "Still broken"),
        missing_information=[missing],
        attempted_actions=[attempted],
        retrieved_journeys=[retrieved],
    )
    output = state.to_dict()
    assert output["missing_information"][0]["requirement"] == "PLATFORM_CONTEXT"
    assert output["attempted_actions"][0]["result"] == "failed"
    assert output["retrieved_journeys"][0]["split_membership"] == "development"
