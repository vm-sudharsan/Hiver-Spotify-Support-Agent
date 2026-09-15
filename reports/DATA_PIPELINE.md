# SpotifyCares Journey Data Pipeline

## Scope

This pipeline prepares a reproducible pool of reconstructed SpotifyCares support journeys for later annotation, retrieval, and evaluation. It does not assign the frozen taxonomy labels, create the golden evaluation set, build an agent, create embeddings, create a vector database, call an LLM, or modify the raw dataset.

The primary unit is a reconstructed support journey rather than an isolated tweet.

## Input dataset

- **Source:** `data/raw/archive/twcs.csv`
- **Rows processed:** 2,811,774
- **Columns:** `tweet_id`, `author_id`, `inbound`, `created_at`, `text`, `response_tweet_id`, `in_response_to_tweet_id`
- **Customer/inbound rows:** 1,537,843
- **Support/outbound rows:** 1,273,931
- **Observed date range:** 2008-05-08 through 2017-12-03
- **Raw-data handling:** read-only; the source file was not modified, moved, renamed, or deleted.

The script reads the CSV with Python's standard-library `csv` reader and processes it into bounded batches. It builds a temporary SQLite index on disk rather than loading the raw file into memory.

## SpotifyCares filtering approach

The filter reuses the validated definition in `src/explore_dataset.py` and the existing exploration report:

1. A root is an inbound customer message with an empty in-file `in_response_to_tweet_id`.
2. Its `response_tweet_id` must point to an in-file outbound message.
3. That outbound root reply must have `author_id = SpotifyCares`.
4. Descendants are followed using `in_response_to_tweet_id`.

This produced **24,568 reconstructable SpotifyCares roots**, matching the previously reported SpotifyCares thread count.

The support account identifier is taken from the source `author_id` field. The output labels the journey brand as `SpotifyCares` because that is the selected project account; no text-based brand inference is introduced.

## Conversation reconstruction method

The script stores all source rows in a temporary SQLite table keyed by `tweet_id`, with indexes for parent and response relationships. For each qualifying root, a recursive query follows child messages where:

```text
child.in_response_to_tweet_id = current.tweet_id
```

Traversal is capped at depth 100, matching the validated exploration logic. Cycles are blocked by a path check. Only relationships present in the source index are followed. The script never invents a parent, response, message ID, or missing intermediate message.

Each journey is then ordered deterministically by parsed timestamp, original timestamp text, and `tweet_id`. Each message retains its original relationship fields, even when those fields point outside the reconstructed journey.

## Reconstruction status

Each journey receives one of:

- `complete`: no missing relationship target or detected reconstruction issue within the retained chain, and the depth limit was not reached.
- `partial`: a relationship target is missing, a retained message has a non-reciprocal relationship signal, or the traversal reaches the depth limit.
- `uncertain`: reserved for relationship inconsistencies that cannot be conservatively represented as merely partial.

The latest run produced:

| Reconstruction status | Journeys |
|---|---:|
| `complete` | 23,466 |
| `partial` | 1,102 |
| `uncertain` | 0 |
| **Total** | **24,568** |

The zero `uncertain` count is a result of this source and conservative classification, not an assumption that all relationships are complete.

## Output files

### Journey dataset

`data/processed/spotify_journeys.jsonl`

Each JSONL line is one journey with this top-level structure:

```text
journey_id
root_tweet_id
brand
reconstruction_status
reconstruction_status_reasons
message_count
customer_turn_count
support_turn_count
multi_turn
started_at
ended_at
heuristic_metadata
duplicate_leakage_metadata
messages
```

Each message retains:

```text
tweet_id
author_id
inbound
role: customer or support
created_at
text
in_response_to_tweet_id
response_tweet_id
reconstruction_depth
exact_duplicate_message
exact_duplicate_message_count
normalized_duplicate_message
normalized_duplicate_message_count
heuristic_flags
```

The `role` field is derived directly from `inbound`: `true` means `customer`; `false` means `support`. It is validated against that source flag.

### Manifest

`data/processed/spotify_journeys_manifest.json`

The manifest records the input/output paths, filter and traversal definitions, maximum depth, hash method, runtime, and output statistics.

## Journey statistics

| Metric | Count |
|---|---:|
| SpotifyCares journeys | 24,568 |
| Total messages | 72,030 |
| Customer turns | 37,305 |
| Support turns | 34,725 |
| Multi-turn journeys | 6,166 |
| Single/short journeys | 18,402 |
| Read-back JSONL journeys | 24,568 |

A multi-turn journey has at least two customer messages and at least two support messages, matching the existing exploration definition. The multi-turn share is **25.1%**.

The output does not contain intent, state, action, resolution, or escalation ground-truth labels. Those fields are intentionally reserved for the later human annotation protocol.

## Heuristic diagnostic metadata

The following journey-level flags are lightweight textual markers for analysis only:

- `failure_marker_flag`
- `question_marker_flag`
- `diagnostic_context_marker_flag`
- `dm_handoff_marker_flag`
- `resolution_marker_flag`

The same flags are retained per message under `heuristic_flags`. They are not taxonomy labels, are not ground truth, and must not be used as a substitute for human annotation.

The marker rules are deterministic regular expressions. They identify wording such as “no luck,” question language, device/version/network/account-context terms, DM or secure-channel terms, and visible working/resolution terms. They can produce false positives and false negatives.

## Duplicate and leakage metadata

The pipeline computes deterministic SHA-256 hashes using Python standard-library functionality.

### Message-level metadata

- `exact_hash`: hash of inbound/outbound role, author ID, and original text.
- `normalized_hash`: hash of inbound/outbound role, case-folded author ID, and Unicode-normalized, whitespace-normalized text.
- Each message records whether its hash occurs more than once in the raw indexed dataset and the corresponding count.

These are duplicate-content heuristics, not duplicate tweet-ID detection. Source `tweet_id` remains the provenance identity.

### Journey-level metadata

- `journey_signature_exact_hash`: ordered role/text signature hash.
- `journey_signature_normalized_hash`: ordered role/normalized-text signature hash.
- Counts and boolean duplicate indicators for both signatures.

The pipeline does **not** claim semantic near-duplicate detection. It does not use embeddings, external similarity libraries, or a semantic model. Exact and normalized hashes should later be supplemented with a carefully designed duplicate-grouping review before train/development/golden splitting.

## Validation performed

The script validates:

- journey IDs are unique;
- tweet IDs are not duplicated within a journey;
- every message preserves a non-empty original `tweet_id`;
- message ordering is deterministic;
- customer/support role agrees with the source `inbound` value;
- every non-root parent reference in a reconstructed journey points to a retained message in that journey;
- the root has the expected SpotifyCares outbound response relationship;
- stored message and turn counts agree with the message list;
- the JSONL output can be read back and parsed successfully;
- read-back journey count matches the written journey count.

Latest run results:

- **Journey IDs:** passed; 24,568 unique.
- **Message IDs within journeys:** passed.
- **Roles versus `inbound`:** passed; 0 mismatches.
- **Parent retention:** passed.
- **Message counts and turn counts:** passed.
- **JSONL read-back:** passed; 24,568 journeys.
- **Input date parsing:** passed; 0 invalid timestamps.

Representative inspection included a multi-turn partial journey, a complete DM-handoff journey, a failure-marker journey, and a visible-resolution-marker journey. These confirmed that source IDs, relationship fields, roles, flags, and reconstruction reasons are present. A DM request remains a visible handoff signal; it is not treated as proof of resolution.

## Exact reproduction command

From `D:\Hiver`:

```powershell
python src/build_spotify_journeys.py
```

The script defaults to:

```text
Input:    D:\Hiver\data\raw\archive\twcs.csv
Output:   D:\Hiver\data\processed\spotify_journeys.jsonl
Manifest: D:\Hiver\data\processed\spotify_journeys_manifest.json
```

Custom paths can be supplied with `--input`, `--output`, and `--manifest`. The script fails clearly when the input path does not exist.

## Runtime observed

The latest full run processed the raw dataset in **76.6 seconds** and completed in **100.1 seconds** total on the development machine. Runtime depends on disk, CPU, Python version, and filesystem state.

## Important limitations and concerns

- Relationship fields in the source are incomplete. The pipeline intentionally undercounts conversations that begin outside the export or cannot be linked conservatively.
- The reconstruction follows the validated rooted-thread definition and a depth limit of 100; it is not a general connected-component reconstruction.
- A `complete` journey means structurally reconstructable under this procedure, not that the real-world conversation or outcome is complete.
- Some source messages contain response links to siblings, external messages, or missing targets. These are retained as provenance and surfaced through `reconstruction_status_reasons`; they are not repaired.
- Public Twitter data cannot reveal all DM, backend, account, billing, or specialist outcomes.
- Heuristic markers are analysis metadata only and are not labels for the 10 intents, 9 states, or 13 support actions.
- Historical product, policy, catalog, device, and help-link behavior may no longer be current.
- Exact and normalized hashing does not detect true semantic near-duplicates.
- No development/golden split has been assigned yet. The entire processed pool must be isolated and split by conversation and duplicate group before model tuning or retrieval evaluation.

## Intentionally not implemented yet

- Human intent/state/action annotations.
- The 150-250 example golden evaluation set.
- Development versus golden pool assignment.
- Classifiers or other predictive models.
- Embeddings or semantic retrieval.
- Vector databases or indexes for agent retrieval.
- LLM calls, prompts, response generation, or APIs.
- Next Best Support Action policy execution.
- Current product/policy source integration.
