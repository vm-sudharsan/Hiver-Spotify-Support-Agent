"""Validate human annotations without creating or inferring labels."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agent.taxonomy import ACTIONS, INTENTS, REQUIREMENTS, REQUIREMENT_STATUSES, STATES, ACTION_RESULTS, EXPLICITNESS

INTENT_STATUSES = {"labelled", "ambiguous", "insufficient_evidence", "unlabelled"}
STATE_STATUSES = INTENT_STATUSES
OUTCOMES = {"resolved", "monitoring_or_improved", "unresolved", "escalated_or_handoff", "dm_ended", "unknown"}
ESCALATION = {"yes", "no", "uncertain"}
EVIDENCE = {"visible", "partial", "dm_ended", "unknown"}
CONFIDENCE = {"high", "medium", "low"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_annotations(
    annotation_path: Path,
    candidates_path: Path,
    development_path: Path,
    *,
    annotator_id: str | None = None,
) -> dict[str, Any]:
    """Return a validation report; never repairs or labels annotations."""
    if not annotation_path.exists():
        return {"ok": False, "status": "NOT_READY", "errors": [f"annotation file does not exist: {annotation_path}"]}
    candidates = {record.get("journey_id"): record for record in read_jsonl(candidates_path)}
    development_ids = {record.get("journey_id") for record in read_jsonl(development_path)}
    records = read_jsonl(annotation_path)
    errors: list[str] = []
    annotation_ids: set[str] = set()
    journey_ids: set[str] = set()
    annotators: set[str] = set()
    excluded = 0
    for index, record in enumerate(records, 1):
        prefix = f"record {index}"
        annotation_id = record.get("annotation_id")
        journey_id = record.get("journey_id")
        if not annotation_id:
            errors.append(f"{prefix}: annotation_id is required")
        elif annotation_id in annotation_ids:
            errors.append(f"{prefix}: duplicate annotation_id")
        annotation_ids.add(annotation_id)
        if not journey_id or journey_id in journey_ids:
            errors.append(f"{prefix}: missing or duplicate journey_id")
        journey_ids.add(journey_id)
        if journey_id not in candidates:
            errors.append(f"{prefix}: journey_id is not a golden annotation candidate")
        elif record.get("root_tweet_id") != candidates[journey_id].get("root_tweet_id"):
            errors.append(f"{prefix}: root_tweet_id does not match candidate")
        if journey_id in development_ids:
            errors.append(f"{prefix}: golden journey appears in development data")
        current_annotator = record.get("annotator_id")
        if not current_annotator:
            errors.append(f"{prefix}: annotator_id is required")
        annotators.add(current_annotator)
        if annotator_id and current_annotator != annotator_id:
            errors.append(f"{prefix}: annotator_id does not match requested annotator")
        _check_choice(record, "intent", INTENTS, prefix, errors, optional=True)
        _check_choice(record, "current_state", STATES, prefix, errors, optional=True)
        _check_choice(record, "intent_status", INTENT_STATUSES, prefix, errors)
        _check_choice(record, "state_status", STATE_STATUSES, prefix, errors)
        _check_choice(record, "observed_next_action", set(ACTIONS) | {"UNKNOWN", "UNLABELLED"}, prefix, errors)
        _check_choice(record, "ideal_next_action", ACTIONS, prefix, errors, optional=True)
        _check_choice(record, "outcome", OUTCOMES, prefix, errors)
        _check_choice(record, "escalation_eligible", ESCALATION, prefix, errors)
        _check_choice(record, "evidence_visibility", EVIDENCE, prefix, errors)
        _check_choice(record, "confidence", CONFIDENCE, prefix, errors)
        if not isinstance(record.get("missing_information"), list):
            errors.append(f"{prefix}: missing_information must be a list")
        else:
            for item in record["missing_information"]:
                if not isinstance(item, dict) or item.get("requirement") not in REQUIREMENTS or item.get("status") not in REQUIREMENT_STATUSES:
                    errors.append(f"{prefix}: invalid missing-information item")
        if not isinstance(record.get("attempted_actions"), list):
            errors.append(f"{prefix}: attempted_actions must be a list")
        else:
            for item in record["attempted_actions"]:
                if not isinstance(item, dict) or item.get("action") not in ACTIONS or item.get("explicitness") not in EXPLICITNESS or item.get("result") not in ACTION_RESULTS:
                    errors.append(f"{prefix}: invalid attempted-action item")
        if record.get("exclude_from_golden") == "yes":
            excluded += 1
    return {
        "ok": not errors,
        "status": "VALID" if not errors else "INVALID",
        "record_count": len(records),
        "excluded_count": excluded,
        "annotators": sorted(value for value in annotators if value),
        "errors": errors,
    }


def _check_choice(record: dict[str, Any], field: str, allowed: Any, prefix: str, errors: list[str], *, optional: bool = False) -> None:
    value = record.get(field)
    if optional and value in {None, ""}:
        return
    if value not in allowed:
        errors.append(f"{prefix}: {field} is missing or outside the frozen vocabulary")
