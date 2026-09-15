# SpotifyCares Golden Evaluation Annotation Guide

## Purpose and scope

This guide defines the human annotation protocol for a future 150-250 example golden evaluation set for the SpotifyCares support-agent project. It is intended to let two independent annotators label the same reconstructed conversation consistently.

This document defines labels and adjudication rules only. It does not create the golden set, sample conversations, modify the raw dataset, modify the taxonomy or architecture, build an agent, create embeddings or a vector database, install packages, or call an LLM.

The annotation contract is frozen:

- 10 customer intents
- 9 troubleshooting journey states
- 13 support actions

The historical source contains incomplete conversation relationships and many invisible outcomes. Therefore, `UNKNOWN`, `AMBIGUOUS`, `INSUFFICIENT_EVIDENCE`, and `UNLABELLED` are valid annotation results. Annotators must not force a label merely to increase coverage.

## 1. Annotation unit

### 1.1 One example

One annotation example represents a **current customer message plus the relevant preceding conversation context within one reconstructed SpotifyCares conversation**. The unit is not an isolated tweet unless no preceding context is available or the conversation is genuinely one message long.

The example must preserve:

- `conversation_id` and source message IDs;
- chronological customer and support messages;
- the customer message at which the evaluation point is anchored;
- all preceding context needed to understand intent, state, missing information, attempted actions, and risk;
- any immediately following support message needed to label the historically observed next action.

Do not include later messages when they would reveal information unavailable at the evaluation point, except in a separately stored outcome field used only to annotate what actually happened afterward.

### 1.2 Evaluation point

The evaluation point is the latest customer message for which the system would be asked to choose a next support action. It must be identified by source message ID and timestamp when available.

Use this procedure:

1. Start with a customer message that has a support response or a clearly observable conversation continuation.
2. Include all relevant preceding messages in the same reconstructed conversation.
3. Treat the customer message as the current input. Do not use the future support reply to decide the current state or missing information.
4. Inspect the next support message only to label `OBSERVED_NEXT_ACTION` and later outcome fields.
5. If no clear next support action follows, record `UNLABELLED` or `UNKNOWN` as appropriate.

For a first customer message, the preceding context may be empty. For a later customer message, prior support instructions and prior customer results are essential because state and attempted actions are cumulative.

### 1.3 Context boundary

Use only messages in the reconstructed conversation and source metadata available to the project. If reconstruction is partial, preserve that fact in `reconstruction_status` and lower annotation confidence when it affects the label.

Do not infer hidden DM messages, backend actions, internal incident status, or a final resolution that is not visible in the source.

## 2. Intent annotation

Intent is the customer's primary problem or goal, not the current troubleshooting state and not the next support action. Select exactly one of the existing 10 intents when the evidence supports one. Use `intent_status = AMBIGUOUS` or `INSUFFICIENT_EVIDENCE` when a defensible single intent is not possible; do not create an `OTHER` intent.

### 2.1 Frozen intent definitions and boundaries

#### 1. Playback reliability

- **Definition:** Music will not start, pauses, skips, stutters, crashes, or behaves inconsistently during playback.
- **Include:** Playback failure or interruption is the customer's main complaint, including cross-device playback pauses.
- **Exclude:** A specific track/artist/catalog availability complaint where availability is the central issue; a non-playback app UI, battery, login screen, or control problem.
- **Example:** “My music keeps stuttering/skipping ever since I upgraded to iOS 11.”

#### 2. App, device, and platform behavior

- **Definition:** An app UI, login screen, battery use, control, crash, or platform-specific feature behaves incorrectly without a primarily playback-focused report.
- **Include:** App crashes, blank/login screens, battery drain, unusable controls, or platform behavior where playback is not the primary goal.
- **Exclude:** Playback interruption as the dominant complaint; download/offline or catalog availability as the dominant complaint.
- **Example:** “The new iOS is making your app way less usable.”

#### 3. Content or catalog availability

- **Definition:** A particular song, artist, album, or track is unavailable, greyed out, or inconsistent by territory.
- **Include:** “Removed,” unavailable, greyed-out, or artist-specific catalog complaints.
- **Exclude:** General playback failure affecting many or unspecified tracks; playlist organization when availability is not the issue.
- **Example:** “Why can’t I listen to Dua Lipa?”

#### 4. Playlist, library, and music organization

- **Definition:** The customer wants to find, order, save, manage, shuffle, repeat, or otherwise organize music and playlists.
- **Include:** Library arrangement, playlist behavior, saved music organization, and feature-use questions.
- **Exclude:** A track being unavailable, local-file/download storage as the primary issue, or playback failure as the primary issue.
- **Example:** “Move songs around so they're in my order and not the order of when I added them.”

#### 5. Premium, subscription, and plan status

- **Definition:** Premium activation, upgrade, trial, cancellation, renewal, or a mismatch between paid and free-plan status.
- **Include:** “Premium stopped working,” plan entitlement, trial, cancellation, and upgrade status.
- **Exclude:** A charge, refund, card error, or payment dispute, which belongs to Billing, payment, refund, and card issues.
- **Example:** “I'm paying for Premium but it keeps saying free service.”

#### 6. Billing, payment, refund, and card issues

- **Definition:** Duplicate or incorrect charges, card errors, payment-method problems, refunds, or charge disputes.
- **Include:** Money charged, card purchase errors, payment method, or refund requests.
- **Exclude:** A plan-status complaint with no payment problem; account access/security unless the primary problem is compromise or ownership.
- **Example:** “My card was charged twice, and I am not even upgraded.”

#### 7. Account access, identity, and security

- **Definition:** Inability to sign in, password/email problems, account takeover, or profile/country identity issues.
- **Include:** Hacked account, changed email, locked account, password/sign-in failure, or ownership/access concern.
- **Exclude:** Premium status, billing, or Family/student eligibility when access/security is not the primary goal.
- **Example:** “Somebody hacked my Spotify account and changed my email.”

#### 8. Family and student eligibility

- **Definition:** Family-plan invitation/address problems, student verification, or discount/eligibility questions.
- **Include:** Family invitations, address checks, student verification, and eligibility rules.
- **Exclude:** General Premium status or payment problems unless eligibility is clearly the main concern.
- **Example:** “Trying to verify that I'm a student again but the pop-up doesn't do anything.”

#### 9. Downloads and offline listening

- **Definition:** Downloading, offline visibility, local files, storage, or managing downloaded music.
- **Include:** Offline mode, downloaded content, local files, and download storage behavior.
- **Exclude:** General playback or library organization when download/offline behavior is not central.
- **Example:** “Give me the option to offline/download the song.”

#### 10. Ads and free-tier experience

- **Definition:** Ad frequency, ad-free benefit, ad content, promotion eligibility, or free-tier advertising behavior.
- **Include:** Unwanted ads, ad interruptions, ad-free duration, and free-tier promotions.
- **Exclude:** Premium entitlement when the customer is primarily asking about paid plan status; ordinary playback interruptions without an ad issue.
- **Example:** “The ad interrupted the music I had streaming at work.”

Connected-device integration remains a cross-cutting context field, not an eleventh intent.

### 2.2 Difficult intent boundaries

- **Playback reliability vs App, device, and platform behavior:** choose Playback reliability when starting, pausing, skipping, stuttering, or playback continuity is the main complaint. Choose App/device/platform behavior when the primary issue is UI, login screen, battery, crash, control, or a platform feature and playback is incidental or absent.
- **Playback reliability vs Content or catalog availability:** choose Content/catalog when a named song, artist, album, or set of tracks is unavailable or greyed out. Choose Playback when the issue is broad, environment-specific, or not tied to particular catalog items. If both are equally supported, mark ambiguity and record the alternative.
- **Premium/subscription vs Billing/payment:** choose Premium/subscription for entitlement, plan, trial, cancellation, or upgrade status. Choose Billing/payment for charges, refunds, card errors, or payment methods. A paid-status complaint alone is not a billing label.
- **Account access/security vs other account issues:** choose Account access/security when sign-in, ownership, password/email, lockout, or compromise is central. Choose Premium, Billing, or Family/student when the account is merely the context for a plan, payment, or eligibility issue.
- **Downloads/offline vs Playlist/library:** choose Downloads/offline when storage, downloaded content, local files, or offline availability is central. Choose Playlist/library for organizing or managing music independent of offline storage.

## 3. Troubleshooting-state annotation

Select exactly one of the existing 9 journey states at the evaluation point when possible. State is determined from the entire preceding conversation, not merely the last sentence.

### 3.1 Frozen states

| State | Use when |
|---|---|
| `SYMPTOM_REPORTED` | The customer has reported a problem, but the journey has not yet established enough context for a later branch. |
| `CONTEXT_COLLECTED` | Relevant diagnostic facts have been supplied and are available for a branch-specific action. |
| `FIRST_LINE_ACTION_PROPOSED` | Support has proposed a reversible first-line action and the customer result is not yet available. |
| `ACTION_RESULT_REPORTED` | The customer has reported that an action worked, partly helped, or failed, but the journey has not yet clearly moved to repeated failure, resolution, or another terminal branch. |
| `REPEATED_FAILURE_OR_BROADER_INCIDENT` | Multiple attempts fail, the problem persists or recurs, or the issue spans environments in a way suggesting a broader incident. |
| `PRIVATE_ACCOUNT_CONTEXT_REQUIRED` | Private account, plan, billing, entitlement, or security data is required for the next step. |
| `SPECIALIST_OR_PRODUCT_INVESTIGATION` | Support indicates that developers, technical staff, or a relevant product team is investigating or receiving feedback. |
| `RESOLVED` | The customer explicitly indicates that the issue is fixed or resolved. |
| `MONITORING` | The issue appears improved or support asks the customer to watch for recurrence, but there is no explicit confirmation of resolution. |

`DIAGNOSTIC_CONTEXT_NEEDED` is **not a state**. Record missing diagnostic information as a condition in `missing_information`, and record the support question used to request it as an existing support action. After the customer provides the required facts, the state can become `CONTEXT_COLLECTED`.

### 3.2 State precedence and ambiguity rules

When multiple state signals exist, use the most recent supported journey position while preserving prior attempts and failures. Apply these precedence rules when the evidence is clear:

1. Explicit `RESOLVED` takes precedence over earlier action-result states.
2. Explicit specialist/developer investigation takes precedence over ordinary troubleshooting states.
3. A private-account handoff requirement takes precedence when secure account context is the next required step.
4. Repeated failure or recurrence takes precedence over a single ordinary failed action.
5. `MONITORING` applies to apparent improvement or a request to watch for recurrence without explicit resolution.
6. `ACTION_RESULT_REPORTED` applies when a result is known but no later branch is established.
7. `FIRST_LINE_ACTION_PROPOSED` applies when support has proposed an action but no customer result is available.
8. `CONTEXT_COLLECTED` applies when required branch facts are available before the next action.
9. Otherwise use `SYMPTOM_REPORTED`.

Definitions for difficult endings:

- **Explicit resolution:** Customer says it is fixed, working, solved, or equivalent. Label `RESOLVED`.
- **Apparent improvement:** Customer says it seems better, works so far, or support says to monitor, without explicit fixed/resolved confirmation. Label `MONITORING`.
- **Repeated failure:** At least two distinct attempted actions fail, or one action fails and the issue clearly persists/recurs after prior troubleshooting. Label `REPEATED_FAILURE_OR_BROADER_INCIDENT` when the journey has moved beyond a single result.
- **Private-account context:** Support requests account details by DM or secure channel, or the next step requires private lookup. Label `PRIVATE_ACCOUNT_CONTEXT_REQUIRED`; do not infer that the account issue was solved.
- **Specialist/product investigation:** Support explicitly reports escalation, developer review, investigation, or product feedback. Label `SPECIALIST_OR_PRODUCT_INVESTIGATION`.
- **Ambiguous ending:** If the final visible message does not establish a state, use `state_status = AMBIGUOUS` and choose the best-supported state only if the confidence is at least Low and the uncertainty is recorded. Otherwise use `UNLABELLED`.

## 4. Missing-information annotation

Missing information is a structured condition attached to the case. It is not a journey state and it is not a new support action.

For each item, record `requirement`, `status`, `why_needed`, `safely_requestable`, `candidate_action`, and evidence references. Use only the existing 13 actions in `candidate_action`.

### 4.1 Controlled missing-information items

| Requirement | What is missing | Why it matters | Safely requestable? | Existing action that can request it |
|---|---|---|---|---|
| `PLATFORM_CONTEXT` | Device, OS, Spotify version, browser, or app version | Separates platform branches and reproducibility | Usually yes in public support | `ASK_PLATFORM_CONTEXT` |
| `SYMPTOM_EVIDENCE` | Exact error, visible behavior, screenshot, crash state, greyed-out state, or onset | Distinguishes failure modes and confirms the reported symptom | Usually yes; avoid private content in screenshots | `ASK_SYMPTOM_EVIDENCE` |
| `SCOPE_OR_ENVIRONMENT` | Other device, artist, browser, network, speaker/car, Wi-Fi/cellular, or affected scope | Tests whether the issue is local, catalog-specific, or broader | Usually yes | `ASK_SCOPE_OR_ENVIRONMENT` |
| `CATALOG_CONTEXT` | Song link/URI, artist/track, account country, or availability scope | Needed for catalog, rights, and territory investigation | URI and country are generally requestable; do not infer rights | `ASK_CATALOG_CONTEXT` |
| `SECURE_ACCOUNT_CONTEXT` | Username/email, plan/account status, entitlement, or security details | Required for private account lookup | No in a public channel; request only through a secure channel | `REQUEST_SECURE_ACCOUNT_DETAILS` or `MOVE_TO_DM_OR_SECURE_CHANNEL` |
| `PRIOR_ATTEMPTS_AND_TIMING` | What was tried, result, recurrence, or update/onset timing | Prevents repeating failed actions and supports transition selection | Usually yes | `ASK_SYMPTOM_EVIDENCE` or `ASK_SCOPE_OR_ENVIRONMENT` |

These are requirement names for annotation only. They do not expand the taxonomy.

### 4.2 Status values

- `missing`: no reliable evidence supplied.
- `present`: the required fact is available and usable.
- `conflicting`: the conversation contains incompatible facts.
- `private`: the fact may be needed but cannot safely be requested or recorded in public context.
- `unknown`: the conversation is too incomplete to determine whether it exists.
- `not_required`: the branch does not require this item at the evaluation point.

Mark a requirement as missing only when it would materially affect the next-action decision. Do not list every possible fact.

## 5. Attempted-action annotation

Record every clearly attempted or explicitly proposed support action from the frozen 13-action vocabulary, in chronological order. An action is an operation performed or proposed in the conversation, not a generic word that happens to appear.

### 5.1 Frozen action vocabulary

`ASK_PLATFORM_CONTEXT`, `ASK_SYMPTOM_EVIDENCE`, `ASK_SCOPE_OR_ENVIRONMENT`, `ASK_CATALOG_CONTEXT`, `SESSION_RESET`, `REINSTALL_OR_CLEAN_INSTALL`, `BROWSER_REMEDIATION`, `NETWORK_REMEDIATION`, `PROVIDE_HELP_RESOURCE`, `REQUEST_SECURE_ACCOUNT_DETAILS`, `MOVE_TO_DM_OR_SECURE_CHANNEL`, `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE`, `CONFIRM_AND_MONITOR`.

### 5.2 Required fields per attempt

For each attempt record:

- `action`: one of the 13 names;
- `order`: sequence number within the conversation;
- `source_message_id`: message that proposed, performed, or reported the action;
- `explicitness`: `explicit` when directly stated, `inferred` when strongly implied by concrete wording, or `ambiguous` when not reliable;
- `result`: one of `attempted`, `failed`, `partially_helped`, `improved`, `resolved`, or `unknown`;
- `result_evidence`: customer wording or source reference;
- `equivalence_group`: whether the action is materially the same as a prior attempt, when relevant.

`attempted` means the action was clearly performed or accepted but no result is visible. `unknown` means the action or result cannot be reliably established. Do not turn a support suggestion into a successful attempt.

### 5.3 Result guidance

Strong failure evidence includes explicit customer feedback such as:

- “No luck.”
- “Still not working.”
- “That didn't help.”
- “Neither worked.”
- “Nothing changed.”
- “It still happens.”
- “The problem persists.”

A customer reporting “I tried reinstalling” establishes an attempted `REINSTALL_OR_CLEAN_INSTALL`; it does not establish success or failure without a result. “Thanks” alone is not proof of resolution. “Seems to have worked so far” is `improved` or `MONITORING`, not `resolved`.

Use `partially_helped` when one symptom or environment improves while a material issue remains. Use `improved` when the customer reports better behavior but does not explicitly say the issue is fixed. Use `resolved` only when the customer explicitly confirms the issue is fixed or working.

### 5.4 Ambiguous actions

If support says “try this” but the customer never responds, record the action as `attempted` only when the message clearly proposes that controlled action; record its result as `unknown`. If a generic help link could represent several actions, use `PROVIDE_HELP_RESOURCE` and do not infer a specific repair. If multiple actions are bundled, record each only when the text clearly supports each action.

## 6. Next-support-action annotation

### 6.1 Observed versus ideal action

The golden target is primarily the **historically observed next support action**: what Spotify support actually did next after the evaluation point. It is not what an annotator personally believes support should have done.

Record two separate fields:

- `OBSERVED_NEXT_ACTION`: one of the 13 actions when the next support message clearly expresses that action; otherwise `UNKNOWN` or `UNLABELLED`.
- `IDEAL_NEXT_ACTION`: optional research field for what the protocol considers a defensible next action under the frozen taxonomy and evidence. It must never replace the observed target and must not be used to rewrite history.

Use the observed action even when it was generic, repetitive, or arguably suboptimal. Annotators may record `observed_action_quality = questionable` and explain why, but should not substitute the ideal action.

### 6.2 Selecting the observed action

1. Identify the first support message after the evaluation point.
2. Determine whether it contains one or more controlled actions.
3. If one action is clear, label it as `OBSERVED_NEXT_ACTION`.
4. If several actions are explicitly bundled, record the ordered list in `observed_next_actions` and designate the first actionable operation as `primary_observed_next_action`.
5. If the message only acknowledges, repeats the problem, or contains no recognizable controlled action, use `UNKNOWN`.
6. If the support reply is missing, truncated, or inaccessible, use `UNLABELLED` for the observed target and record the reason.

A reply that requests username/email by DM is `REQUEST_SECURE_ACCOUNT_DETAILS`, `MOVE_TO_DM_OR_SECURE_CHANNEL`, or both only when both actions are independently explicit. Do not label a private handoff as resolution.

## 7. Resolution and outcome annotation

Outcome describes what is visibly known after the evaluation point. It is separate from current state and next action.

Use exactly one primary outcome when supported:

- `resolved`: Customer explicitly indicates the issue is fixed, solved, or working.
- `monitoring_or_improved`: Customer reports improvement or support asks the customer to monitor recurrence, without explicit resolution.
- `unresolved`: The issue is explicitly still present or the latest visible customer result is failure.
- `escalated_or_handoff`: Support visibly escalates to technical/product staff or hands the case to a human/secure channel, with no visible resolution.
- `dm_ended`: The public conversation ends at a DM/secure-channel request and no later outcome is visible. Use this alongside `evidence_visibility = dm_ended`.
- `unknown`: The visible conversation does not support a more specific outcome.

Where multiple descriptions apply, preserve both in structured secondary fields but use the most informative primary label. For example, a technical escalation followed by no visible result is `escalated_or_handoff`, not `resolved`. A DM request after a failed action is `dm_ended` or `escalated_or_handoff`, never automatic resolution.

A support message suggesting a troubleshooting step proves only that the step was suggested. It is not evidence that the customer followed it or that it worked.

## 8. Escalation annotation

Record whether the case is **eligible for escalation** based on observed risk and evidence boundaries. This is an annotation of operational suitability, not a judgment about model confidence.

Use:

- `yes`: visible evidence meets one or more escalation boundaries;
- `no`: low-risk, sufficiently evidenced handling appears appropriate at the evaluation point;
- `uncertain`: the case may be risky, but the visible evidence is insufficient to decide.

Record one or more reason codes:

- `PRIVATE_ACCOUNT_CONTEXT`
- `SECURITY_OR_ACCOUNT_ACCESS`
- `BILLING_PAYMENT_OR_REFUND`
- `REPEATED_FAILURE_OR_RELAPSE`
- `BROADER_INCIDENT`
- `SPECIALIST_OR_PRODUCT_INVESTIGATION`
- `INSUFFICIENT_EVIDENCE`
- `CONFLICTING_EVIDENCE`
- `HISTORICAL_POLICY_OR_CATALOG_LIMITATION`
- `OTHER_HIGH_RISK`

Escalation boundaries:

- Private account lookup, plan entitlement, billing, payment, refund, security, and ownership cases are generally escalation-eligible.
- Repeated failure, relapse, cross-device/network incidents, or specialist/product investigation are escalation-eligible.
- Insufficient or conflicting evidence is escalation-eligible when an incorrect action could matter or no safe next action is supported.
- Clearly scoped, low-risk environment, browser, session, or diagnostic questions may be `no` when enough facts are present and no failed action is being repeated.

Do not use “the LLM would be confident” or any model score as an annotation criterion.

## 9. Evidence visibility

Record how much of the outcome is visible in the source:

- `visible`: The relevant customer result or outcome is explicitly present in the accessible conversation.
- `partial`: Some progression or result is visible, but the ending, resolution, or full context is missing.
- `dm_ended`: The public conversation ends at a DM/secure-channel request and the private continuation is unavailable.
- `unknown`: The available source does not establish what happened.

Visibility matters because an observed handoff is evidence of a support action, not evidence of successful resolution. Metrics for action selection may use a DM handoff as an observed transition, but resolution metrics must not count it as success.

## 10. Ambiguity protocol

Unknown is preferable to an unsupported guess. Annotators must record an ambiguity reason whenever a label is uncertain.

### 10.1 Required handling

- **Multiple plausible intents:** choose one only when the primary customer goal is supported by the full context. Otherwise record the leading intent, alternative intent, `intent_status = AMBIGUOUS`, and the boundary reason.
- **Unclear state:** use the state precedence rules only when the conversation supports them. Otherwise record `state_status = AMBIGUOUS` or `UNLABELLED`.
- **Unclear action:** if no controlled action is clearly expressed, use `UNKNOWN` for an absent/unclear action or `UNLABELLED` when the relevant reply is missing.
- **Incomplete reconstruction:** mark `reconstruction_status = partial` or `uncertain`; lower confidence and exclude from the golden set if the missing context could change the primary labels.
- **Invisible outcome:** use `evidence_visibility = dm_ended` or `unknown`; do not infer resolution.
- **Ambiguous customer wording:** record only what the wording supports. “I tried it” without identifying the action is not enough for a specific action.
- **Generic support language:** “we are looking into it” may support `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE` only when the surrounding text clearly indicates investigation; otherwise use `UNKNOWN` or `UNLABELLED`.

### 10.2 Ambiguity versus exclusion

Mark an example `ambiguous` when it is still a useful challenge case and at least one plausible label can be recorded with a reason. Mark it `insufficient_evidence` when the visible conversation cannot support the requested field. Mark it `exclude_from_golden = yes` when:

- the conversation identity or ordering is unreliable;
- key messages are missing and the evaluation point cannot be established;
- labels depend mainly on hidden DM/backend content;
- the next action cannot be observed and the example is not intentionally part of an unknown-action stratum;
- the example is a duplicate or near-duplicate of another selected golden example;
- private or sensitive content cannot be safely retained under the project handling rules.

Excluded records may remain in a separate audit log with minimal identifiers and a reason, but must not enter the locked golden set.

## 11. Annotation confidence

Use a simple three-level scale for each major label and an overall annotation confidence:

- **High:** Direct wording or an unambiguous sequence supports the label; relevant context is complete enough and no material contradiction is present.
- **Medium:** The label is the best-supported interpretation, but wording, context, or action mapping has a limited ambiguity.
- **Low:** The label is tentative because of incomplete reconstruction, generic language, conflicting facts, or an invisible outcome.

Low-confidence examples can be valuable challenge cases. They must be separately tracked and should not be mixed with high-confidence examples when reporting performance. A low-confidence label must include an `ambiguity_reason` or `insufficient_evidence_reason`.

## 12. Inter-annotator agreement

Two annotators should label each candidate independently, without seeing the other annotation. They should receive the same conversation context, evaluation point, label definitions, and source references.

Compare at least:

- primary intent and ambiguity status;
- current troubleshooting state and state status;
- missing-information items and statuses;
- attempted actions, order, explicitness, and results;
- primary observed next action;
- outcome and evidence visibility;
- escalation eligibility and reason codes;
- overall confidence and ambiguity reason.

Recommended conceptual measures:

- exact agreement and Cohen's kappa for single categorical fields such as primary intent, state, outcome, and escalation eligibility;
- macro-F1 or Jaccard similarity for multi-label missing-information items and escalation reason codes;
- sequence-aware agreement for attempted-action order and observed action lists;
- separate agreement rates for high-confidence and low-confidence examples;
- adjudication rate and field-level missingness rate.

Do not count agreement created by both annotators choosing an unsupported forced label as quality. Track `UNKNOWN`, `UNLABELLED`, and ambiguity agreement explicitly.

Disagreements should be adjudicated by reviewing the protocol and source evidence, not by voting for the more common label. Update the guide before the next annotation batch if a recurring disagreement reveals an underspecified boundary.

## 13. Golden-set composition

Do not create the set during this phase. When the set is later sampled, target 150-250 examples; a practical initial target is 200. Strata may overlap, so the counts below are sampling goals rather than additive quotas.

### 13.1 Recommended composition for a 200-example target

- 70-90 common-intent cases covering Playback, App/device/platform, Content/catalog, Playlist/library, and Premium/subscription.
- At least 30 cases from rarer intents, including Billing/payment, Account access/security, Family/student, Downloads/offline, and Ads/free-tier.
- At least 80 multi-turn journeys with enough context to test state and attempted-action memory.
- At least 35 repeated-failure, relapse, or broader-incident cases.
- At least 30 escalation-eligible cases, including private-account, security, billing, repeated-failure, and specialist/product examples.
- At least 25 DM-ended or otherwise partially visible outcomes.
- At least 20 cases with explicit `RESOLVED` evidence.
- At least 20 `MONITORING` or apparent-improvement cases.
- At least 20 ambiguous, insufficient-evidence, or unknown-next-action challenge cases, clearly flagged.
- At least 15 cases where no safe next action is evident from the visible evidence.

Ensure every one of the 10 intents and every one of the 9 states appears. Include both observed diagnostic questions and observed remediation/escalation actions across the 13-action vocabulary where the historical data supports them. Do not balance by inventing examples for rare or absent transitions.

### 13.2 Sampling safeguards

Use conversation-level and near-duplicate-level sampling. Avoid selecting several examples that differ only by copied support template, the same incident burst, or the same customer wording. Preserve representative frequency information separately from the deliberately balanced evaluation composition.

Include easy, medium, and challenge cases. A golden set consisting only of common, clean, successfully resolved cases would overestimate state, action, and response quality.

## 14. Leakage prevention

The golden set must be isolated before any training or system tuning occurs.

1. Reconstruct and assign stable conversation/thread identity first.
2. Detect duplicate and near-duplicate groups, copied support templates, and apparent incident clusters.
3. Select candidate examples by conversation and duplicate group, never by isolated tweet.
4. Annotate candidates independently before exposing system predictions.
5. Adjudicate and lock the final set and its labels.
6. Remove every golden conversation, message, duplicate group, and derived transition from training data, retrieval indexes, prompt examples, feature fitting, and threshold tuning.
7. Keep a manifest containing conversation IDs, message IDs, split membership, selection reason, and lock status.
8. Do not use golden outcomes to choose retrieval settings, action thresholds, prompts, or escalation rules.

If the same conversation contains multiple possible evaluation points, select one primary point for the golden set or place all points in the same locked group and document the decision. Never split points from one conversation across train and evaluation.

## 15. Annotation record schema

The following is a conceptual record for one example. It introduces field names, not new taxonomy labels.

```text
AnnotationRecord
- example_id
- conversation_id
- source_message_ids
- evaluation_point_message_id
- evaluation_point_timestamp
- conversation_context
- reconstruction_status: complete, partial, or uncertain
- intent: one frozen intent or null when unlabelled
- intent_alternatives
- intent_status: labelled, ambiguous, insufficient_evidence, or unlabelled
- intent_confidence: high, medium, or low
- troubleshooting_state: one frozen state or null when unlabelled
- state_status: labelled, ambiguous, insufficient_evidence, or unlabelled
- state_confidence: high, medium, or low
- missing_information: list of MissingInformationItem
- attempted_actions: ordered list of AttemptedAction
- primary_observed_next_action: one frozen action, unknown, or unlabelled
- observed_next_actions: ordered list of frozen actions when bundled
- observed_action_quality: clear, generic, repetitive, questionable, or unknown
- ideal_next_action: optional frozen action or null
- outcome: resolved, monitoring_or_improved, unresolved, escalated_or_handoff, dm_ended, or unknown
- evidence_visibility: visible, partial, dm_ended, or unknown
- escalation_eligible: yes, no, or uncertain
- escalation_reason_codes
- annotation_confidence: high, medium, or low
- ambiguity_reason
- insufficient_evidence_reason
- exclude_from_golden: yes or no
- exclusion_reason
- annotator_id
- annotation_timestamp
- adjudication_status
- adjudication_notes
```

```text
MissingInformationItem
- requirement
- status
- why_needed
- safely_requestable: yes, no, or unknown
- candidate_action: one or more existing actions
- evidence_references
```

```text
AttemptedAction
- action
- order
- source_message_id
- explicitness: explicit, inferred, or ambiguous
- result: attempted, failed, partially_helped, improved, resolved, or unknown
- result_evidence
- equivalence_group
```

The `ideal_next_action` field is optional and must be kept separate from the observed target. It exists for later policy analysis, not for evaluating whether the historical support reply matched an annotator's preference.

## 16. Worked examples

These examples use patterns documented in the existing Spotify support playbook. They demonstrate annotation reasoning; they do not assert outcomes beyond the visible evidence described there.

### Example A: Chrome web-player skipping

**Visible sequence:** Customer reports songs randomly skip in Chrome web player. Support asks about browser/incognito or another-browser testing. Customer reports Firefox works, Chrome is current, and there is no error.

- Intent: `Playback reliability` because skipping is the primary complaint.
- State at the evaluation point after the customer supplies browser comparison: `CONTEXT_COLLECTED`.
- Missing information: `SYMPTOM_EVIDENCE` may be present as “no error”; no platform requirement is missing if the relevant browser facts are available.
- Attempted actions: the browser comparison is `ASK_SCOPE_OR_ENVIRONMENT`, result `partially_helped` because Firefox works while Chrome still skips.
- Observed next action: if evaluating immediately before the documented cache/cookie support message, label `BROWSER_REMEDIATION` when that message is the next support action.
- Outcome: “seems to have worked so far” is `monitoring_or_improved`, not `resolved`.
- Evidence visibility: `visible` for the improvement statement.
- Escalation: usually `no` at the browser-remediation point if no high-risk or repeated-failure signal is present.

### Example B: Artist unavailable on iPhone after failed steps

**Visible sequence:** Customer reports Lana Del Rey music does not play on iPhone SE. Support gathers device/OS and whether other artists work. Customer says other artists play and login/restart and download do not help. Support provides a reinstall link. Customer says “Still no luck.” Support moves to technical-team investigation; later the customer reports music working again.

At the evaluation point immediately after “Still no luck”:

- Intent: `Content or catalog availability` because the artist-specific availability problem is central.
- State: `REPEATED_FAILURE_OR_BROADER_INCIDENT` because multiple attempts failed and the issue remains artist-specific.
- Missing information: record only material absent requirements; if account context is requested later, it is not retroactively missing at this point unless needed for the next branch.
- Attempted actions: `SESSION_RESET` and the documented download attempt may be recorded only if the source explicitly supports them; `REINSTALL_OR_CLEAN_INSTALL` is explicit and its result is `failed`.
- Observed next action: `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE` for the investigation message.
- Outcome at that point: `escalated_or_handoff`, not resolved. The later customer report can support a later `RESOLVED` evaluation point if it explicitly indicates the issue worked again.
- Escalation: `yes`, reason `REPEATED_FAILURE_OR_RELAPSE` and/or `SPECIALIST_OR_PRODUCT_INVESTIGATION`.

### Example C: Account-linked Echo/Sonos issue

**Visible sequence:** Customer says linking Echo/Sonos prevents phone and desktop playback and reports an account-used-elsewhere message. Support asks whether devices play simultaneously and explains the one-stream rule with a resource. Customer says the explanation does not fit because the speaker was stopped. Spotify passes the case to developers.

At the point before developer escalation:

- Intent: `Playback reliability`, with connected-device integration recorded as context.
- State: `REPEATED_FAILURE_OR_BROADER_INCIDENT` because the proposed explanation does not fit the customer's evidence and the issue persists across connected environments.
- Missing information: `SYMPTOM_EVIDENCE` may be satisfied by the account-used-elsewhere message and device behavior.
- Attempted actions: `ASK_SYMPTOM_EVIDENCE` and `PROVIDE_HELP_RESOURCE` are observed; the resource does not prove a fix.
- Observed next action: `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE`.
- Outcome: `escalated_or_handoff`; evidence visibility `visible` for the developer handoff but not for final resolution.
- Escalation: `yes`, reason `SPECIALIST_OR_PRODUCT_INVESTIGATION` and possibly `CONFLICTING_EVIDENCE`.

### Example D: iPhone login loop and secure handoff

**Visible sequence:** Customer reports an iPhone login screen loop after reinstall. Support asks for device/OS, screenshot, and other-device behavior. Customer supplies iPhone/iOS details, screenshot, and repeated failure. Support suggests remove/restart/reinstall and asks about another network. Blank screens persist; the customer declines an unrelated desktop test. Support requests account details by DM.

- Intent: `Account access, identity, and security` if login access is the primary issue; do not label App/device/platform merely because an iPhone is involved.
- State at the DM request: `PRIVATE_ACCOUNT_CONTEXT_REQUIRED`.
- Missing information: `SECURE_ACCOUNT_CONTEXT` is private and safely requestable only through the secure channel.
- Attempted actions: reinstall/session reset with `failed` or `unknown` result according to the visible customer wording; do not assume the customer completed every bundled step.
- Observed next action: `MOVE_TO_DM_OR_SECURE_CHANNEL` and, if explicitly requesting username/email, `REQUEST_SECURE_ACCOUNT_DETAILS`.
- Outcome: `dm_ended` or `escalated_or_handoff`, not resolved.
- Evidence visibility: `dm_ended`.
- Escalation: `yes`, reasons `PRIVATE_ACCOUNT_CONTEXT` and `SECURITY_OR_ACCOUNT_ACCESS`.

## 17. Quality-control checklist

Before submitting an annotation, the annotator must confirm:

- [ ] The evaluation point is identified by message ID and is not confused with the later support reply.
- [ ] The context includes the relevant preceding messages from the same conversation.
- [ ] Exactly one existing intent is selected, or ambiguity/insufficient evidence is explicitly recorded.
- [ ] The intent describes the customer's goal, not the state or support action.
- [ ] Exactly one existing troubleshooting state is selected when supportable.
- [ ] `DIAGNOSTIC_CONTEXT_NEEDED` was not used as a state.
- [ ] Missing information is recorded as a condition with a reason and candidate existing action.
- [ ] Previous actions are listed in chronological order and failures are preserved.
- [ ] Every attempted action uses one of the frozen 13 actions.
- [ ] Result labels distinguish failed, partially helped, improved, resolved, attempted, and unknown.
- [ ] Strong failure wording is cited when an action is marked failed.
- [ ] `OBSERVED_NEXT_ACTION` records what support actually did next, not what should have happened.
- [ ] `IDEAL_NEXT_ACTION`, if used, is separate from the observed target.
- [ ] A DM request or handoff was not treated as successful resolution.
- [ ] Outcome and evidence visibility are recorded separately.
- [ ] Escalation eligibility is based on risk and evidence boundaries, not LLM confidence.
- [ ] Ambiguous, incomplete, generic, or invisible evidence has a reason code.
- [ ] Confidence reflects the evidence quality and is not used to force a label.
- [ ] The example is not a duplicate or near-duplicate of another locked golden example.
- [ ] Conversation identity, source references, split membership, and exclusion status are preserved.
- [ ] No unseen policy, backend state, private DM content, or current product truth was inferred.

## Frozen annotation principles

1. Intent and troubleshooting state are separate.
2. Missing information is a condition, not a state.
3. Previous failed actions are durable context.
4. Support actions are explicitly represented.
5. `RESOLVED` and `MONITORING` are distinct.
6. Historical observed action is different from ideal recommended action.
7. DM or handoff is not proof of resolution.
8. Unknown is preferable to an unsupported guess.
9. Evidence-aware automation is a system decision, not an annotation shortcut.
