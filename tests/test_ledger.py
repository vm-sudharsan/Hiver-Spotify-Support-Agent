import pytest

from src.agent.ledger import extract_attempted_actions, failed_actions, filter_actions
from src.agent.models import Message


def test_ledger_records_order_and_customer_result():
    messages = (
        Message("1", "customer", "The web player skips songs"),
        Message("2", "support", "Please try another browser or incognito"),
        Message("3", "customer", "Firefox works but Chrome still does not work"),
        Message("4", "support", "Please clear the cache and cookies"),
    )
    ledger = extract_attempted_actions(messages)
    assert ledger[0].action == "ASK_SCOPE_OR_ENVIRONMENT"
    assert ledger[0].result == "failed"
    assert ledger[0].source_message_id == "2"
    assert [item.order for item in ledger] == list(range(1, len(ledger) + 1))
    assert any(item.action == "BROWSER_REMEDIATION" for item in ledger)


def test_failed_action_protection_filters_repetition():
    messages = (
        Message("1", "support", "Please reinstall the app"),
        Message("2", "customer", "Still no luck, reinstall did not help"),
    )
    ledger = extract_attempted_actions(messages)
    result = filter_actions(("REINSTALL_OR_CLEAN_INSTALL", "SESSION_RESET"), ledger)
    assert result.eligible_actions == ("SESSION_RESET",)
    assert "REINSTALL_OR_CLEAN_INSTALL" in result.rejected_actions
    assert result.repeated_failed_action_rate == 0.5
    assert failed_actions(ledger) == ("REINSTALL_OR_CLEAN_INSTALL",)


def test_failed_action_can_be_reconsidered_with_new_evidence():
    messages = (
        Message("1", "support", "Restart the app"),
        Message("2", "customer", "Nothing changed"),
    )
    ledger = extract_attempted_actions(messages)
    result = filter_actions(("SESSION_RESET",), ledger, allow_retry=True)
    assert result.eligible_actions == ("SESSION_RESET",)
    assert result.rejected_actions == {}


def test_invalid_candidate_is_rejected_before_policy():
    with pytest.raises(ValueError, match="frozen vocabulary"):
        filter_actions(("INVENTED_ACTION",), ())
