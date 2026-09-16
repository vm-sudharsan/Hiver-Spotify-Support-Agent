import json

import pytest

from src.evaluation.freeze_golden import freeze_golden


def write(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def annotation(journey_id, excluded="no"):
    return {
        "annotation_id": f"a-{journey_id}",
        "journey_id": journey_id,
        "root_tweet_id": f"root-{journey_id}",
        "annotator_id": "annotator_1",
        "intent": "Playback reliability",
        "current_state": "CONTEXT_COLLECTED",
        "intent_status": "labelled",
        "state_status": "labelled",
        "observed_next_action": "ASK_PLATFORM_CONTEXT",
        "ideal_next_action": "ASK_PLATFORM_CONTEXT",
        "outcome": "unknown",
        "escalation_eligible": "no",
        "evidence_visibility": "visible",
        "confidence": "medium",
        "missing_information": [],
        "attempted_actions": [],
        "exclude_from_golden": excluded,
    }


def candidate(journey_id):
    return {"journey_id": journey_id, "root_tweet_id": f"root-{journey_id}"}


def test_freeze_writes_only_included_human_annotations(tmp_path):
    annotations = tmp_path / "annotations.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    development = tmp_path / "development.jsonl"
    output = tmp_path / "evaluation" / "golden.jsonl"
    manifest = tmp_path / "evaluation" / "golden_manifest.json"
    write(annotations, [annotation("one"), annotation("two", "yes")])
    write(candidates, [candidate("one"), candidate("two")])
    write(development, [candidate("dev")])
    result = freeze_golden(annotations, candidates, development, output, manifest, min_count=1)
    assert result["included_count"] == 1
    assert [json.loads(line)["journey_id"] for line in output.read_text(encoding="utf-8").splitlines()] == ["one"]
    assert json.loads(manifest.read_text(encoding="utf-8"))["excluded_count"] == 1


def test_freeze_rejects_development_overlap(tmp_path):
    annotations = tmp_path / "annotations.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    development = tmp_path / "development.jsonl"
    write(annotations, [annotation("one")])
    write(candidates, [candidate("one")])
    write(development, [candidate("one")])
    with pytest.raises(ValueError, match="overlap"):
        freeze_golden(annotations, candidates, development, tmp_path / "golden.jsonl", tmp_path / "manifest.json", min_count=1)


def test_freeze_rejects_too_small_final_set(tmp_path):
    annotations = tmp_path / "annotations.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    development = tmp_path / "development.jsonl"
    write(annotations, [annotation("one")])
    write(candidates, [candidate("one")])
    write(development, [candidate("dev")])
    with pytest.raises(ValueError, match="minimum"):
        freeze_golden(annotations, candidates, development, tmp_path / "golden.jsonl", tmp_path / "manifest.json")
