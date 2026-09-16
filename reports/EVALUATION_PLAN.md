# Evaluation Plan

## Purpose

Measure whether the support agent understands SpotifyCares journeys, selects historically supported next actions, avoids repeating failed advice, drafts grounded replies, and escalates risky cases appropriately.

## Data boundaries

- Development retrieval and tuning: `data/processed/spotify_development.jsonl`.
- Reserved human candidates: `data/processed/golden_annotation_candidates.jsonl`.
- Human annotation input: `data/annotations/<annotator_id>.jsonl`.
- Final golden data must be created only from validated human annotations.
- Golden journey IDs must never enter retrieval, baseline fitting, or threshold tuning.

## Metrics

Intent:

- Accuracy
- Macro-F1

State:

- Accuracy
- Macro-F1

Next action:

- Accuracy
- Macro-F1 where labels are comparable
- Top-k accuracy may be added when action alternatives are retained

Escalation:

- Precision
- Recall
- F1

Operational and evidence metrics:

- `repeated_failed_action_rate`: selected actions that were already reported failed.
- `evidence_coverage`: important case facts represented by supporting journeys.
- `transition_consistency`: agreement among comparable historical transitions.
- `response_groundedness`: judge/human rubric score and validator warnings.

No metric is reported as a result until human labels or a documented human review subset exists.

## Baselines

1. **Trivial baseline:** majority intent/action/escalation fitted only from real labeled development records. It currently refuses to fit because the development pool is unlabeled.
2. **Simple baseline:** lexical intent and state extraction plus deterministic action rules, without historical retrieval.
3. **Structured agent:** explicit case state, journey retrieval, transition evidence, failed-action protection, policy escalation, and grounded response drafting.

## LLM judge

The optional judge scores groundedness, action alignment, relevance, safety, clarity, and escalation appropriateness on a fixed 1-5 rubric. It must not see labels that would leak the metric under review. Provider absence returns `NOT_AVAILABLE`; malformed output is rejected.

## Human agreement

A double-annotated subset will be compared using Cohen's kappa for categorical fields, Jaccard for multilabel reason codes, adjudication rate, and exclusion rate. No agreement number will be reported until shared human annotations exist.

## Leakage checks

Before final evaluation:

- validate candidate membership and duplicate annotation IDs;
- check golden IDs against development IDs;
- construct retrieval with the golden candidate IDs excluded;
- preserve conversation-level split membership;
- document that semantic near-duplicate detection is not implemented in the prepared split.

## Reproducibility

Run the deterministic tests with:

```powershell
python -m pytest -q
python src/annotation_tool.py --self-test
python -m src.agent.cli --demo
python -m src.evaluation.evaluate
```

The last command reports readiness or measured metrics based on existing human annotation files. It must not create labels.

## Current status

- Human golden set: NOT YET COMPLETE.
- Headline metrics: NOT YET MEASURED.
- Human-versus-judge agreement: NOT READY.
- Failure analysis: signal tooling implemented; confirmed failures require human-grounded evaluation.
