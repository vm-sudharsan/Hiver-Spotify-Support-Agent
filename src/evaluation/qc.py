"""Golden-set freeze and leakage QC helpers."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def golden_qc_report(
    annotations: Sequence[dict[str, Any]],
    candidates: Sequence[dict[str, Any]],
    development: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    candidate_ids = {record.get("journey_id") for record in candidates}
    development_ids = {record.get("journey_id") for record in development}
    annotation_ids = [record.get("journey_id") for record in annotations]
    errors: list[str] = []
    if len(annotation_ids) != len(set(annotation_ids)):
        errors.append("duplicate journey IDs in annotations")
    for journey_id in annotation_ids:
        if journey_id not in candidate_ids:
            errors.append(f"annotation is not a reserved candidate: {journey_id}")
        if journey_id in development_ids:
            errors.append(f"golden journey appears in development data: {journey_id}")
    included = [record for record in annotations if record.get("exclude_from_golden") != "yes"]
    excluded = [record for record in annotations if record.get("exclude_from_golden") == "yes"]
    return {
        "status": "VALID" if not errors else "INVALID",
        "annotation_count": len(annotations),
        "included_count": len(included),
        "excluded_count": len(excluded),
        "candidate_count": len(candidate_ids),
        "errors": errors,
    }


def freeze_manifest(
    annotations: Sequence[dict[str, Any]],
    *,
    annotation_version: str,
    annotators: Sequence[str],
    qc_status: str,
) -> dict[str, Any]:
    """Create metadata only; callers decide when to write a human-approved freeze."""
    included = [record for record in annotations if record.get("exclude_from_golden") != "yes"]
    excluded = [record for record in annotations if record.get("exclude_from_golden") == "yes"]
    return {
        "annotation_version": annotation_version,
        "annotators": list(annotators),
        "qc_status": qc_status,
        "included_journey_ids": [record.get("journey_id") for record in included],
        "excluded_journey_ids": [record.get("journey_id") for record in excluded],
    }
