import pytest

from src.agent.baselines import BaselineDataError, MajorityBaseline, SimpleBaseline
from src.agent.models import CanonicalConversation, Message


def labelled(journey_id, intent, action, escalation):
    return {
        "journey_id": journey_id,
        "intent": intent,
        "primary_observed_next_action": action,
        "escalation_eligible": escalation,
    }


def test_majority_baseline_uses_only_available_development_labels():
    baseline = MajorityBaseline.fit(
        [
            labelled("one", "Playback reliability", "ASK_PLATFORM_CONTEXT", "no"),
            labelled("two", "Playback reliability", "ASK_PLATFORM_CONTEXT", "no"),
            labelled("three", "Billing, payment, refund, and card issues", "MOVE_TO_DM_OR_SECURE_CHANNEL", "yes"),
        ]
    )
    prediction = baseline.predict()
    assert prediction.intent == "Playback reliability"
    assert prediction.action == "ASK_PLATFORM_CONTEXT"
    assert prediction.escalation == "AUTO_HANDLE"


def test_majority_baseline_rejects_golden_overlap():
    with pytest.raises(BaselineDataError, match="golden"):
        MajorityBaseline.fit(
            [labelled("golden", "Playback reliability", "ASK_PLATFORM_CONTEXT", "no")],
            golden_journey_ids={"golden"},
        )


def test_majority_baseline_does_not_invent_missing_labels():
    with pytest.raises(BaselineDataError, match="no complete human-labelled"):
        MajorityBaseline.fit([{"journey_id": "one"}])


def test_simple_baseline_runs_without_retrieval():
    conversation = CanonicalConversation(
        "current",
        (
            Message("1", "customer", "My Chrome web player skips songs"),
            Message("2", "support", "What browser are you using?"),
            Message("3", "customer", "Still skips"),
        ),
    )
    prediction = SimpleBaseline().predict(conversation, evaluation_point_id="3")
    assert prediction.intent == "Playback reliability"
    assert prediction.state
    assert prediction.action
    assert prediction.escalation in {"AUTO_HANDLE", "ESCALATE"}
