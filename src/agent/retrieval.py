"""Development-only, journey-level historical retrieval."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .models import CaseState, CanonicalConversation, RetrievedJourney
from .normalization import conversation_from_journey

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover - exercised only in dependency-light environments.
    TfidfVectorizer = None
    cosine_similarity = None

TOKEN_RE = re.compile(r"(?u)\b\w+\b")


def journey_text(conversation: CanonicalConversation) -> str:
    """Build a sequence-preserving retrieval document from a whole journey."""
    return " ".join(f"{message.role}: {message.text}" for message in conversation.messages)


def build_query(case: CaseState, context: tuple[Any, ...] = ()) -> str:
    """Combine current evidence with structured state without adding labels."""
    parts = [f"customer: {case.current_customer_message.text}"]
    parts.extend(str(message.text) for message in context)
    if case.intent:
        parts.append(f"intent: {case.intent}")
    if case.current_state:
        parts.append(f"state: {case.current_state}")
    parts.extend(f"environment: {key}={value}" for key, value in sorted(case.current_environment.items()))
    parts.extend(f"failed action: {action}" for action in case.failed_actions)
    return " ".join(parts)


class DevelopmentJourneyRetriever:
    """TF-IDF retrieval over development journeys only."""

    def __init__(
        self,
        journeys: list[dict[str, Any]],
        *,
        golden_journey_ids: set[str] | None = None,
    ) -> None:
        self._records = {str(record.get("journey_id")): record for record in journeys}
        if not self._records or "" in self._records:
            raise ValueError("retrieval requires non-empty journey IDs")
        self._golden_ids = golden_journey_ids or set()
        overlap = self._golden_ids.intersection(self._records)
        if overlap:
            raise ValueError(f"golden journeys cannot enter the development retrieval index: {sorted(overlap)[:3]}")
        self._conversations = {
            journey_id: conversation_from_journey(record)
            for journey_id, record in self._records.items()
        }
        self._documents = [journey_text(self._conversations[journey_id]) for journey_id in self._records]
        if not any(document.strip() for document in self._documents):
            raise ValueError("retrieval requires at least one non-empty journey document")
        self._journey_ids = tuple(self._records)
        if TfidfVectorizer is not None:
            self._vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)
            self._matrix = self._vectorizer.fit_transform(self._documents)
            self._fallback_vectors = None
        else:
            self._vectorizer = None
            self._matrix = None
            self._fallback_vectors = [_fallback_vector(document) for document in self._documents]

    @classmethod
    def from_jsonl(
        cls,
        development_path: Path,
        *,
        golden_path: Path | None = None,
    ) -> "DevelopmentJourneyRetriever":
        development = _read_jsonl(development_path)
        golden_ids = {str(record["journey_id"]) for record in _read_jsonl(golden_path)} if golden_path else set()
        return cls(development, golden_journey_ids=golden_ids)

    @property
    def size(self) -> int:
        return len(self._journey_ids)

    def search(
        self,
        query: str | CaseState,
        *,
        top_k: int = 5,
        exclude_journey_ids: set[str] | None = None,
    ) -> list[RetrievedJourney]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        query_text = build_query(query) if isinstance(query, CaseState) else str(query)
        if not query_text.strip():
            raise ValueError("retrieval query must not be empty")
        excluded = (exclude_journey_ids or set()) | self._golden_ids
        scores = self._scores(query_text)
        ranked = sorted(
            (
                (float(score), journey_id)
                for journey_id, score in zip(self._journey_ids, scores)
                if journey_id not in excluded
            ),
            key=lambda item: (-item[0], item[1]),
        )
        results = []
        for rank, (score, journey_id) in enumerate(ranked[:top_k], 1):
            conversation = self._conversations[journey_id]
            results.append(
                RetrievedJourney(
                    journey_id=journey_id,
                    rank=rank,
                    retrieval_score=score,
                    source_message_ids=tuple(message.message_id for message in conversation.messages),
                )
            )
        return results

    def conversation(self, journey_id: str) -> CanonicalConversation:
        try:
            return self._conversations[journey_id]
        except KeyError as exc:
            raise KeyError(f"journey is not in the development index: {journey_id}") from exc

    def _scores(self, query: str) -> list[float]:
        if self._vectorizer is not None:
            return cosine_similarity(self._vectorizer.transform([query]), self._matrix)[0].tolist()
        query_vector = _fallback_vector(query)
        return [_cosine(query_vector, document_vector) for document_vector in self._fallback_vectors or []]


def _read_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _fallback_vector(text: str) -> dict[str, float]:
    tokens = TOKEN_RE.findall(text.casefold())
    counts = Counter(tokens)
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {token: count / norm for token, count in counts.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    return sum(value * right.get(token, 0.0) for token, value in left.items())
