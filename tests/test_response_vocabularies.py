import pytest

from src.agent.escalation import EscalationDecision
from src.agent.models import CaseState, Message
from src.agent.response import draft_response


def test_response_rejects_invented_action():
    case = CaseState("current", Message("1", "customer", "Issue"))
    with pytest.raises(ValueError, match="frozen action"):
        draft_response(case, "INVENTED_ACTION", EscalationDecision("AUTO_HANDLE", (), "safe", "low"))
