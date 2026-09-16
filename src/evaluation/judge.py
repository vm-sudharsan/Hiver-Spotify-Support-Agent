"""Optional structured LLM-as-judge for generated support responses."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from src.agent.llm import ConfiguredLLM

DIMENSIONS = ("groundedness", "action_alignment", "relevance", "safety", "clarity", "escalation_appropriateness")


@dataclass(frozen=True)
class JudgeResult:
    status: str
    scores: dict[str, int] | None = None
    rationale: str = ""
    model: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def judge_response(
    *,
    customer_message: str,
    draft_response: str,
    selected_action: str,
    escalation_decision: str,
    evidence_summary: str,
    provider: ConfiguredLLM | None = None,
) -> JudgeResult:
    provider = provider or ConfiguredLLM()
    system = (
        "You are a strict evaluator of a Spotify support response. Return JSON only with "
        "scores 1-5 for groundedness, action_alignment, relevance, safety, clarity, "
        "escalation_appropriateness, plus concise rationale. Do not infer hidden outcomes."
    )
    user = "\n".join((
        f"CUSTOMER: {customer_message}",
        f"DRAFT: {draft_response}",
        f"SELECTED ACTION: {selected_action}",
        f"ESCALATION: {escalation_decision}",
        f"HISTORICAL EVIDENCE: {evidence_summary}",
    ))
    result = provider.structured_json(system, user)
    if result.status != "OK" or result.value is None:
        return JudgeResult(result.status, model=result.model, error=result.error)
    scores = result.value.get("scores")
    if not isinstance(scores, dict) or any(dimension not in scores for dimension in DIMENSIONS):
        return JudgeResult("INVALID", model=result.model, error="judge response omitted required dimensions")
    try:
        normalized = {dimension: int(scores[dimension]) for dimension in DIMENSIONS}
    except (TypeError, ValueError):
        return JudgeResult("INVALID", model=result.model, error="judge scores must be integers")
    if any(score < 1 or score > 5 for score in normalized.values()):
        return JudgeResult("INVALID", model=result.model, error="judge scores must be between 1 and 5")
    rationale = result.value.get("rationale", "")
    return JudgeResult("MEASURED", normalized, str(rationale), result.model)
