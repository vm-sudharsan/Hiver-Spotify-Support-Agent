# Implementation Decision Log

This log records decisions actually implemented in the repository.

1. **Use reconstructed journeys as the retrieval unit.** The retriever indexes complete development journeys, preserving message provenance instead of treating isolated tweets as independent support examples.
2. **Keep the 10 intents, 9 states, and 13 actions frozen.** All agent modules validate against the existing vocabularies and reject invented labels.
3. **Represent missing diagnostic context as a requirement.** Missing information is stored separately from troubleshooting state; `DIAGNOSTIC_CONTEXT_NEEDED` is not introduced as a state.
4. **Make case state explicit.** `CaseState` stores the current customer message, confidence, environment, missing information, attempted actions, failed actions, retrieval, selected action, and automation decision.
5. **Cut evaluation context at the customer message.** Normalization exposes context only through the selected evaluation point so future support replies cannot contaminate current intent or state.
6. **Use TF-IDF before embeddings.** The development-only retriever is fast, inspectable, reproducible, and sufficient for the first measurable implementation.
7. **Protect against failed-action repetition.** A failed action is filtered from direct reuse unless a caller explicitly supplies new evidence to allow a retry.
8. **Keep escalation outside response generation.** A deterministic policy decides `AUTO_HANDLE` or `ESCALATE` using explicit risk gates; confidence cannot override high-risk rules.
9. **Use a deterministic response fallback.** The system can run without an API key and drafts replies constrained to the selected frozen action.
10. **Treat historical evidence as internal trace data.** Journey IDs support audit and evaluation but are not exposed as unsupported customer-facing claims.
11. **Make LLM use optional.** Provider configuration is environment-based, structured, and absent by default; deterministic components remain runnable offline.
12. **Never fabricate evaluation labels or results.** Majority baselines refuse unlabeled development data, evaluation reports `NOT_READY` when appropriate, and failure analysis emits signals rather than confirmed failures.
13. **Keep human annotation separate from the agent.** The annotation tool remains manual and does not show model predictions or retrieval output.
14. **Use a small, transparent test suite.** Tests focus on frozen vocabularies, leakage boundaries, failed-action protection, escalation gates, response safety, and deterministic metrics.

## Current boundaries

- The current development pool has no human intent/action labels, so the majority baseline cannot yet be fit.
- The current annotation directory contains one pre-existing `annotator_1` record and no shared two-annotator subset; agreement is `NOT_READY`.
- Final golden freeze and headline metrics remain human-data milestones, not generated artifacts.
