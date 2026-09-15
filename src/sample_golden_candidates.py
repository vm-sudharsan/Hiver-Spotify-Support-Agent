"""Select a reproducible, stratified annotation-candidate sample."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any, Callable


DEFAULT_SOURCE = Path("data/processed/spotify_golden_candidates.jsonl")
DEFAULT_DEVELOPMENT = Path("data/processed/spotify_development.jsonl")
DEFAULT_OUTPUT = Path("data/processed/golden_annotation_candidates.jsonl")
DEFAULT_MANIFEST = Path("data/processed/golden_sampling_manifest.json")
DEFAULT_SEED = 20260916
TARGET_COUNT = 240
TOKEN_RE = re.compile(r"[a-z0-9]+")

LENGTH_TARGETS = {
    "single_turn": 72,
    "short_multi_turn": 60,
    "medium_multi_turn": 60,
    "long_multi_turn": 48,
}
SECONDARY_TARGETS = {
    "reconstruction_status": {"complete": 210, "partial": 30},
    "failure_marker": {True: 50},
    "dm_handoff_marker": {True: 60},
    "resolution_marker": {True: 30},
    "diagnostic_context_marker": {True: 60},
    "question_marker": {True: 190},
}


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    raw_lines: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
            if not isinstance(record, dict) or not record.get("journey_id"):
                raise ValueError(f"Missing journey_id at {path}:{line_number}")
            records.append(record)
            raw_lines.append(line.rstrip("\r\n"))
    return records, raw_lines


def length_bucket(record: dict[str, Any]) -> str:
    message_count = record["message_count"]
    if message_count <= 2:
        return "single_turn"
    if message_count <= 4:
        return "short_multi_turn"
    if message_count <= 8:
        return "medium_multi_turn"
    return "long_multi_turn"


def observable_dimensions(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("heuristic_metadata") or {}
    return {
        "length_bucket": length_bucket(record),
        "reconstruction_status": record.get("reconstruction_status"),
        "failure_marker": bool(metadata.get("failure_marker_flag")),
        "dm_handoff_marker": bool(metadata.get("dm_handoff_marker_flag")),
        "resolution_marker": bool(metadata.get("resolution_marker_flag")),
        "diagnostic_context_marker": bool(metadata.get("diagnostic_context_marker_flag")),
        "question_marker": bool(metadata.get("question_marker_flag")),
    }


def tokens(record: dict[str, Any]) -> set[str]:
    text = " ".join(message.get("text", "") for message in record.get("messages", []))
    return set(TOKEN_RE.findall(text.casefold()))


def stable_tie(record: dict[str, Any], seed: int) -> float:
    digest = hashlib.sha256(f"{seed}:{record['journey_id']}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def available_counts(records: list[dict[str, Any]]) -> dict[str, Counter]:
    dimensions = [observable_dimensions(record) for record in records]
    return {
        "length_bucket": Counter(item["length_bucket"] for item in dimensions),
        "reconstruction_status": Counter(item["reconstruction_status"] for item in dimensions),
        "failure_marker": Counter(item["failure_marker"] for item in dimensions),
        "dm_handoff_marker": Counter(item["dm_handoff_marker"] for item in dimensions),
        "resolution_marker": Counter(item["resolution_marker"] for item in dimensions),
        "diagnostic_context_marker": Counter(item["diagnostic_context_marker"] for item in dimensions),
        "question_marker": Counter(item["question_marker"] for item in dimensions),
    }


def select(records: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    if sum(LENGTH_TARGETS.values()) != TARGET_COUNT:
        raise ValueError("Length targets must sum to the requested sample size")
    dimensions = {record["journey_id"]: observable_dimensions(record) for record in records}
    record_tokens = {record["journey_id"]: tokens(record) for record in records}
    frequencies = Counter(token for values in record_tokens.values() for token in values)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_tokens: set[str] = set()
    counts = {name: Counter() for name in SECONDARY_TARGETS}
    length_counts = Counter()
    remaining = {record["journey_id"]: record for record in records}

    while len(selected) < TARGET_COUNT:
        eligible = [
            record
            for record in remaining.values()
            if length_counts[dimensions[record["journey_id"]]["length_bucket"]]
            < LENGTH_TARGETS[dimensions[record["journey_id"]]["length_bucket"]]
        ]
        if not eligible:
            raise ValueError("Insufficient records to satisfy length targets")

        def score(record: dict[str, Any]) -> tuple[float, float, float]:
            journey_id = record["journey_id"]
            item = dimensions[journey_id]
            coverage_score = 0.0
            for dimension, targets in SECONDARY_TARGETS.items():
                value = item[dimension]
                target = targets.get(value, 0)
                if target and counts[dimension][value] < target:
                    coverage_score += 10.0 + (target - counts[dimension][value]) / target
            novelty = sum(
                1.0 / frequencies[token]
                for token in record_tokens[journey_id]
                if token not in selected_tokens
            )
            commonness_balance = 1.0 if item["reconstruction_status"] == "complete" else 0.0
            return coverage_score, novelty, commonness_balance

        chosen = max(eligible, key=lambda record: (*score(record), stable_tie(record, seed)))
        journey_id = chosen["journey_id"]
        item = dimensions[journey_id]
        selected.append(chosen)
        selected_ids.add(journey_id)
        del remaining[journey_id]
        length_counts[item["length_bucket"]] += 1
        for dimension in SECONDARY_TARGETS:
            counts[dimension][item[dimension]] += 1
        selected_tokens.update(record_tokens[journey_id])

    return selected


def stratum_counts(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    dimensions = [observable_dimensions(record) for record in records]
    result: dict[str, dict[str, int]] = {}
    for name in ("length_bucket", "reconstruction_status", "failure_marker", "dm_handoff_marker", "resolution_marker", "diagnostic_context_marker", "question_marker"):
        result[name] = {str(value): count for value, count in sorted(Counter(item[name] for item in dimensions).items(), key=lambda pair: str(pair[0]))}
    return result


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def validate(
    source: list[dict[str, Any]],
    development: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    output: Path,
    seed: int,
) -> dict[str, Any]:
    source_by_id = {record["journey_id"]: record for record in source}
    development_ids = {record["journey_id"] for record in development}
    selected_ids = [record["journey_id"] for record in selected]
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("Selected journey_id is duplicated")
    if len({record["root_tweet_id"] for record in selected}) != len(selected):
        raise ValueError("Selected root_tweet_id is duplicated")
    if not set(selected_ids) <= set(source_by_id):
        raise ValueError("Selected journey is not in the reserved candidate pool")
    if set(selected_ids) & development_ids:
        raise ValueError("Selected journey is in the development pool")
    on_disk, _ = read_jsonl(output)
    if on_disk != selected:
        raise ValueError("Output records differ from selected records")
    for record in selected:
        source_record = source_by_id[record["journey_id"]]
        if record != source_record or record["messages"] != source_record["messages"]:
            raise ValueError(f"Journey content or provenance changed: {record['journey_id']}")
    rerun = select(source, seed)
    if rerun != selected:
        raise ValueError("Selection is not deterministic for the supplied seed")
    actual_strata = stratum_counts(selected)
    return {
        "selected_in_reserved_pool": True,
        "excluded_from_development": True,
        "journey_ids_unique": True,
        "root_tweet_ids_unique": True,
        "content_and_provenance_preserved": True,
        "valid_jsonl": True,
        "deterministic_for_seed": True,
        "actual_stratum_counts": actual_strata,
        "stratum_counts_match_manifest": True,
        "selected_count": len(selected),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--development", type=Path, default=DEFAULT_DEVELOPMENT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    source, source_raw = read_jsonl(args.source)
    development, _ = read_jsonl(args.development)
    if len(source) < TARGET_COUNT:
        raise ValueError("Reserved candidate pool is smaller than requested sample")
    selected = select(source, args.seed)
    write_jsonl(args.output, selected)
    validation = validate(source, development, selected, args.output, args.seed)
    actual_counts = stratum_counts(selected)
    if validation["actual_stratum_counts"] != actual_counts:
        raise ValueError("Validated stratum counts differ from manifest counts")
    manifest = {
        "sampling_version": "spotify_golden_annotation_sampling_v1",
        "source_file": str(args.source),
        "development_file": str(args.development),
        "output_file": str(args.output),
        "candidate_pool_size": len(source),
        "selected_candidate_count": len(selected),
        "unused_candidate_count": len(source) - len(selected),
        "random_seed": args.seed,
        "sampling_dimensions": [
            "length_bucket: message_count <=2, 3-4, 5-8, >=9",
            "reconstruction_status",
            "failure_marker_flag",
            "dm_handoff_marker_flag",
            "resolution_marker_flag",
            "diagnostic_context_marker_flag",
            "question_marker_flag",
            "lexical token novelty tie-breaker",
        ],
        "target_counts_per_stratum": {
            "length_bucket": LENGTH_TARGETS,
            "reconstruction_status": SECONDARY_TARGETS["reconstruction_status"],
            "failure_marker": {"true": 50},
            "dm_handoff_marker": {"true": 60},
            "resolution_marker": {"true": 30},
            "diagnostic_context_marker": {"true": 60},
            "question_marker": {"true": 190},
        },
        "actual_counts_per_stratum": actual_counts,
        "available_source_counts_per_stratum": {
            name: {str(value): count for value, count in counter.items()}
            for name, counter in available_counts(source).items()
        },
        "selection_methodology": "fixed length quotas, deterministic greedy coverage of secondary observable targets, and inverse-frequency lexical novelty tie-breaking; no labels inferred",
        "heuristic_metadata_is_ground_truth": False,
        "monitoring_improvement_metadata_available": False,
        "source_jsonl_sha256": hashlib.sha256("\n".join(source_raw).encode("utf-8")).hexdigest(),
        "validation": validation,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()