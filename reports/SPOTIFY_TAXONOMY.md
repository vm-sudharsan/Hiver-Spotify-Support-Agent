# SpotifyCares Taxonomy: Intent, State, and Action

## Purpose and evidence base

This taxonomy is for describing observed SpotifyCares support journeys before any AI system is built. It separates:

- **Customer intent** — the problem or goal that caused the customer to contact support.
- **Troubleshooting state** — where that case currently sits in a support journey.

It is based on the reconstructed SpotifyCares analysis: 24,568 threads, 72,030 messages, and manually reviewed linked troubleshooting journeys. Frequencies are approximate first-match, rule-based estimates from root customer tweets; they are not LLM classifications. The categories are deliberately broad enough to be evaluated and refined later.

## A. Proposed customer-intent taxonomy

About 31.2% of roots were not captured by the deliberately small keyword rules. That is an evidence limitation, not a proposed “other” intent. The ten intents below cover the recurring, operationally distinct problem families found in the sampled conversations.

### 1. Playback reliability

- **Definition:** music will not start, pauses, skips, stutters, crashes, or behaves inconsistently during playback.
- **Approximate frequency:** 2,767 roots (about 11.3%; combined app/device-function and explicit playback wording).
- **Representative customer messages:**
  1. “My only Halloween song won’t play and I’m starting to get upset.”
  2. “My web player is stuck in a commercial. ‘Play’ isn't an option.”
  3. “My music keeps stuttering/skipping ever since I upgraded to iOS 11.”
  4. “Songs by Prince and Robin Thicke won't play on my ... phone.”
  5. “It pauses every 20 secs ... won't cast to chromecast or ps4 either.”
- **Could be confused with:** content availability when only one artist/track fails; connected-device integration when playback fails only through a speaker.
- **Why distinct:** its first-line workflow is environment and symptom diagnosis (device/OS/version, error, network, other device) followed by recovery steps.

### 2. App, device, and platform behavior

- **Definition:** an app UI, login screen, battery use, controls, crash, or platform-specific feature behaves incorrectly without a primarily playback-focused report.
- **Approximate frequency:** 2,703 roots (11.0%).
- **Representative customer messages:**
  1. “doesn’t work and i even tried deleting the app.”
  2. “the app is killing [my] phone battery.”
  3. “the new iOS is making your app way less usable.”
  4. “there is no way to manage Albums ... in the App. It's a mess.”
  5. “Groove Music quits & redirect to Spotify. But the W10M App is a bugfest.”
- **Could be confused with:** playback reliability; download/offline issues when the app is the visible surface of the failure.
- **Why distinct:** platform and version are central evidence, and support often needs screenshot/UI reproduction rather than a catalog or subscription check.

### 3. Content or catalog availability

- **Definition:** a particular song, artist, album, or track is unavailable, greyed out, or inconsistent by territory.
- **Approximate frequency:** 2,436 roots (9.9%).
- **Representative customer messages:**
  1. “did you take [this song] off spotify?”
  2. “only three of [the artist's] songs will play, the others are not working.”
  3. “why can’t I listen to Dua Lipa?”
  4. “this album ... is not playable.”
  5. “tracks are greyed out.”
- **Could be confused with:** playback reliability, especially when only one artist will not play; playlist/library issues.
- **Why distinct:** Spotify consistently asks for a song link/URI, country, and whether the issue affects specific artists before deciding whether to investigate catalog/backend state.

### 4. Playlist, library, and music organization

- **Definition:** a customer wants to find, order, save, manage, shuffle, repeat, or otherwise organize music and playlists.
- **Approximate frequency:** 3,349 roots (13.6%).
- **Representative customer messages:**
  1. “is there a way to find non-explicit songs that are explicit?”
  2. “why are [an artist's] releases ... missing?”
  3. “move songs around so they're in my order and not the order of when I added them.”
  4. “shuffle and repeat button just don’t ... work.”
  5. “I only want that one local file visible in the playlist.”
- **Could be confused with:** catalog availability if library entries are unavailable; download/offline if local files are involved.
- **Why distinct:** the support goal is often instruction or product behavior explanation, not repair of a device/account fault.

### 5. Premium, subscription, and plan status

- **Definition:** Premium activation, upgrade, trial, cancellation, renewal, or a mismatch between paid and free-plan status.
- **Approximate frequency:** 3,955 roots (16.1%).
- **Representative customer messages:**
  1. “my spotify premium stopped working.”
  2. “I'm paying for premium but every time i log in it keeps saying free service.”
  3. “Im already a premium user can i still avail this promo?”
  4. “my subscription had been cancelled?”
  5. “I have a free account. I want to upgrade via the 3 month offer.”
- **Could be confused with:** billing/payment when the concern is a charge; family/student where eligibility is the issue.
- **Why distinct:** the primary outcome is plan entitlement/status, usually needing account lookup rather than device troubleshooting.

### 6. Billing, payment, refund, and card issues

- **Definition:** duplicate/incorrect charges, card errors, payment method problems, refund requests, or charge disputes.
- **Approximate frequency:** 1,185 roots (4.8%).
- **Representative customer messages:**
  1. “y'all charged my account 8 times.”
  2. “my card was charged twice, and i am not even upgraded.”
  3. “Help on my spotify card please.”
  4. “keep getting charged for an account that is on the free subscription.”
  5. “card bad day error” when trying to buy Premium.
- **Could be confused with:** Premium status and account compromise.
- **Why distinct:** it is financially sensitive and requires a secure account/payment workflow, not public technical troubleshooting.

### 7. Account access, identity, and security

- **Definition:** inability to sign in, password/email problems, Facebook-linked access, account takeover, or profile/country identity issues.
- **Approximate frequency:** 1,656 roots (6.7%; access/password plus account/profile/country).
- **Representative customer messages:**
  1. “I can't log into my account ... password is incorrect.”
  2. “Some idiot hacked my Spotify account and changed my email.”
  3. “Will changing my password stop this person from using my [account]?”
  4. “I login with facebook ... [but] my email account ... is now defunct.”
  5. “account was locked as soon as I tried to login.”
- **Could be confused with:** Premium/billing when access blocks a plan; connected integrations when Facebook authentication is involved.
- **Why distinct:** privacy and security make private account verification the central next action.

### 8. Family and student eligibility

- **Definition:** Family-plan invitation/address problems, student verification, or discount/eligibility questions.
- **Approximate frequency:** 816 roots (3.3%).
- **Representative customer messages:**
  1. “friends invited me on spotify family ... something went wrong.”
  2. “fix ... problem in managing family accounts.”
  3. “trying to verify that I'm a student again but the pop up doesn't do anything.”
  4. “family premium account has stopped working, even though we have paid.”
  5. “student deals are only for college/uni kids.”
- **Could be confused with:** Premium plan status or account identity.
- **Why distinct:** eligibility, invitation, and address/verification rules are a coherent account-policy workflow.

### 9. Downloads and offline listening

- **Definition:** downloading, offline visibility, local files, storage, or managing downloaded music.
- **Approximate frequency:** 224 roots (0.9%).
- **Representative customer messages:**
  1. “I only want that one local file visible ... It wasn't until I said download [that] it appeared.”
  2. “give me the option to offline/download the song.”
  3. “download nearly 100MB ... each week or two.”
  4. “shuffle all download music in one touch?”
  5. “songs downloaded to my phone [but the issue persists].”
- **Could be confused with:** playback reliability and library organization.
- **Why distinct:** offline storage/state is a separate diagnostic surface with distinct actions and limitations.

### 10. Ads and free-tier experience

- **Definition:** ad frequency, ad-free benefit, ad content, promotion eligibility, or free-tier advertising behavior.
- **Approximate frequency:** 339 roots (1.4%).
- **Representative customer messages:**
  1. “30 mins ad free ... Not 10 mins.”
  2. “Stop showing me diaper ads. I don't have a baby.”
  3. “advertising a sale to me for which I’m geographically ineligible.”
  4. “the ad interrupted the music I had streaming at work.”
  5. “any way to block this particular ad? Happy with ads/don't want premium.”
- **Could be confused with:** Premium subscription or playback interruption.
- **Why distinct:** the goal is ad/promotion behavior or policy feedback, not account entitlement or a playback repair.

**Connected-device integration** (Bluetooth, Sonos, Chromecast, Echo/Alexa, Facebook linking) is retained as a **cross-cutting context field**, rather than an eleventh intent. It changes the workflow for playback and account-access cases but is usually not the customer’s ultimate goal. It appeared in about 168 roots (0.7%) under the narrow rule.

## B. Proposed troubleshooting states

| State | Definition and evidence | Typical next support action |
|---|---|---|
| `SYMPTOM_REPORTED` | Customer states a problem but has not supplied enough discriminating context. Example: “my web player is stuck in a commercial.” | Ask what happens, exact error, platform, onset, scope. |
| `CONTEXT_COLLECTED` | Customer provides relevant facts, e.g., iPhone/iOS/version, other device works, one artist only, or Wi-Fi versus cellular. | Choose a branch-specific action. |
| `FIRST_LINE_ACTION_PROPOSED` | Support gives a reversible action: logout/login, restart, test another browser/device/network, or a help link. | Wait for result; avoid introducing unrelated steps. |
| `ACTION_RESULT_REPORTED` | Customer says the step worked, partly changed behavior, or did not work. Explicit failure wording appears in 19.5% of threads. | Confirm resolution, narrow diagnosis, or advance the action ladder. |
| `REPEATED_FAILURE_OR_BROADER_INCIDENT` | Multiple attempts fail, issue spans devices/networks/users, or customer reports persistent recurrence. Examples: unavailable artists after reinstall; cross-device pausing. | Collect more discriminating evidence, stop repeating the same step, escalate or use secure account check. |
| `PRIVATE_ACCOUNT_CONTEXT_REQUIRED` | Username/email, plan/billing, entitlement, or account-security data is needed. Explicit DM handoff appears in 32.5% of threads. | Explain the privacy boundary and move to DM/secure support. |
| `SPECIALIST_OR_PRODUCT_INVESTIGATION` | Support says developers/technical staff are investigating, or passes feedback to the relevant team. | Set expectation, avoid promising a fix, capture evidence, monitor/update. |
| `RESOLVED` | Customer explicitly indicates that the issue is fixed or resolved. | Confirm the outcome and close the journey when appropriate. |
| `MONITORING` | The issue appears improved, or support asks the customer to monitor whether it recurs, but there is no explicit confirmation of resolution. | Provide recurrence guidance and remain ready to continue if the issue returns. |

These are journey states, not intents. Missing diagnostic information is a condition, not a journey state: after a customer reports a symptom, the system identifies what information is missing and uses a support action to ask for it. Once the customer provides it, the journey moves to `CONTEXT_COLLECTED`. This condition occurs in 44.8% of reconstructed threads and may involve device/OS/version/browser, song link, country, network, screenshot, or account context.

The distinction is:

- **Journey state:** the case's position in the troubleshooting journey, such as `SYMPTOM_REPORTED` or `CONTEXT_COLLECTED`.
- **Missing-information condition:** required diagnostic context has not yet been supplied.
- **Support action:** the explicit operation used to obtain or act on information, such as `ASK_PLATFORM_CONTEXT` or `ASK_SYMPTOM_EVIDENCE`.

For example, a **content availability** case can move through `SYMPTOM_REPORTED` → missing catalog context condition → `ASK_CATALOG_CONTEXT` → `CONTEXT_COLLECTED` → `FIRST_LINE_ACTION_PROPOSED` → `REPEATED_FAILURE_OR_BROADER_INCIDENT` → `SPECIALIST_OR_PRODUCT_INVESTIGATION`.

## C. Controlled vocabulary of recurring support actions

| Action | Meaning | Evidence in threads |
|---|---|---|
| `ASK_PLATFORM_CONTEXT` | Ask device, OS, Spotify version, browser, or app version. | “What device, operating system, and Spotify version?” |
| `ASK_SYMPTOM_EVIDENCE` | Ask exact symptom, error, screenshot, crash state, greyed-out state, or onset. | “Are you getting any error messages?” |
| `ASK_SCOPE_OR_ENVIRONMENT` | Test another device, artist, browser/incognito session, Wi-Fi/3G/4G, connection, speaker/car context. | “Is this happening via WiFi, 3G/4G, or both?” |
| `ASK_CATALOG_CONTEXT` | Ask song link/URI and account country. | “Can you send us a Song Link ... What country is your account set to?” |
| `SESSION_RESET` | Log out, restart device, log back in. | Repeated first-line sequence in playback cases. |
| `REINSTALL_OR_CLEAN_INSTALL` | Direct customer to reinstall or clean-reinstall steps. | Used after simpler attempts fail. |
| `BROWSER_REMEDIATION` | Try another browser/incognito, update browser, clear cache/cookies. | Chrome web-player skipping case. |
| `NETWORK_REMEDIATION` | Compare Wi-Fi/cellular/another connection or restart connection. | Cross-device pausing cases. |
| `PROVIDE_HELP_RESOURCE` | Provide a help/reinstall/support link. | Links occur in 66.1% of reconstructed threads. |
| `REQUEST_SECURE_ACCOUNT_DETAILS` | Request username/email or other account details privately. | “DM us your account's username and email address.” |
| `MOVE_TO_DM_OR_SECURE_CHANNEL` | Continue after public triage in DM. | Present explicitly in 32.5% of threads. |
| `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE` | Report to developers/tech team or state an investigation is active. | Used after repeated/cross-environment failure. |
| `CONFIRM_AND_MONITOR` | Acknowledge working outcome and ask customer to return if it recurs. | “Glad to hear it worked ... if it happens again.” |

## D. Recurring state transitions from real conversations

| State A | Support action | Customer feedback | State B |
|---|---|---|---|
| `SYMPTOM_REPORTED`: web player skips songs | `ASK_SCOPE_OR_ENVIRONMENT`: try another browser/incognito | Firefox works; Chrome still skips | `CONTEXT_COLLECTED` |
| `CONTEXT_COLLECTED`: Chrome current, no error | `BROWSER_REMEDIATION`: clear cache/cookies | “seems to have worked so far” | `MONITORING` |
| `SYMPTOM_REPORTED`: one artist unavailable | `ASK_PLATFORM_CONTEXT` | iPhone, iOS, version supplied | `CONTEXT_COLLECTED` |
| `CONTEXT_COLLECTED` | `SESSION_RESET` | “No luck ... tried downloading” | `ACTION_RESULT_REPORTED` |
| `ACTION_RESULT_REPORTED` | `REINSTALL_OR_CLEAN_INSTALL` | “Still no luck” | `REPEATED_FAILURE_OR_BROADER_INCIDENT` |
| `REPEATED_FAILURE_OR_BROADER_INCIDENT` | `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE` | Later customer says music works again | `RESOLVED` |
| `SYMPTOM_REPORTED`: Echo/Sonos linkage blocks phone playback | `ASK_SYMPTOM_EVIDENCE` | account-used-elsewhere message; no audio active | `CONTEXT_COLLECTED` |
| `CONTEXT_COLLECTED` | Explain one-stream rule + `PROVIDE_HELP_RESOURCE` | customer says explanation does not fit | `REPEATED_FAILURE_OR_BROADER_INCIDENT` |
| `REPEATED_FAILURE_OR_BROADER_INCIDENT` | `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE` | Spotify says feedback goes to developers | `SPECIALIST_OR_PRODUCT_INVESTIGATION` |
| `SYMPTOM_REPORTED`: login loop after reinstall | `ASK_PLATFORM_CONTEXT` + screenshot | iPhone/iOS/screenshot and repeated failure supplied | `CONTEXT_COLLECTED` |
| `CONTEXT_COLLECTED` | `SESSION_RESET`/reinstall and other-device question | blank screen persists; customer declines irrelevant test | `REPEATED_FAILURE_OR_BROADER_INCIDENT` |
| `REPEATED_FAILURE_OR_BROADER_INCIDENT` | `MOVE_TO_DM_OR_SECURE_CHANNEL` | account details requested | `PRIVATE_ACCOUNT_CONTEXT_REQUIRED` |
| `SYMPTOM_REPORTED`: songs pause across phone/Chromecast/PS4 | `ASK_SCOPE_OR_ENVIRONMENT` | all connections; began after Android update | `CONTEXT_COLLECTED` |
| `CONTEXT_COLLECTED` | `SESSION_RESET` then `REINSTALL_OR_CLEAN_INSTALL` | partial cast change, control still fails | `REPEATED_FAILURE_OR_BROADER_INCIDENT` |
| `REPEATED_FAILURE_OR_BROADER_INCIDENT` | `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE` | developer notification; customer asked to monitor | `SPECIALIST_OR_PRODUCT_INVESTIGATION` |

## E. Automation boundaries supported by the data

### Suitable for automatic handling

- Asking for missing diagnostic context and avoiding questions already answered.
- Selecting a low-risk first-line action for clearly scoped playback/app/browser cases.
- Guiding browser, cache/cookie, session-reset, and environment-comparison steps.
- Asking for URI/country for a content-availability case.
- Explaining why a secure channel is required and summarizing attempts before handoff.
- Confirming a reported success and providing recurrence guidance.

### More appropriate for human or specialist escalation

- Account compromise, password/email ownership, payment/refund, Premium entitlement, and Family-plan address/eligibility issues.
- Repeated failure after the documented action ladder.
- Cross-device/network failures suggesting an app, catalog, or platform incident.
- Country/rights/catalog issues and product-design feedback.
- Any case requiring private account lookup, backend state, or a promise of remediation.

### Evidence insufficient for confident automation

- Whether a DM case was actually resolved: public resolution is visible in only 15.2% of reconstructed threads.
- Current validity of 2017 product versions, help links, policies, or catalog availability.
- Internal incident status, account state, and support actions occurring outside Twitter.
- A definitive “best” action when the customer has supplied inconsistent or incomplete facts.

## F. Final proposed taxonomy

### Intents: 10

1. Playback reliability
2. App, device, and platform behavior
3. Content or catalog availability
4. Playlist, library, and music organization
5. Premium, subscription, and plan status
6. Billing, payment, refund, and card issues
7. Account access, identity, and security
8. Family and student eligibility
9. Downloads and offline listening
10. Ads and free-tier experience

Connected-device integration is a cross-cutting context attribute used to branch playback/access workflows rather than a separate primary intent.

### States: 9 journey states

`SYMPTOM_REPORTED`, `CONTEXT_COLLECTED`, `FIRST_LINE_ACTION_PROPOSED`, `ACTION_RESULT_REPORTED`, `REPEATED_FAILURE_OR_BROADER_INCIDENT`, `PRIVATE_ACCOUNT_CONTEXT_REQUIRED`, `SPECIALIST_OR_PRODUCT_INVESTIGATION`, `RESOLVED`, `MONITORING`.

Diagnostic context needed is a missing-information condition, handled through an explicit support action, not an additional journey state.

### Actions: 13

`ASK_PLATFORM_CONTEXT`, `ASK_SYMPTOM_EVIDENCE`, `ASK_SCOPE_OR_ENVIRONMENT`, `ASK_CATALOG_CONTEXT`, `SESSION_RESET`, `REINSTALL_OR_CLEAN_INSTALL`, `BROWSER_REMEDIATION`, `NETWORK_REMEDIATION`, `PROVIDE_HELP_RESOURCE`, `REQUEST_SECURE_ACCOUNT_DETAILS`, `MOVE_TO_DM_OR_SECURE_CHANNEL`, `ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE`, `CONFIRM_AND_MONITOR`.

This taxonomy is small enough to annotate and evaluate: ten broad intents, nine observable states, and thirteen action types. It remains expressive because intent answers **what** the customer needs, state answers **where** the journey is, and action answers **what support should do next**. That three-part distinction captures the repeated Spotify troubleshooting journeys without creating a fragile category for every device, artist, or wording variation.

## Frozen Design Principles

1. Intent and troubleshooting state are separate concepts.
2. Missing diagnostic information is a condition/requirement, not a journey state.
3. Previous failed actions must be preserved as state/context.
4. Support actions are explicitly represented.
5. `RESOLVED` and `MONITORING` are distinct.
6. Automation should be evidence-aware.
7. Insufficient, conflicting, private, or high-risk cases should be eligible for escalation.
