# Hiver Spotify Support Agent

## 1. Problem framing

Build a support decision system for SpotifyCares that classifies customer intent, tracks journey state, recommends a historically grounded next action, drafts a constrained response, and decides whether automation is safe.

## 2. Why SpotifyCares

SpotifyCares contains observable troubleshooting journeys: context collection, reversible actions, reported outcomes, changed branches after failure, secure handoffs, and specialist investigation.

## 3. What good means

A good system uses the current message and prior context, remembers attempted actions, avoids repeating failed advice, selects an allowed action, gives an explicit escalation reason, and does not claim invisible outcomes.

## 4. What we chose not to build

No vector database, microservices, complex agent framework, autonomous account access, autonomous billing/refund handling, or generic unconstrained chatbot. The first implementation is deterministic and inspectable.

## 5. System architecture

The pipeline is: normalization -> intent/state extraction -> action ledger -> development-only journey retrieval -> transition evidence -> next action policy -> escalation gate -> grounded response -> structured trace.

## 6. Data preparation

The prepared assets contain 24,568 SpotifyCares journeys, a 19,654-journey development pool, 4,914 reserved golden candidates, and 240 annotation candidates. The raw dataset remains read-only.

## 7. Golden evaluation design

Human annotators use the existing local annotation tool. Current intent and state use only the evaluation point and preceding context. Future replies support observed action and outcome analysis only. Final golden freeze is NOT YET COMPLETE.

## 8. Baselines

The simple baseline is implemented. The trivial majority baseline is implemented but will refuse to fit until labeled development data exists.

## 9. Results

**NOT YET MEASURED.** The existing annotation directory contains only a small pre-existing annotation record, which is insufficient for headline claims.

## 10. Failure analysis

Trace and signal tooling identifies low confidence, weak retrieval, absent transition evidence, repeated failed-action selection, escalation review, and response warnings. These are investigation signals, not confirmed failures.

## 11. What is misleading about my headline number?

Any single score could hide the under-observed nature of outcomes after DM or specialist handoff, the small and deliberately composed golden set, intent ambiguity, and the difference between choosing a safe next action and actually resolving a customer issue.

## 12. Limitations

Historical support behavior is not current policy truth. Public threads often do not expose final outcomes. The split detects exact and normalized duplicate signatures but not all semantic near-duplicates. Lexical extraction is a transparent starting point, not a final classifier.

## 13. One more week

Complete human annotation and adjudication, freeze the golden manifest, fit the majority baseline where permitted, run full evaluation, review failure signals, calibrate thresholds, and optionally compare a configured LLM judge against a human-rated subset.
