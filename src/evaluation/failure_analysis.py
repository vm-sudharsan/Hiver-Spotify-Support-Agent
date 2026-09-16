"""Trace export and suspected-failure signal analysis."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.agent.pipeline import AgentResult


def trace_record(result: AgentResult, *, model_version: str = "deterministic-v1", latency_ms: float | None = None) -> dict[str, Any]:
    """Create an auditable trace record without including secrets or raw provider output."""
    return {
        "conversation_id": result.conversation_id,
        "evaluation_point_message_id": result.evaluation_point_message_id,
        "intent": asdict(result.intent),
        "state": asdict(result.state),
        "attempted_actions": [asdict(item) for item in result.attempted_actions],
        "retrieved_journeys": [asdict(item) for item in result.retrieved_journeys],
        "historical_evidence": [asdict(item) for item in result.transition_evidence],
        "candidate_actions": {
            "selected": result.action.selected_action,
            "alternatives": list(result.action.alternatives),
            "component_scores": result.action.component_scores,
            "rejected": result.action.rejected_actions,
        },
        "escalation": asdict(result.escalation),
        "response": asdict(result.response),
        "model_version": model_version,
        "latency_ms": latency_ms,
    }


def write_traces(path: Path, traces: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(trace, ensure_ascii=False, sort_keys=True) + "\n" for trace in traces), encoding="utf-8")


def suspected_failure_signals(trace: dict[str, Any]) -> list[str]:
    """Return investigation signals, not confirmed failure labels."""
    signals: list[str] = []
    intent = trace.get("intent", {})
    state = trace.get("state", {})
    retrieved = trace.get("retrieved_journeys", [])
    evidence = trace.get("historical_evidence", [])
    action = trace.get("candidate_actions", {})
    response = trace.get("response", {})
    if intent.get("confidence", 1.0) < 0.5:
        signals.append("LOW_INTENT_CONFIDENCE")
    if state.get("confidence", 1.0) < 0.5:
        signals.append("LOW_STATE_CONFIDENCE")
    if not retrieved or max((item.get("retrieval_score", 0.0) for item in retrieved), default=0.0) < 0.1:
        signals.append("LOW_RETRIEVAL_SIMILARITY")
    if not evidence:
        signals.append("NO_HISTORICAL_TRANSITION_EVIDENCE")
    if action.get("selected") in action.get("rejected", {}):
        signals.append("REPEATED_FAILED_ACTION_SELECTED")
    if trace.get("escalation", {}).get("decision") == "ESCALATE":
        signals.append("ESCALATION_REVIEW")
    if response.get("warnings"):
        signals.append("RESPONSE_GROUNDING_WARNING")
    return signals


def analyze_traces(traces: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [{"conversation_id": trace.get("conversation_id"), "signals": suspected_failure_signals(trace)} for trace in traces]
    return {
        "status": "SIGNALS_ONLY",
        "trace_count": len(traces),
        "suspected_signal_count": sum(bool(row["signals"]) for row in rows),
        "rows": rows,
        "note": "Signals identify cases for inspection; they are not evaluated failures without human-grounded labels.",
    }
