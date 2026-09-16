"""Freeze a final golden file from validated human annotations only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .validate_annotations import read_jsonl, validate_annotations

ROOT = Path(__file__).resolve().parents[2]


def freeze_golden(
    annotation_path: Path,
    candidates_path: Path,
    development_path: Path,
    output_path: Path,
    manifest_path: Path,
    *,
    annotation_version: str = "v1",
    min_count: int = 150,
) -> dict[str, Any]:
    validation = validate_annotations(annotation_path, candidates_path, development_path)
    annotations = read_jsonl(annotation_path) if annotation_path.exists() else []
    included = [record for record in annotations if record.get("exclude_from_golden") != "yes"]
    if not validation.get("ok"):
        if any("development data" in error for error in validation.get("errors", [])):
            raise ValueError("golden/development overlap detected during annotation validation")
        raise ValueError(f"annotations are not valid: {validation.get('errors', [])}")
    if not included:
        raise ValueError("cannot freeze an empty golden set")
    if len(included) < min_count:
        raise ValueError(f"golden set has {len(included)} included records; minimum is {min_count}")
    development_ids = {record.get("journey_id") for record in read_jsonl(development_path)}
    included_ids = [record.get("journey_id") for record in included]
    overlap = set(included_ids) & development_ids
    if overlap:
        raise ValueError(f"golden/development overlap detected: {sorted(overlap)[:3]}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in included), encoding="utf-8")
    manifest = {
        "annotation_version": annotation_version,
        "source_annotation_file": str(annotation_path),
        "candidate_file": str(candidates_path),
        "development_file": str(development_path),
        "included_count": len(included),
        "excluded_count": len(annotations) - len(included),
        "included_journey_ids": included_ids,
        "excluded_journey_ids": [record.get("journey_id") for record in annotations if record.get("exclude_from_golden") == "yes"],
        "annotators": sorted({record.get("annotator_id") for record in included if record.get("annotator_id")}),
        "qc_status": "validated_human_annotations",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--min-count", type=int, default=150)
    args = parser.parse_args()
    print(json.dumps(freeze_golden(args.annotations, args.candidates, args.development, args.output, args.manifest, min_count=args.min_count), indent=2))


if __name__ == "__main__":
    main()
