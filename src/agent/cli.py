"""Command-line demo for the deterministic SpotifyCares support agent."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .pipeline import AgentResult, run_agent
from .retrieval import DevelopmentJourneyRetriever

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEVELOPMENT = ROOT / "data" / "processed" / "spotify_development.jsonl"
DEFAULT_GOLDEN = ROOT / "data" / "processed" / "spotify_golden_candidates.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_target(path: Path, journey_id: str | None) -> dict[str, Any]:
    records = read_jsonl(path)
    if journey_id:
        for record in records:
            if record.get("journey_id") == journey_id:
                return record
        raise ValueError(f"journey_id not found in input: {journey_id}")
    if not records:
        raise ValueError(f"input contains no journeys: {path}")
    return records[0]


def print_result(result: AgentResult) -> None:
    print("CUSTOMER")
    print(result.state.reason or "Current customer message is the evaluation point.")
    print()
    print("CASE UNDERSTANDING")
    print(f"Intent: {result.intent.intent or 'UNLABELLED'} (confidence {result.intent.confidence:.2f})")
    print(f"Intent evidence: {', '.join(result.intent.evidence) or 'none'}")
    print(f"State: {result.state.state} (confidence {result.state.confidence:.2f})")
    print(f"Missing information: {', '.join(result.state.missing_information) or 'none detected'}")
    print()
    print("ATTEMPTED ACTIONS")
    if result.attempted_actions:
        for item in result.attempted_actions:
            print(f"{item.order}. {item.action} [{item.result}] source={item.source_message_id}")
    else:
        print("none observed")
    print()
    print("HISTORICAL EVIDENCE")
    if result.retrieved_journeys:
        for item in result.retrieved_journeys:
            print(f"{item.rank}. {item.journey_id} score={item.retrieval_score:.3f}")
    else:
        print("none retrieved")
    for item in result.transition_evidence:
        print(f"  {item.state} -> {item.action}: {item.support_count} observations ({item.evidence_strength})")
    print()
    print("NEXT BEST SUPPORT ACTION")
    print(result.action.selected_action)
    print(f"WHY: {result.action.reason}")
    if result.action.alternatives:
        print(f"Alternatives: {', '.join(result.action.alternatives)}")
    print()
    print("AUTOMATION DECISION")
    print(result.escalation.decision)
    print(f"Risk: {result.escalation.risk}")
    print(f"REASON: {result.escalation.reason}")
    print()
    print("DRAFT REPLY")
    print(result.response.text)
    print(f"Grounded: {result.response.grounded}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run the first development journey")
    parser.add_argument("--input", type=Path, help="prepared journey JSONL to inspect")
    parser.add_argument("--journey-id", help="select a journey from --input")
    parser.add_argument("--evaluation-point", help="customer message ID for the evaluation point")
    parser.add_argument("--development", type=Path, default=DEFAULT_DEVELOPMENT)
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="emit the structured trace as JSON")
    args = parser.parse_args()
    target_path = args.input or args.development
    if not args.demo and args.input is None:
        parser.error("use --demo or provide --input")
    target = load_target(target_path, args.journey_id)
    retriever = DevelopmentJourneyRetriever.from_jsonl(args.development, golden_path=args.golden)
    result = run_agent(target, retriever, evaluation_point_id=args.evaluation_point, top_k=args.top_k)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print_result(result)


if __name__ == "__main__":
    main()
