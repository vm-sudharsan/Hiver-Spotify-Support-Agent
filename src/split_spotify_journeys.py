"""Create and validate leakage-safe development and golden-candidate pools."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path("data/processed/spotify_journeys.jsonl")
DEFAULT_DEVELOPMENT = Path("data/processed/spotify_development.jsonl")
DEFAULT_GOLDEN = Path("data/processed/spotify_golden_candidates.jsonl")
DEFAULT_MANIFEST = Path("data/processed/spotify_split_manifest.json")
DEFAULT_SEED = 20260915
GOLDEN_RATIO = 0.20


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    journeys: list[dict[str, Any]] = []
    raw_lines: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                journey = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
            if not isinstance(journey, dict) or not journey.get("journey_id"):
                raise ValueError(f"Missing journey_id at {path}:{line_number}")
            journeys.append(journey)
            raw_lines.append(line.rstrip("\r\n"))
    return journeys, raw_lines


class UnionFind:
    def __init__(self, values: list[str]) -> None:
        self.parent = {value: value for value in values}
        self.rank = {value: 0 for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def grouping(journeys: list[dict[str, Any]]) -> dict[str, str]:
    journey_ids = [journey["journey_id"] for journey in journeys]
    if len(journey_ids) != len(set(journey_ids)):
        raise ValueError("Source journey_id values are not unique")
    union_find = UnionFind(journey_ids)
    signature_owner: dict[str, str] = {}
    for journey in journeys:
        metadata = journey.get("duplicate_leakage_metadata") or {}
        signatures = (
            ("exact", metadata.get("journey_signature_exact_hash")),
            ("normalized", metadata.get("journey_signature_normalized_hash")),
        )
        for signature_type, signature in signatures:
            if not signature:
                raise ValueError(f"Missing {signature_type} journey signature in {journey['journey_id']}")
            token = f"{signature_type}:{signature}"
            previous = signature_owner.get(token)
            if previous is None:
                signature_owner[token] = journey["journey_id"]
            else:
                union_find.union(journey["journey_id"], previous)

    members: defaultdict[str, list[str]] = defaultdict(list)
    for journey_id in journey_ids:
        members[union_find.find(journey_id)].append(journey_id)
    group_keys = {
        root: hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()
        for root, ids in members.items()
    }
    return {journey_id: group_keys[union_find.find(journey_id)] for journey_id in journey_ids}


def assign_splits(
    journeys: list[dict[str, Any]], group_keys: dict[str, str], seed: int
) -> tuple[set[str], set[str], int]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for journey in journeys:
        groups[group_keys[journey["journey_id"]]].append(journey["journey_id"])
    ordered_groups = sorted(groups.items())
    random.Random(seed).shuffle(ordered_groups)
    target = round(len(journeys) * GOLDEN_RATIO)
    golden_ids: set[str] = set()
    for group_key, member_ids in ordered_groups:
        if len(golden_ids) >= target and golden_ids:
            break
        golden_ids.update(member_ids)
    all_ids = {journey["journey_id"] for journey in journeys}
    return all_ids - golden_ids, golden_ids, target


def write_jsonl(path: Path, journeys: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for journey in journeys:
            handle.write(json.dumps(journey, ensure_ascii=False, sort_keys=True) + "\n")


def validate(
    source: list[dict[str, Any]],
    development: list[dict[str, Any]],
    golden: list[dict[str, Any]],
    group_keys: dict[str, str],
    source_raw: list[str],
    development_path: Path,
    golden_path: Path,
    seed: int,
) -> dict[str, Any]:
    source_by_id = {journey["journey_id"]: journey for journey in source}
    development_ids = {journey["journey_id"] for journey in development}
    golden_ids = {journey["journey_id"] for journey in golden}
    if development_ids & golden_ids:
        raise ValueError("A journey_id occurs in both partitions")
    if development_ids | golden_ids != set(source_by_id):
        raise ValueError("Partition IDs do not match source IDs")
    development_groups = {group_keys[journey_id] for journey_id in development_ids}
    golden_groups = {group_keys[journey_id] for journey_id in golden_ids}
    if development_groups & golden_groups:
        raise ValueError("A duplicate grouping key occurs in both partitions")
    if len(development) + len(golden) != len(source):
        raise ValueError("Partition counts do not match source count")

    for partition, path in ((development, development_path), (golden, golden_path)):
        on_disk, _ = read_jsonl(path)
        if on_disk != partition:
            raise ValueError(f"Output records do not match expected source records: {path}")
        for journey in partition:
            source_journey = source_by_id[journey["journey_id"]]
            if journey != source_journey:
                raise ValueError(f"Journey content changed for {journey['journey_id']}")
            if journey["messages"] != source_journey["messages"]:
                raise ValueError(f"Message provenance changed for {journey['journey_id']}")

    recomputed_groups = grouping(source)
    expected_development, expected_golden, _ = assign_splits(source, recomputed_groups, seed)
    if expected_development != development_ids or expected_golden != golden_ids:
        raise ValueError("Split is not deterministic for the supplied seed")
    source_digest = hashlib.sha256("\n".join(source_raw).encode("utf-8")).hexdigest()
    return {
        "journey_id_disjoint": True,
        "group_key_disjoint": True,
        "counts_match_source": True,
        "records_trace_to_source": True,
        "message_provenance_preserved": True,
        "deterministic_for_seed": True,
        "golden_excluded_from_development": True,
        "source_jsonl_sha256": source_digest,
    }


def duplicate_statistics(journeys: list[dict[str, Any]], group_keys: dict[str, str]) -> dict[str, int]:
    exact = Counter(
        (journey.get("duplicate_leakage_metadata") or {}).get("journey_signature_exact_hash")
        for journey in journeys
    )
    normalized = Counter(
        (journey.get("duplicate_leakage_metadata") or {}).get("journey_signature_normalized_hash")
        for journey in journeys
    )
    sizes = Counter(group_keys.values())
    return {
        "exact_duplicate_signature_families": sum(count > 1 for count in exact.values()),
        "exact_duplicate_signature_journeys": sum(count for count in exact.values() if count > 1),
        "normalized_duplicate_signature_families": sum(count > 1 for count in normalized.values()),
        "normalized_duplicate_signature_journeys": sum(count for count in normalized.values() if count > 1),
        "group_count": len(sizes),
        "singleton_group_count": sum(size == 1 for size in sizes.values()),
        "multi_member_group_count": sum(size > 1 for size in sizes.values()),
        "largest_group_size": max(sizes.values(), default=0),
    }


def heuristic_pool_statistics(journeys: list[dict[str, Any]]) -> dict[str, Any]:
    flag_names = (
        "failure_marker_flag",
        "question_marker_flag",
        "diagnostic_context_marker_flag",
        "dm_handoff_marker_flag",
        "resolution_marker_flag",
    )
    return {
        "multi_turn_journeys": sum(bool(journey.get("multi_turn")) for journey in journeys),
        "single_or_short_journeys": sum(not bool(journey.get("multi_turn")) for journey in journeys),
        "reconstruction_status": dict(sorted(Counter(journey.get("reconstruction_status") for journey in journeys).items())),
        "journeys_with_heuristic_flag": {
            name: sum(bool((journey.get("heuristic_metadata") or {}).get(name)) for journey in journeys)
            for name in flag_names
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--development", type=Path, default=DEFAULT_DEVELOPMENT)
    parser.add_argument("--golden-candidates", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    source, source_raw = read_jsonl(args.source)
    group_keys = grouping(source)
    development_ids, golden_ids, target = assign_splits(source, group_keys, args.seed)
    by_id = {journey["journey_id"]: journey for journey in source}
    development = [journey for journey in source if journey["journey_id"] in development_ids]
    golden = [journey for journey in source if journey["journey_id"] in golden_ids]
    write_jsonl(args.development, development)
    write_jsonl(args.golden_candidates, golden)
    validation = validate(
        source,
        development,
        golden,
        group_keys,
        source_raw,
        args.development,
        args.golden_candidates,
        args.seed,
    )
    manifest = {
        "split_version": "spotify_group_split_v1",
        "random_seed": args.seed,
        "source_dataset": str(args.source),
        "development_dataset": str(args.development),
        "golden_candidate_dataset": str(args.golden_candidates),
        "total_journeys": len(source),
        "development_count": len(development),
        "golden_candidate_count": len(golden),
        "target_golden_candidate_count": target,
        "observed_golden_candidate_ratio": round(len(golden) / len(source), 6) if source else 0,
        "grouping_method": "connected components of shared exact or normalized journey signature hashes",
        "semantic_near_duplicate_detection": "not_implemented; no semantic similarity claim",
        "grouping_statistics": duplicate_statistics(source, group_keys),
        "duplicate_family_statistics": duplicate_statistics(source, group_keys),
        "golden_candidate_heuristic_metadata_statistics": heuristic_pool_statistics(golden),
        "validation": validation,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()