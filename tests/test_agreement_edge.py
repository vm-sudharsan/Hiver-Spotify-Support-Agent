from src.evaluation.agreement import agreement_report


def test_agreement_is_not_claimed_without_shared_examples():
    result = agreement_report([{"journey_id": "one"}], [{"journey_id": "two"}])
    assert result["status"] == "NOT_READY"
    assert result["shared_count"] == 0
