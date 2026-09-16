from src.agent.action_policy import ActionDecision
from src.agent.escalation import EscalationDecision
from src.agent.intent import IntentPrediction
from src.agent.models import CaseState, Message
from src.agent.response import ResponseDraft
from src.agent.state import StatePrediction
from src.agent.pipeline import AgentResult
from src.agent.transitions import TransitionEvidence
from src.evaluation.failure_analysis import analyze_traces, suspected_failure_signals, trace_record, write_traces


def result():
    return AgentResult(
        conversation_id="journey-1",
        evaluation_point_message_id="3",
        intent=IntentPrediction("Playback reliability", 0.4, evidence=("skip",)),
        state=StatePrediction("SYMPTOM_REPORTED", 0.8),
        attempted_actions=(),
        retrieved_journeys=(),
        transition_evidence=(),
        action=ActionDecision("ASK_PLATFORM_CONTEXT", 1.0, "reason", (), (), {"state_fit": 1.0}, {}),
        escalation=EscalationDecision("AUTO_HANDLE", (), "safe", "low"),
        response=ResponseDraft("Please share your device.", "ASK_PLATFORM_CONTEXT", "AUTO_HANDLE", (), (), ()),
    )


def test_trace_contains_required_audit_fields(tmp_path):
    trace = trace_record(result(), latency_ms=12.5)
    assert trace["conversation_id"] == "journey-1"
    assert "historical_evidence" in trace
    assert trace["model_version"] == "deterministic-v1"
    path = tmp_path / "traces.jsonl"
    write_traces(path, [trace])
    assert path.read_text(encoding="utf-8").count("journey-1") == 1


def test_signals_are_not_claimed_as_failures():
    signals = suspected_failure_signals(trace_record(result()))
    assert "LOW_INTENT_CONFIDENCE" in signals
    assert "NO_HISTORICAL_TRANSITION_EVIDENCE" in signals
    report = analyze_traces([trace_record(result())])
    assert report["status"] == "SIGNALS_ONLY"
    assert "not evaluated failures" in report["note"]
