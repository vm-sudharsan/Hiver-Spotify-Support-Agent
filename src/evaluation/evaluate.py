"""Run the human-grounded golden evaluation when annotations exist."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.agent.pipeline import run_agent
from src.agent.retrieval import DevelopmentJourneyRetriever
from src.evaluation.failure_analysis import trace_record
from .metrics import evaluate_predictions
from .validate_annotations import read_jsonl, validate_annotations

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANNOTATIONS = ROOT / "data" / "annotations" / "annotator_1.jsonl"
DEFAULT_CANDIDATES = ROOT / "data" / "processed" / "golden_annotation_candidates.jsonl"
DEFAULT_DEVELOPMENT = ROOT / "data" / "processed" / "spotify_development.jsonl"


def run_evaluation(
    annotation_path: Path,
    candidates_path: Path = DEFAULT_CANDIDATES,
    development_path: Path = DEFAULT_DEVELOPMENT,
) -> dict[str, Any]:
    validation = validate_annotations(annotation_path, candidates_path, development_path)
    if not validation["ok"]:
        return {"status": validation["status"], "validation": validation, "metrics": "NOT YET MEASURED"}
    annotations = read_jsonl(annotation_path)
    candidates = {record["journey_id"]: record for record in read_jsonl(candidates_path)}
    retriever = DevelopmentJourneyRetriever.from_jsonl(development_path, golden_path=candidates_path)
    predictions: dict[str, dict[str, Any]] = {}
    traces: list[dict[str, Any]] = []
    for annotation in annotations:
        if annotation.get("exclude_from_golden") == "yes":
            continue
        target = candidates[annotation["journey_id"]]
        result = run_agent(
            target,
            retriever,
            evaluation_point_id=annotation.get("evaluation_point_message_id"),
        )
        predictions[annotation["journey_id"]] = {
            "intent": result.intent.intent,
            "state": result.state.state,
            "action": result.action.selected_action,
            "escalation": result.escalation.decision,
        }
        traces.append(trace_record(result))
    included = [annotation for annotation in annotations if annotation.get("exclude_from_golden") != "yes"]
    return {"status": "MEASURED", "validation": validation, "metrics": evaluate_predictions(included, predictions, traces)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--development", type=Path, default=DEFAULT_DEVELOPMENT)
    args = parser.parse_args()
    print(json.dumps(run_evaluation(args.annotations, args.candidates, args.development), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
