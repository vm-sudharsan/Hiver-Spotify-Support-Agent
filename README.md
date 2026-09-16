# Hiver Spotify Support Agent

Hiver SDE Intern take-home implementation for a SpotifyCares support decision agent.

## Core idea

This is not generic message-to-RAG answering. The system models:

```text
historical support journeys
        -> current case state
        -> attempted and failed actions
        -> historical transition evidence
        -> next best support action
        -> grounded response
        -> auto-handle or escalate
```

## Current implementation

- Frozen 10-intent, 9-state, 13-action taxonomy.
- Explicit `CaseState` and action ledger.
- Development-only TF-IDF journey retrieval.
- Transition evidence and failed-action protection.
- Deterministic next-action and escalation policies.
- Grounded response fallback without an LLM.
- Optional structured LLM provider and judge.
- CLI demo, traces, evaluation metrics, agreement, QC, and failure signals.
- Manual browser annotation tool for the reserved golden candidates.

## Setup

Python 3.12 is supported. Install the small project dependencies used by the environment as needed; the deterministic path uses the standard library and `scikit-learn` when available.

Optional provider configuration can be copied from `.env.example` into the process environment. Never commit `.env` or API keys.

## Run the demo

```powershell
python -m src.agent.cli --demo
python -m src.agent.cli --demo --json
```

The demo prints case understanding, attempted actions, historical evidence, next action, escalation, and draft reply.

## Human annotation

```powershell
python src/annotation_tool.py
```

Open `http://127.0.0.1:8765/`. The tool is manual: it does not prefill model predictions or show retrieval results. Annotations are stored separately by annotator under `data/annotations/`.

## Evaluation

```powershell
python -m src.evaluation.evaluate
python -m pytest -q
python src/annotation_tool.py --self-test
```

Evaluation validates annotation schema and leakage boundaries first. It reports `NOT_READY` or `NOT YET MEASURED` when human data is insufficient. It never labels the golden set automatically.

## Data and leakage

Development data is `data/processed/spotify_development.jsonl`. Reserved candidates are `data/processed/spotify_golden_candidates.jsonl`; the 240 annotation candidates are `data/processed/golden_annotation_candidates.jsonl`. Golden candidates are excluded from retrieval and tuning.

The raw dataset is read-only and ignored by Git. Exact and normalized duplicate grouping is implemented; semantic near-duplicate detection remains a documented limitation.

## Reports

- [Architecture](reports/ARCHITECTURE.md)
- [Evaluation plan](reports/EVALUATION_PLAN.md)
- [Decision log](reports/DECISION_LOG.md)
- [Final report skeleton](reports/FINAL_REPORT.md)

## Current results

Headline metrics, final golden-set size, judge scores, human agreement, and failure counts are **NOT YET MEASURED**. No result is invented in the repository.

## Scope boundary

The agent is designed for triage and next-action recommendation. It does not access accounts, process payments/refunds, claim current catalog policy, or autonomously close cases whose outcomes are not visible.
