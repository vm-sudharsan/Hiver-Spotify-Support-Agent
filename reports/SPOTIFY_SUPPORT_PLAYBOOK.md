# SpotifyCares Support Playbook Evidence

## Decision

**Hypothesis: SUPPORTED.**

Historical SpotifyCares threads support a system that predicts a reasonable **next support action**—not just a similarly worded reply—because the same observable workflow recurs: collect diagnostic context, choose a reversible troubleshooting step, inspect the customer’s result, gather more discriminating evidence or change the step, then move to secure/specialist handling when needed.

This is support for a scoped triage-and-next-action system, not for autonomous resolution of account, billing, rights/catalog, or backend incidents.

## Method and scope

The raw `twcs.csv` file was read without modification. Threads were conservatively reconstructed from an inbound root with no in-file parent whose `response_tweet_id` leads to SpotifyCares; descendants were followed through `in_response_to_tweet_id`.

- Reconstructed SpotifyCares threads: **24,568**
- Messages in those threads: **72,030**
- Average messages per thread: **2.93**
- Multi-turn threads (at least two customer and two company messages): **6,166 (25.1%)**

Intent estimates use explicit first-match keyword rules on the initial customer tweet. They are not LLM labels and are intentionally approximate: natural-language categories overlap, and 31.2% of roots remain “other/unclear” under this narrow rule set.

## 1. Common customer problem categories

| Category | Approx. threads | Typical thread length | Representative customer evidence |
|---|---:|---:|---|
| Premium/subscription | 3,955 (16.1%) | 2.48 | “my spotify premium stopped working”; “can't log on to my premium account” |
| Playlist/library | 3,349 (13.6%) | 3.14 | missing releases; album is present but not playable |
| Device/app behavior | 2,703 (11.0%) | 3.64 | app draining battery; iOS update made app less usable |
| Content availability | 2,436 (9.9%) | 3.25 | artist/track removed or unavailable in a region |
| Billing/payment | 1,185 (4.8%) | 2.32 | account charged repeatedly; card error buying Premium |
| Login/password | 919 (3.7%) | 2.38 | unable to access account; password reset still fails |
| Family/student plan | 816 (3.3%) | 2.34 | family invite/verification error; student re-verification |
| Account/profile/country | 737 (3.0%) | 2.44 | account hacked; email/country/profile problem |
| Ads/free plan | 339 (1.4%) | 3.12 | promised ad-free interval too short; unwanted ads |
| Download/offline | 224 (0.9%) | 3.36 | downloads repeat or offline library behavior fails |
| Connect/speaker integration | 168 (0.7%) | 3.95 | Bluetooth/Echo/Sonos/Facebook connection issue |
| Explicit playback/streaming wording | 64 (0.3%) | 3.95 | web player stuck; songs skipping/not playing |

The low explicit playback count is a rule artifact: many playback reports use device, artist, or app wording and are captured in those overlapping categories. The multi-step samples below show playback and availability are operationally important despite that narrow count.

## 2. Recurring support actions and diagnostics

### Diagnostic information requested

Spotify repeatedly asks for:

- **Device and OS:** “What device, operating system, and Spotify version?”
- **App/browser version:** app version, Chrome/browser, incognito testing, screenshot.
- **Network/environment:** Wi-Fi versus 3G/4G, another network, another device, speaker/car/Bluetooth state.
- **Account context:** username/email by DM; account country; Family-plan or account status.
- **Symptom details:** error text, screenshot, whether the issue affects another artist/device, whether tracks are greyed out, song link/URI.
- **Prior attempts and timing:** whether restart/reinstall/log-out was tried, whether an update preceded the failure, and what changed.

### Troubleshooting actions observed

| Action | Marker count in 34,725 company messages | Typical use |
|---|---:|---|
| Diagnostic question marks | 17,897 | Gather discriminating context before selecting a branch |
| Requests for device/version/error/account context | 8,465 | Device/OS/version, error, screenshot, details |
| Restart | 1,101 | Early, reversible device recovery |
| Log out / log in | 925 | Account/session playback issues |
| Reinstall | 436 | After simpler session/device checks fail |
| Browser troubleshooting | 388 | Browser, incognito, supported browser, cache/cookies |
| Cache/cookie handling | 131 | Web-player-specific branch |
| Network/connection checks | 156 | Wi-Fi vs cellular, alternate connection |
| Links/resources | 17,839 | Reinstall/help/DM/resource instructions |
| Explicit DM request | 8,063 | Private account lookup or continued handling |
| Technical/specialist escalation markers | 627 | “tech folks,” investigation, report/feedback to developers |

Counts overlap and are textual markers, not mutually exclusive actions. They are still strong evidence that Spotify responses contain more than generic empathy: links occur in 51.4% of company messages, and an explicit troubleshooting marker occurs in 8.6% under this conservative wording rule.

## 3. Estimated thread-level behavior

| Evidence in a reconstructed thread | Threads | Approx. share | Interpretation |
|---|---:|---:|---|
| At least one support question | 12,508 | 50.9% | Diagnostic questioning is common |
| Device/version/error/account information request | 11,018 | 44.8% | Structured context collection is common |
| Link/resource | 16,241 | 66.1% | Help, reinstall, or secure-channel instructions are frequent |
| Explicit DM handoff | 7,973 | 32.5% | Private follow-up is a major boundary |
| Concrete troubleshooting wording | 2,407 | 9.8% | Conservative lower bound; misses implicit advice |
| Customer explicitly reports failure | 4,802 | 19.5% | Material population for next-step/adaptation learning |
| Specialist/technical escalation marker | 606 | 2.5% | Public escalation is visible but uncommon |
| Visible resolution/thanks/working marker | 3,723 | 15.2% | Closure is under-observed, often after DM |

“Adaptation after failure” cannot be precisely measured with a single keyword count. A conservative marker from the prior full scan found 527 explicit change-of-approach phrases (about 1.5% of company messages). The linked journeys below show stronger semantic adaptation: after “no luck” or “nothing changed,” Spotify moves from restart/login to reinstall, asks a different discriminating question, requests private account context, or escalates.

## 4. Multi-step troubleshooting journeys

The following are abbreviated actual linked threads, arranged in conversational order.

1. **Chrome web-player skipping — visible resolution**

   Customer symptom: songs randomly skip in Chrome web player.
   → Support diagnostic question: browser and incognito/another-browser test.
   → Customer information: Firefox works; Chrome is current; no error message.
   → Support action: supported-browser link, then clear cache/cookies and reinstall Chrome.
   → Customer result: “clearing cache/cookies seems to have worked so far.”
   → Next support action: confirms success and invites return if it recurs.

2. **Artist unavailable on iPhone — step change and escalation**

   Customer symptom: Lana Del Rey music does not play on iPhone SE.
   → Diagnostic: device/OS; whether other artists work.
   → Information: other artists play; login/restart and download also fail.
   → Action: reinstall link.
   → Result: “Still no luck.”
   → Next action: moves to technical-team investigation; later customer reports music working again.

3. **Account linked to Echo/Sonos — product-rule clarification**

   Customer symptom: linking Echo/Sonos prevents phone and desktop playback, despite no active audio.
   → Diagnostic: whether devices play simultaneously; exact error.
   → Information: account-used-elsewhere message; clearing Alexa link restores phone/desktop.
   → Action: explain one-stream-at-a-time behavior and give resource link.
   → Result: customer clarifies the speaker was stopped, so the explanation does not fully fit.
   → Next action: Spotify passes the case to developers.

4. **iPhone login screen loops — narrowing and secure handoff**

   Customer symptom: iPhone app login screen loops after reinstall.
   → Diagnostic: exact device/OS, screenshot, other-device behavior.
   → Information: iPhone 7 Plus/iOS 11.0.2, repeated reinstall, partial back-button workaround.
   → Action: remove app, restart device, reinstall; then different-network question.
   → Result: persistent blank screens; customer declines unrelated desktop testing.
   → Next action: Spotify narrows back to phone and requests account details by DM.

5. **Metallica unavailable — escalation after failed sequence**

   Customer symptom: cannot play any Metallica on iPhone 7.
   → Diagnostic: device/OS/version, then whether logout/restart helps.
   → Information: iOS 11.0.3; logout/restart already tried.
   → Action: reinstall link.
   → Result: still unavailable for that artist.
   → Next action: Spotify says it is investigating and requests account details via DM.

6. **Artist availability on Android — evidence collection then DM**

   Customer symptom: selected artists fail on Samsung Galaxy A5.
   → Diagnostic: song link, country, device/OS/app version, greyed-out state/error.
   → Information: Ireland, Android 7.0, app version, “song is not available.”
   → Action: log out/in and restart.
   → Result: “Neither worked.”
   → Next action: requests username/email by DM for account-side investigation.

7. **Cross-device playback pauses — network branch then escalation**

   Customer symptom: playback pauses every 20 seconds on Android, Chromecast, and PS4.
   → Diagnostic: version, Wi-Fi versus cellular, restart connection.
   → Information: all connections; saved songs; casting behavior; issue began after Android update.
   → Action: logout/restart/login, then reinstall link.
   → Result: partial change in casting but remaining control failure.
   → Next action: notify developers and request outcome after reinstall.

8. **iPhone crash after clean reinstall — adaptation to relapse**

   Customer symptom: music pauses then crashes after one song.
   → Diagnostic: device, Spotify/iOS version, onset, Wi-Fi/3G/4G.
   → Information: iPhone SE, iOS 10.0.2, all networks, near a recent update.
   → Action: clean reinstall link.
   → Result: customer first says it worked, then immediately says it still happens.
   → Next action: does not repeat reinstall; requests username/email for closer account inspection.

9. **Dua Lipa intermittent playback — progressive evidence gathering**

   Customer symptom: one artist intermittently stops/does not start.
   → Diagnostic: all songs or one artist, country, device/OS/version, error, other artists.
   → Information: US, iPhone 6S/iOS 11, no error; logout/login did not help.
   → Action: reinstall steps.
   → Result: reinstall did not solve it.
   → Next action: DM account details for backend check.

10. **iOS skipping with Bluetooth/car context — avoid repeating failed advice**

   Customer symptom: music stutters/skips after iOS 11, particularly during network changes/car use.
   → Diagnostic: Wi-Fi versus cellular, other devices, car-stereo condition.
   → Information: reinstall and logout/restart failed; issue is iPhone-specific; customer shares video.
   → Action: asks targeted environment questions rather than repeating reinstall.
   → Result: customer agrees to test in different use conditions.
   → Next action: keep monitoring and continue once discriminating evidence returns.

## 5. Explicit “that did not work” behavior

Customer failures are not rare: 4,802 reconstructed threads (19.5%) have an explicit failure marker such as “still,” “no luck,” “nothing changed,” “didn't work,” or “cannot.” In the ten journeys above, Spotify usually does one of four things:

| Customer feedback | Observed Spotify response | Assessment |
|---|---|---|
| Restart/login did not help | Reinstall, gather URI/country, or ask a different symptom question | Changes the step |
| Reinstall did not help | Request username/email by DM or escalate to technical staff | Escalates/hands off |
| Alternate browser works but original does not | Focus on browser support/version/cache/cookies | Narrows the hypothesis |
| Symptom persists across devices/networks | Recognize likely broader issue and notify developers | Changes from local troubleshooting to incident handling |
| Customer says a fix first worked, then relapsed | Stop repeating the same step; request private account context | Adapts to new evidence |

There are cases where Spotify repeats a broadly similar family of advice—logout/restart/reinstall is a common sequence—and public “tech folks are investigating” language can be generic. But the representative linked sequences show meaningful non-repetition once a customer supplies evidence that the preceding step failed.

## 6. Strongest recurring playbook patterns

1. **Environment-first technical triage:** device + OS + app/browser version + exact symptom/error.
2. **Low-risk recovery ladder:** logout/login and restart before clean reinstall; browser/cookie checks for web-player cases.
3. **Discriminating tests:** other device, other network, Wi-Fi versus mobile data, another browser/incognito, speaker/car/Bluetooth condition, another artist.
4. **Catalog/availability branch:** song link/URI + country + account state before account/backend investigation.
5. **Account-safe handoff:** username/email only through DM after public technical context is collected.
6. **Incident boundary:** cross-device or multi-user failure after standard steps becomes technical-team/developer investigation rather than more generic self-service advice.

## 7. Can these conversations support next-action prediction?

**Yes, for a constrained support playbook.** A next-action system could predict actions such as:

- request device/OS/version/error details;
- ask whether the issue occurs on another device, network, browser, or artist;
- recommend restart/logout-login/reinstall/cache clearing in an ordered sequence;
- request song URI and country for availability problems;
- request secure account details by DM;
- summarize attempts and route to technical escalation.

The evidence is not merely lexical similarity. The next action depends on **state accumulated within the thread**: what device is involved, what has been tried, whether a different environment works, whether the symptom is artist-specific, and whether the customer has explicitly reported failure. The Chrome cache success, iPhone reinstall relapse, and cross-device availability examples all require that state to choose a sensible next action.

## 8. Dataset limitations and reliability risks

- **Incomplete endings:** only 15.2% of reconstructed threads contain visible resolution/thanks/working markers; DM and backend outcomes are frequently absent.
- **Conservative reconstruction:** external/missing relationship IDs and thread-depth limits can omit context or split a conversation.
- **Public-data privacy boundary:** account email/username, billing, and security cases must not be handled publicly.
- **Historical product drift:** 2017 devices, app versions, links, policies, and catalog state may no longer apply.
- **Generic support language:** some “we are looking into it” replies do not demonstrate a precise underlying action.
- **No ground-truth action labels:** next-action labels would need careful, rule-based or human annotation; the raw reply itself is not always a single action.
- **Incident versus individual issue ambiguity:** repeated reports may signal a platform/content incident, but the dataset does not expose internal incident state.

## Conclusion

The data supports the selected hypothesis and provides a credible basis for a future stateful support-playbook system: it can learn to select the next diagnostic question, troubleshooting branch, secure handoff, or escalation based on prior conversation evidence. Its realistic objective should be **high-quality next-step guidance and escalation**, not guaranteed autonomous resolution.
