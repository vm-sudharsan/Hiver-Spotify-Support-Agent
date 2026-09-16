from src.agent.llm import ConfiguredLLM
from src.evaluation.judge import DIMENSIONS, judge_response


def test_unconfigured_provider_is_explicitly_unavailable():
    result = judge_response(
        customer_message="Songs skip",
        draft_response="Please try another browser.",
        selected_action="BROWSER_REMEDIATION",
        escalation_decision="AUTO_HANDLE",
        evidence_summary="No direct transition evidence.",
        provider=ConfiguredLLM(endpoint="", api_key="", model=""),
    )
    assert result.status == "NOT_AVAILABLE"
    assert result.scores is None


def test_configured_provider_result_is_validated_without_network():
    class FakeProvider:
        def structured_json(self, system, user):
            return type("Result", (), {"status": "OK", "model": "fake", "error": "", "value": {"scores": {dimension: 4 for dimension in DIMENSIONS}, "rationale": "clear"}})()

    result = judge_response(
        customer_message="Songs skip",
        draft_response="Please try another browser.",
        selected_action="BROWSER_REMEDIATION",
        escalation_decision="AUTO_HANDLE",
        evidence_summary="Two historical transitions.",
        provider=FakeProvider(),
    )
    assert result.status == "MEASURED"
    assert result.scores == {dimension: 4 for dimension in DIMENSIONS}
    assert result.model == "fake"
