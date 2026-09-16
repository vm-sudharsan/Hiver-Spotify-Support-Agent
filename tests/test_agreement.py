from src.evaluation.agreement import agreement_report, cohens_kappa, jaccard
from src.evaluation.qc import freeze_manifest, golden_qc_report


def record(journey_id, intent="Playback reliability", reasons=None, excluded="no"):
    return {"journey_id": journey_id, "intent": intent, "current_state": "CONTEXT_COLLECTED", "outcome": "unknown", "escalation_eligible": "no", "escalation_reason_codes": reasons or [], "exclude_from_golden": excluded}


def test_cohens_kappa_and_jaccard_are_deterministic():
    assert cohens_kappa(["a", "b", "a"], ["a", "b", "b"]) == 0.4
    assert jaccard(["A", "B"], ["B", "C"]) == 0.3333


def test_agreement_report_calculates_shared_subset_metrics():
    left = [record("one"), record("two", intent="Billing, payment, refund, and card issues", reasons=["BILLING_PAYMENT_OR_REFUND"])]
    right = [record("one"), record("two", intent="Playback reliability", reasons=["BILLING_PAYMENT_OR_REFUND"])]
    result = agreement_report(left, right)
    assert result["status"] == "MEASURED"
    assert result["shared_count"] == 2
    assert result["adjudication_rate"] == 0.5
    assert result["multilabel_jaccard"] == 1.0


def test_qc_rejects_development_overlap_and_freeze_manifest_is_metadata_only():
    annotations = [record("golden-1"), record("exclude-1", excluded="yes")]
    qc = golden_qc_report(annotations, [{"journey_id": "golden-1"}, {"journey_id": "exclude-1"}], [{"journey_id": "dev-1"}])
    assert qc["status"] == "VALID"
    assert qc["included_count"] == 1
    manifest = freeze_manifest(annotations, annotation_version="v1", annotators=["annotator_1"], qc_status="pending")
    assert manifest["included_journey_ids"] == ["golden-1"]
    assert manifest["qc_status"] == "pending"
