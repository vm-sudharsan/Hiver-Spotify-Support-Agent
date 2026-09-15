# SpotifyCares Evaluation Split

## Purpose

This split reserves a leakage-aware pool for future human annotation. It does not create annotations, assign taxonomy labels, or create the final 200-example golden set.

The split was created from `data/processed/spotify_journeys.jsonl` with `src/split_spotify_journeys.py`.

## Why Group-Level Splitting Is Necessary

An exact or obvious normalized duplicate must remain in one evaluation partition. Splitting individual journeys without first forming duplicate groups could place the same conversation content in development and golden candidates, inflating evaluation results.

The implementation builds connected components from shared existing journey-level `journey_signature_exact_hash` or `journey_signature_normalized_hash` values. Assignment is then made to whole groups using a fixed random seed. The golden-candidate pool is completely excluded from development.

## What the Grouping Detects

The grouping uses only metadata already produced by the journey pipeline:

- exact ordered role/text journey signatures;
- normalized ordered role/text signatures using Unicode normalization, case folding, and whitespace normalization.

It does not claim semantic near-duplicate detection. It does not use embeddings, an LLM, external ML libraries, or an invented similarity heuristic. Semantically similar but textually different or template-related journeys may therefore remain in different groups. This is a known leakage limitation.

## Split Configuration and Results

- Split version: `spotify_group_split_v1`
- Random seed: `20260915`
- Target: 80% development, 20% golden candidates at group level
- Source journeys: `24,568`
- Development journeys: `19,654`
- Golden candidates: `4,914`
- Observed golden-candidate ratio: `20.0016%`

The one-journey difference from an exact percentage is caused by the integer target. The current duplicate structure does not require rounding around multi-member groups, because all observed groups are singletons.

### Grouping statistics

| Metric | Count |
|---|---:|
| Exact duplicate signature families | 0 |
| Journeys in exact duplicate families | 0 |
| Normalized duplicate signature families | 0 |
| Journeys in normalized duplicate families | 0 |
| Total grouping keys | 24,568 |
| Singleton groups | 24,568 |
| Multi-member groups | 0 |
| Largest group | 1 |

Heuristic metadata in the golden-candidate pool is retained only to support later deliberate sampling. It is not ground truth. The pool contains 1,202 multi-turn journeys, 3,712 single/short journeys, 513 failure-marker journeys, 2,134 DM-handoff-marker journeys, and 203 resolution-marker journeys. These flags do not establish intent, state, action, outcome, escalation, or resolution.

## Validation

The split utility validated:

1. No `journey_id` occurs in both partitions.
2. No grouping key occurs in both partitions.
3. Partition counts equal the source count.
4. Every output record matches a source record by `journey_id` and full JSON content.
5. Message arrays and source provenance are unchanged.
6. Recomputed assignment is identical for seed `20260915`.
7. Golden candidates are excluded from development.

All checks passed. The utility was run twice; SHA-256 hashes for both JSONL outputs and the split manifest were identical across runs.

## Known Limitations

The source pipeline's exact and normalized signatures cannot identify semantic near-duplicates, paraphrases, shared support templates with changed customer text, or duplicate families absent from the metadata. The split is therefore leakage-safe for the duplicate definitions available today, not a guarantee against every form of content similarity.

The heuristic flags are noisy textual markers. They are useful for planning future sampling coverage but must not be treated as human labels.

## Why the Final Golden Set Is Not Created

The `4,914` records are a reserved candidate pool, not the final evaluation set. Human selection and annotation should happen later using the annotation guide, with deliberate coverage across journey structure and visible outcome patterns. No labels or final 200-example sample have been created in this step.