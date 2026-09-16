import json

import pytest

from src.agent.models import CaseState, Message
from src.agent.retrieval import DevelopmentJourneyRetriever, build_query


def journey(journey_id, text):
    return {
        "journey_id": journey_id,
        "reconstruction_status": "complete",
        "messages": [
            {"tweet_id": f"{journey_id}-1", "role": "customer", "text": text},
            {"tweet_id": f"{journey_id}-2", "role": "support", "text": "Support response"},
        ],
    }


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_retrieval_ranks_whole_journeys_by_query(tmp_path):
    development = tmp_path / "development.jsonl"
    write_jsonl(
        development,
        [
            journey("browser", "web player skips songs in Chrome browser"),
            journey("billing", "charged twice for Premium subscription"),
        ],
    )
    retriever = DevelopmentJourneyRetriever.from_jsonl(development)
    results = retriever.search("Chrome web player skips songs", top_k=1)
    assert results[0].journey_id == "browser"
    assert results[0].rank == 1
    assert results[0].source_message_ids == ("browser-1", "browser-2")
    assert retriever.size == 2


def test_case_state_query_includes_failed_actions_without_labels(tmp_path):
    development = tmp_path / "development.jsonl"
    write_jsonl(development, [journey("one", "music still skips")])
    case = CaseState(
        conversation_id="current",
        current_customer_message=Message("current-1", "customer", "Music still skips"),
        failed_actions=["SESSION_RESET"],
        current_environment={"browser": "Chrome"},
    )
    query = build_query(case)
    assert "Music still skips" in query
    assert "failed action: SESSION_RESET" in query
    assert "environment: browser=Chrome" in query


def test_golden_overlap_is_rejected_and_excluded(tmp_path):
    development = tmp_path / "development.jsonl"
    golden = tmp_path / "golden.jsonl"
    write_jsonl(development, [journey("dev", "playback issue"), journey("golden", "billing issue")])
    write_jsonl(golden, [journey("golden", "billing issue")])
    with pytest.raises(ValueError, match="golden journeys"):
        DevelopmentJourneyRetriever.from_jsonl(development, golden_path=golden)


def test_search_excludes_explicit_current_journey(tmp_path):
    development = tmp_path / "development.jsonl"
    write_jsonl(development, [journey("one", "playback issue"), journey("two", "playback issue"), journey("three", "billing issue")])
    retriever = DevelopmentJourneyRetriever.from_jsonl(development)
    results = retriever.search("playback issue", top_k=3, exclude_journey_ids={"one"})
    assert "one" not in {result.journey_id for result in results}
    assert len(results) == 2
