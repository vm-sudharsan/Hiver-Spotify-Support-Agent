from src.evaluation.metrics import operational_metrics


def trace(selected="ASK_PLATFORM_CONTEXT", rejected=None, retrieved=True, evidence=True, warnings=None):
    return {
        "candidate_actions": {"selected": selected, "rejected": rejected or {}},
        "retrieved_journeys": [{"journey_id": "dev-1"}] if retrieved else [],
        "historical_evidence": [{"action": selected, "support_count": 2}] if evidence else [],
        "response": {"warnings": warnings or []},
    }


def test_operational_metrics_measure_trace_properties():
    result = operational_metrics([trace(rejected={"ASK_PLATFORM_CONTEXT": "failed"}), trace()])
    assert result["repeated_failed_action_rate"]["value"] == 0.5
    assert result["evidence_coverage"]["value"] == 1.0
    assert result["transition_consistency"]["value"] == 1.0
    assert result["response_groundedness"]["value"] == 1.0


def test_operational_metrics_expose_grounding_warning_and_empty_status():
    result = operational_metrics([trace(warnings=["unsafe claim"], retrieved=False, evidence=False)])
    assert result["evidence_coverage"]["value"] == 0.0
    assert result["response_groundedness"]["value"] == 0.0
    assert operational_metrics([])["response_groundedness"]["status"] == "NOT YET MEASURED"
