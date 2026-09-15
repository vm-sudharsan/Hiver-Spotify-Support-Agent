# SpotifyCares Golden Annotation Candidate Sampling

## Purpose

This step creates a reproducible pool of `240` annotation candidates from the already isolated `4,914`-journey golden-candidate pool. These are not annotations and are not the final golden evaluation set. The additional candidates provide room for later exclusions, ambiguity, quality control, and adjudication before selecting approximately 200 labelled examples.

The sampler is implemented in `src/sample_golden_candidates.py` and does not alter either source split.

## Why Random Sampling Alone Is Insufficient

Pure random sampling would mostly reproduce the dominant source distribution: single-turn, complete journeys with question markers. It could underrepresent long multi-turn context, partial reconstructions, failures, apparent resolution markers, and DM/handoff situations that are important for evaluating state tracking and escalation decisions.

The sampler therefore fixes coverage across observable structural dimensions and uses deterministic lexical novelty as a tie-breaker. It retains common cases as well as deliberately oversampled difficult-looking cases. The dimensions are sampling metadata only; they are not labels.

## Observable Sampling Dimensions

Only fields present in the candidate records are used:

- length bucket from `message_count`: single-turn (`<=2` messages), short multi-turn (`3-4`), medium multi-turn (`5-8`), and long multi-turn (`>=9`);
- `reconstruction_status`;
- `failure_marker_flag`;
- `dm_handoff_marker_flag`;
- `resolution_marker_flag`;
- `diagnostic_context_marker_flag`;
- `question_marker_flag`;
- lexical token novelty from the preserved message text, used only as a deterministic tie-breaker.

There is no separate reliable `monitoring` or `improvement` field in the source metadata. Resolution markers are only apparent textual indicators and do not establish resolution or monitoring. No intent, state, action, outcome, escalation, or other taxonomy label is assigned.

## Sampling Method

- Source: `data/processed/spotify_golden_candidates.jsonl`
- Candidate pool size: `4,914`
- Selected candidates: `240`
- Unused candidates: `4,674`
- Fixed random seed: `20260916`
- Output: `data/processed/golden_annotation_candidates.jsonl`

The sampler uses exact length quotas of 72, 60, 60, and 48. It then greedily favors records that satisfy unmet secondary coverage targets. Overlapping dimensions are not mutually exclusive, so actual secondary counts can exceed their target minimums. Inverse-frequency token novelty breaks comparable choices and broadens lexical coverage without embeddings or semantic similarity.

### Target and actual counts

| Dimension | Target | Actual |
|---|---:|---:|
| Single-turn | 72 | 72 |
| Short multi-turn | 60 | 60 |
| Medium multi-turn | 60 | 60 |
| Long multi-turn | 48 | 48 |
| Complete reconstruction | 210 | 210 |
| Partial reconstruction | 30 | 30 |
| Failure marker present | 50 | 61 |
| DM/handoff marker present | 60 | 94 |
| Resolution marker present | 30 | 35 |
| Diagnostic marker present | 60 | 115 |
| Question marker present | 190 | 212 |

The target counts for secondary dimensions are minimum coverage goals in an overlapping greedy design, not disjoint cells. They are intentionally not interpreted as truth about the underlying support journey.

## Leakage Prevention

Every selected record is read only from the reserved golden-candidate JSONL. Validation checks that no selected `journey_id` occurs in development, every selected ID exists in the reserved pool, and full journey content, message arrays, and provenance fields match the source record. The upstream group-level split already isolated duplicate grouping keys from development; this sampler does not recompute or weaken that boundary.

## Validation Results

All checks passed:

1. Every selected journey exists in the reserved candidate pool.
2. No selected journey exists in the development pool.
3. `journey_id` values are unique.
4. `root_tweet_id` values are unique.
5. Journey content and message provenance are unchanged.
6. The output is valid JSONL.
7. Re-running with seed `20260916` reproduces the same selection.
8. Actual stratum counts match the generated manifest.

The sampler was run twice. SHA-256 hashes for the selected JSONL and manifest were identical across runs.

## Limitations and Next Step

The heuristic flags are noisy text markers with false positives and false negatives. They do not detect semantic diversity reliably, and they do not label intent, state, action, outcome, escalation, resolution, or monitoring. Length buckets are operational definitions based on message count rather than human judgments of conversation complexity. Because the source has no monitoring/improvement ground-truth field, that dimension cannot be independently stratified here.

The next step is human annotation of these candidates according to `ANNOTATION_GUIDE.md`, followed by quality control, exclusion of unusable or ambiguous examples as appropriate, adjudication, and deliberate selection of the final approximately 200-example golden set.