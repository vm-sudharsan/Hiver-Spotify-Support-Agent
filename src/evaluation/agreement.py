"""Two-annotator agreement and golden-set QC metrics."""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any


def cohens_kappa(left: Sequence[str], right: Sequence[str]) -> float | None:
    if len(left) != len(right):
        raise ValueError("agreement inputs must have equal lengths")
    if not left:
        return None
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    categories = set(left) | set(right)
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum((left_counts[value] / len(left)) * (right_counts[value] / len(right)) for value in categories)
    if expected == 1:
        return 1.0
    return round((observed - expected) / (1 - expected), 4)


def jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    left_set, right_set = set(left), set(right)
    if not left_set and not right_set:
        return 1.0
    return round(len(left_set & right_set) / len(left_set | right_set), 4)


def agreement_report(
    annotator_one: Sequence[dict[str, Any]],
    annotator_two: Sequence[dict[str, Any]],
    *,
    categorical_fields: Sequence[str] = ("intent", "current_state", "outcome", "escalation_eligible"),
) -> dict[str, Any]:
    left = {record.get("journey_id"): record for record in annotator_one if record.get("journey_id")}
    right = {record.get("journey_id"): record for record in annotator_two if record.get("journey_id")}
    shared_ids = sorted(set(left) & set(right))
    if not shared_ids:
        return {"status": "NOT_READY", "shared_count": 0, "categorical_kappa": {}, "multilabel_jaccard": None, "adjudication_rate": None, "exclusion_rate": None}
    kappas: dict[str, float | None] = {}
    for field in categorical_fields:
        values_left = [str(left[journey_id].get(field) or "") for journey_id in shared_ids]
        values_right = [str(right[journey_id].get(field) or "") for journey_id in shared_ids]
        kappas[field] = cohens_kappa(values_left, values_right)
    jaccards = [jaccard(left[journey_id].get("escalation_reason_codes", []), right[journey_id].get("escalation_reason_codes", [])) for journey_id in shared_ids]
    disagreements = sum(any(left[journey_id].get(field) != right[journey_id].get(field) for field in categorical_fields) for journey_id in shared_ids)
    exclusions = sum(left[journey_id].get("exclude_from_golden") == "yes" or right[journey_id].get("exclude_from_golden") == "yes" for journey_id in shared_ids)
    return {
        "status": "MEASURED",
        "shared_count": len(shared_ids),
        "categorical_kappa": kappas,
        "multilabel_jaccard": round(sum(jaccards) / len(jaccards), 4),
        "adjudication_rate": round(disagreements / len(shared_ids), 4),
        "exclusion_rate": round(exclusions / len(shared_ids), 4),
    }
