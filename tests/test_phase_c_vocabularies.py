import pytest

from src.agent.intent import classify_intent
from src.agent.models import Message
from src.agent.state import detect_state


def test_state_requires_customer_evaluation_point():
    with pytest.raises(ValueError, match="customer message"):
        detect_state((Message("1", "support", "Try reinstalling"),))


def test_intent_considers_preceding_context_but_current_customer_has_more_weight():
    messages = (
        Message("1", "customer", "My account is hacked"),
        Message("2", "support", "Please tell us your device"),
        Message("3", "customer", "I am charged twice on my card"),
    )
    assert classify_intent(messages).intent == "Billing, payment, refund, and card issues"
