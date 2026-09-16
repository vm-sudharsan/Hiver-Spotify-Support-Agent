from src.agent.intent import classify_intent
from src.agent.models import Message
from src.agent.state import detect_state


def msg(message_id, role, text):
    return Message(message_id, role, text)


def test_intent_uses_frozen_label_and_returns_evidence():
    prediction = classify_intent((msg("1", "customer", "My Chrome web player keeps skipping songs"),))
    assert prediction.intent == "Playback reliability"
    assert prediction.confidence > 0
    assert any(term in prediction.evidence for term in ("skip", "skipping"))


def test_intent_does_not_invent_other_label():
    prediction = classify_intent((msg("1", "customer", "Hello Spotify"),))
    assert prediction.intent is None
    assert prediction.confidence == 0


def test_state_tracks_repeated_failure_and_attempt_history():
    messages = (
        msg("1", "customer", "Songs are unavailable on my iPhone"),
        msg("2", "support", "Please reinstall the app"),
        msg("3", "customer", "Still no luck, reinstall did not help"),
        msg("4", "support", "Try restarting and logging in again"),
        msg("5", "customer", "Nothing changed"),
    )
    prediction = detect_state(messages)
    assert prediction.state == "REPEATED_FAILURE_OR_BROADER_INCIDENT"
    assert "failed" in prediction.reason


def test_future_specialist_reply_cannot_contaminate_current_state():
    messages_through_point = (
        msg("1", "customer", "The web player skips songs"),
        msg("2", "support", "What browser are you using?"),
        msg("3", "customer", "Chrome on Linux"),
    )
    future_messages = messages_through_point + (
        msg("4", "support", "Our developers are investigating this"),
    )
    assert detect_state(messages_through_point).state == "CONTEXT_COLLECTED"
    assert detect_state(future_messages[:-1]).state == "CONTEXT_COLLECTED"
