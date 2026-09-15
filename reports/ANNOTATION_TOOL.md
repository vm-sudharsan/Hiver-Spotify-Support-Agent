# Local Annotation Tool

## Start

From `D:\Hiver`:

```powershell
python src/annotation_tool.py
```

Open `http://127.0.0.1:8765/`. Use a separate ID such as `annotator_1` or `annotator_2`; each ID writes to its own file under `data/annotations/`.

## Annotate and Resume

Choose the evaluation-point customer message, review the complete chronological conversation, and fill the annotation panel manually. Save writes or updates one record without overwriting other journeys. Closing and restarting the server resumes from the saved JSONL file. Previous, Next, Jump to example, and completed-count navigation are available.

The interface warns that current intent/state must use only the current customer message and preceding context. Future support replies are for observed next action and later outcome only. No model prediction, retrieval result, similarity score, or prefilled ground-truth label is shown.

## Storage and Export

Annotations are stored as newline-delimited JSON in:

```text
data/annotations/<annotator_id>.jsonl
```

Records preserve journey and root IDs, evaluation-point message provenance, ordered missing-information entries, ordered attempted actions, taxonomy fields, uncertainty, confidence, notes, and audit timestamps. The `Export` button downloads the selected annotator's complete JSONL file.

The server validates frozen intent/state/action vocabularies, required statuses, confidence and ambiguity rules, source membership, root IDs, and candidate provenance before saving. `ideal_next_action` remains optional as specified by the guide.

## Two Annotators

Set different annotator IDs. Files are isolated, for example `annotator_1.jsonl` and `annotator_2.jsonl`; they are never merged by the tool. A later adjudication process can compare those independent records or select a double-annotation subset.

## Intentional Boundaries

This tool only supports human annotation. It does not infer or suggest intent, state, action, outcome, escalation, or confidence. It does not build an agent, retrieval system, classifier, embedding index, or final locked golden set. Heuristic source metadata remains context only and is not displayed as a prediction.