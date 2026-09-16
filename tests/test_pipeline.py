from src.agent.pipeline import run_agent
from src.agent.retrieval import DevelopmentJourneyRetriever


def journey(journey_id, customer_text, support_text):
    return {
        "journey_id": journey_id,
        "reconstruction_status": "complete",
        "messages": [
            {"tweet_id": f"{journey_id}-1", "role": "customer", "text": customer_text},
            {"tweet_id": f"{journey_id}-2", "role": "support", "text": support_text},
            {"tweet_id": f"{journey_id}-3", "role": "customer", "text": "Still skips and does not work"},
        ],
    }


def test_pipeline_returns_traceable_structured_result():
    target = journey("current", "The web player skips songs", "What browser are you using?")
    development = [
        journey("dev-1", "The web player skips songs in Chrome", "Try another browser"),
        journey("dev-2", "I was charged twice", "Please contact secure support"),
    ]
    retriever = DevelopmentJourneyRetriever(development)
    result = run_agent(target, retriever, evaluation_point_id="current-3", top_k=2)
    assert result.conversation_id == "current"
    assert result.evaluation_point_message_id == "current-3"
    assert result.intent.intent == "Playback reliability"
    assert result.state.state
    assert result.retrieved_journeys
    assert result.action.selected_action
    assert result.escalation.decision in {"AUTO_HANDLE", "ESCALATE"}
    assert result.response.text
    assert result.to_dict()["response"]["selected_action"] == result.action.selected_action
