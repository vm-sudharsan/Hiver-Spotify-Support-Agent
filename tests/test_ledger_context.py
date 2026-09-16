from src.agent.ledger import extract_attempted_actions
from src.agent.models import Message


def test_future_support_action_is_not_extracted_when_context_is_cut():
    messages = (
        Message("1", "customer", "Chrome web player skips"),
        Message("2", "support", "What browser are you using?"),
        Message("3", "customer", "Chrome on Linux"),
        Message("4", "support", "Our technical team is investigating"),
    )
    ledger = extract_attempted_actions(messages[:3])
    assert all(item.source_message_id != "4" for item in ledger)
    assert all(item.action != "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE" for item in ledger)
