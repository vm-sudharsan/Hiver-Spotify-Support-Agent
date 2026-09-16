import json

from src.evaluation.metrics import binary_metrics, classification_metrics, evaluate_predictions
from src.evaluation.validate_annotations import validate_annotations


def write(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def candidate(journey_id):
    return {"journey_id": journey_id, "root_tweet_id": f"root-{journey_id}", "messages": []}


def annotation(journey_id):
    return {
        "annotation_id": f"annotation-{journey_id}",
        "journey_id": journey_id,
        "root_tweet_id": f"root-{journey_id}",
        "annotator_id": "annotator_1",
        "intent": "Playback reliability",
        "current_state": "CONTEXT_COLLECTED",
        "intent_status": "labelled",
        "state_status": "labelled",
        "observed_next_action": "BROWSER_REMEDIATION",
        "ideal_next_action": "BROWSER_REMEDIATION",
        "outcome": "unknown",
        "escalation_eligible": "no",
        "evidence_visibility": "visible",
        "confidence": "medium",
        "missing_information": [],
        "attempted_actions": [],
        "exclude_from_golden": "no",
    }


def test_metrics_are_deterministic():
    result = classification_metrics(["a", "a", "b"], ["a", "b", "b"], ["a", "b"])
    assert result["accuracy"] == 0.6667
    assert result["macro_f1"] == 0.6667
    binary = binary_metrics(["yes", "no", "yes"], ["yes", "yes", "no"])
    assert binary["precision"] == 0.5
    assert binary["recall"] == 0.5


def test_annotation_validator_checks_candidate_membership_and_isolation(tmp_path):
    annotation_path = tmp_path / "annotations.jsonl"
    candidates_path = tmp_path / "candidates.jsonl"
    development_path = tmp_path / "development.jsonl"
    write(annotation_path, [annotation("golden-1")])
    write(candidates_path, [candidate("golden-1")])
    write(development_path, [candidate("dev-1")])
    report = validate_annotations(annotation_path, candidates_path, development_path)
    assert report["ok"]
    assert report["record_count"] == 1

    write(development_path, [candidate("golden-1")])
    invalid = validate_annotations(annotation_path, candidates_path, development_path)
    assert not invalid["ok"]
    assert any("development" in error for error in invalid["errors"])


def test_evaluation_predictions_reports_all_required_metric_families():
    gold_record = annotation("golden-1")
    gold_record["escalation_eligible"] = "yes"
    gold = [gold_record]
    predictions = {"golden-1": {"intent": "Playback reliability", "state": "CONTEXT_COLLECTED", "action": "BROWSER_REMEDIATION", "escalation": "ESCALATE"}}
    result = evaluate_predictions(gold, predictions)
    assert result["count"] == 1
    assert result["intent"]["accuracy"] == 1.0
    assert result["state"]["macro_f1"] == 1.0
    assert result["next_action"]["accuracy"] == 1.0
    assert result["escalation"]["f1"] == 1.0
    assert result["operational"]["repeated_failed_action_rate"]["status"] == "NOT YET MEASURED"
