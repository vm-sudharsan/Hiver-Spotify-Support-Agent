"""Small dependency-light metrics used by the golden evaluation harness."""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any


def classification_metrics(y_true: Sequence[str], y_pred: Sequence[str], labels: Sequence[str]) -> dict[str, Any]:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if not y_true:
        return {"status": "NOT YET MEASURED", "accuracy": None, "macro_f1": None, "count": 0}
    accuracy = sum(actual == predicted for actual, predicted in zip(y_true, y_pred)) / len(y_true)
    f1_values = []
    for label in labels:
        true_positive = sum(actual == label and predicted == label for actual, predicted in zip(y_true, y_pred))
        false_positive = sum(actual != label and predicted == label for actual, predicted in zip(y_true, y_pred))
        false_negative = sum(actual == label and predicted != label for actual, predicted in zip(y_true, y_pred))
        denominator = 2 * true_positive + false_positive + false_negative
        f1_values.append((2 * true_positive / denominator) if denominator else 0.0)
    return {"status": "MEASURED", "accuracy": round(accuracy, 4), "macro_f1": round(sum(f1_values) / len(f1_values), 4), "count": len(y_true)}


def binary_metrics(y_true: Sequence[str], y_pred: Sequence[str], positive: str = "yes") -> dict[str, Any]:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if not y_true:
        return {"status": "NOT YET MEASURED", "precision": None, "recall": None, "f1": None, "count": 0}
    tp = sum(actual == positive and predicted == positive for actual, predicted in zip(y_true, y_pred))
    fp = sum(actual != positive and predicted == positive for actual, predicted in zip(y_true, y_pred))
    fn = sum(actual == positive and predicted != positive for actual, predicted in zip(y_true, y_pred))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"status": "MEASURED", "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4), "count": len(y_true)}


def operational_metrics(traces: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Measure trace-level safety/evidence properties without inventing labels."""
    if not traces:
        return {name: {"status": "NOT YET MEASURED", "value": None, "count": 0} for name in ("repeated_failed_action_rate", "evidence_coverage", "transition_consistency", "response_groundedness")}
    repeated = []
    evidence_coverage = []
    consistency = []
    grounded = []
    for trace in traces:
        candidate_actions = trace.get("candidate_actions", {})
        rejected = candidate_actions.get("rejected", {})
        selected = candidate_actions.get("selected")
        repeated.append(float(selected in rejected))
        retrieved = trace.get("retrieved_journeys", [])
        historical = trace.get("historical_evidence", [])
        evidence_coverage.append(float(bool(retrieved and historical)))
        total_support = sum(item.get("support_count", 0) for item in historical)
        selected_support = sum(item.get("support_count", 0) for item in historical if item.get("action") == selected)
        consistency.append(selected_support / total_support if total_support else 0.0)
        grounded.append(float(not trace.get("response", {}).get("warnings")))
    return {
        "repeated_failed_action_rate": {"status": "MEASURED", "value": round(sum(repeated) / len(repeated), 4), "count": len(traces)},
        "evidence_coverage": {"status": "MEASURED", "value": round(sum(evidence_coverage) / len(evidence_coverage), 4), "count": len(traces)},
        "transition_consistency": {"status": "MEASURED", "value": round(sum(consistency) / len(consistency), 4), "count": len(traces)},
        "response_groundedness": {"status": "MEASURED", "value": round(sum(grounded) / len(grounded), 4), "count": len(traces)},
    }


def evaluate_predictions(
    gold_records: Sequence[dict[str, Any]],
    predictions: dict[str, dict[str, Any]],
    traces: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Evaluate only records with a corresponding generated prediction."""
    aligned = [(record, predictions[record["journey_id"]]) for record in gold_records if record.get("journey_id") in predictions]
    intent_true = [record["intent"] for record, _ in aligned if record.get("intent")]
    intent_pred = [prediction.get("intent") for record, prediction in aligned if record.get("intent")]
    state_true = [record["current_state"] for record, _ in aligned if record.get("current_state")]
    state_pred = [prediction.get("state") for record, prediction in aligned if record.get("current_state")]
    action_true = [record.get("ideal_next_action") or record.get("observed_next_action") for record, _ in aligned]
    action_pred = [prediction.get("action") for _, prediction in aligned]
    escalation_true = [record.get("escalation_eligible") for record, _ in aligned]
    escalation_pred = ["yes" if prediction.get("escalation") == "ESCALATE" else "no" for _, prediction in aligned]
    return {
        "count": len(aligned),
        "intent": classification_metrics(intent_true, intent_pred, sorted(set(intent_true))),
        "state": classification_metrics(state_true, state_pred, sorted(set(state_true))),
        "next_action": classification_metrics(action_true, action_pred, sorted(set(action_true))),
        "escalation": binary_metrics(escalation_true, escalation_pred),
        "operational": operational_metrics(traces),
    }
