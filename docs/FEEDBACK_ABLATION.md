# Frozen local feedback ablation - 27 October 2026

## Protocol declared before real execution

This user-authorized follow-up supersedes the earlier proposed normal/lost
one-seed design: exactly **four new lost-confirmation trials**, seeds 101 and 202,
both feedback variants run again. No historical result substitutes for any slot.

A: exact current UNKNOWN guard feedback at commit aeba563:

```text
Recovery guard: business outcome UNKNOWN. Further writes are BLOCKED. Use read-only browser interaction to inspect visible state. A search alone is insufficient: a fresh visible row must match the submitted name, email and company together. Finish unsuccessfully if this cannot be established.
```

B: identical A text followed by a newline and exactly this clarification:

```text
Finding text or scrolling only examines the currently loaded page.
To verify an uncertain submission, use the application's search or
refresh mechanism to retrieve current records, then inspect the
matching record's visible details. Do not resubmit while uncertain.
```

Task wording remains the original neutral version 1.1.0 instruction. No fault,
database state, evaluator assertion or seed value is passed to the feedback
presentation layer. Only the guard's existing browser-observable UNKNOWN state
and existing UNKNOWN action-result text trigger the clarification. Idle,
confirmed and terminal messages remain identical. Guard and grader files are
verified byte-equivalent (with Git line-ending normalization) to aeba563.
A passive wrapper records feedback events for both arms; only B's existing
UNKNOWN tool-result text is extended. No guard decision, matching, freshness,
automatic recovery action or extra tool is introduced.

Same qwen3:8b-q4_K_M model/digest, Browser Use 0.13.11, Ollama SDK, permitted
browser-action list, 16384 context, 2048 output tokens/call, 12 calls/steps,
300-second worker deadline, one request, think=false, temperature 0, model seed 42.
No dependency upgrade or paid model. Local provider API charges are zero;
electricity/hardware costs are unmeasured. Model seed does not imply determinism.

Reuse existing seeded block scheduler, ordering seed **4**; predeclared order:
**B/101, A/101, A/202, B/202**. Each variant is first once. Both arms use identical
initial-data snapshots for each seed, fresh DB/server/browser/profile/context.
The long-lived Ollama server and prefix cache are shared, with no flush; routing
disables browser HTTP cache in both arms. Timings are not isolated and model
behavior is not assumed deterministic. Exact texts, settings, canonical JSON
configuration hashes, source hashes, task text, versions and prior-artifact
inventory are frozen in manifest.json before --execute can dispatch.

One attempt per slot; no tuning, retry, resume or replacement. Stop on
infrastructure, usage/accounting, frozen-settings or preservation problems, retaining
all attempted and unstarted records. Source/manifest integrity is checked before
each dispatch. Any repair requires a separate record and a replacement proposal;
it does not authorize continuing or rerunning this experiment.

## Prespecified mechanism/outcome analysis

For each slot retain trace network GET/POST observations, guard fresh-read events,
visible row details and reconciliation separately. A fresh GET or a record in an
API response alone is not visible record evidence. A guard visible-row event is
DOM-observed submitted-record evidence; operator analysis separately checks that
those details match the requested task record, never feeding assertions back to
runtime. If no such observation exists, visibility is not established until
retained screenshots/DOM evidence can support a more specific conclusion.

Independent committed DB grade/duplicate issue stays separate from guard workflow
confirmed/unresolved/failed, original agent claims, completion interceptions,
blocked requests, raw termination, call-ceiling flags, native usage and duration.
No scripted-control result enters real-agent statistics. Two seeds/one task/model
and a feedback-only contrast are exploratory, not proof of reliability or a
causal performance claim. Prior service-worker/other-context limitations remain.

## Preparation verification

Provider interactions in preflight tests are mocked; real Chromium tests verify
A/B delivery, no treatment outside observable uncertainty, unchanged terminal
feedback and independent grading. A test originally compared Python repr rather
than actual delivered strings; its escaped apostrophe/newline assertion was
corrected before freezing. Runtime delivery required no repair or tuning. No
real-agent call had started at that point.

Full suite results, frozen hashes and observed outcomes will be appended below.


## Frozen manifest and completed execution

Canonical configuration SHA-256:

- A: `5ea0f6567fd10322216efe6060b296291fa02f58d8a7601843a9e109a173b25a`.
- B: `cd788fed535ed15f51d131d79fceec357f803d0af52b584e0d687aa449acdfea`.
- Manifest: `93121395373fa509556e1432b2b79460310f55714e74c2640b51fa0a6ab28d12`.

The base guard and grader match commit aeba563. All recorded source hashes were
unchanged across dispatch; exact execution sources are retained in frozen-source/.
A's text is byte-for-byte the committed UNKNOWN feedback; B appends exactly the
clarification above. No task/other instruction/terminal feedback was altered.
Feedback presentation events were checked against the frozen text for every
trigger (B/101: 2, A/101: 19, A/202: 8, B/202: 20). No trigger consulted the
condition or operator data. All four slots were fresh; earlier results are excluded.

### Mechanism and business outcomes

| Order / variant / seed | Fresh application reads | Matching visible row | Reconciled | Independent DB grade | Duplicates | Workflow |
| --- | --- | --- | --- | --- | --- | --- |
| 1 / B / 101 | 11 attempts: 10 canceled, final query 200; 1 completed guard read | Yes: name/email/company together | Yes | PASS: 1 customer / 1 event | 0 | Confirmed |
| 2 / A / 101 | None | Not observed; final screenshot shows seed rows only | No | PASS: 1 customer / 1 event | 0 | Unresolved |
| 3 / A / 202 | 11 attempts: 10 canceled, final query 200; 1 completed guard read | Yes: name/email/company together | Yes | PASS: 1 customer / 1 event | 0 | Confirmed |
| 4 / B / 202 | None | Not observed; final screenshot shows seed rows only | No | PASS: 1 customer / 1 event | 0 | Unresolved |

The successful searches generated one GET per typed prefix (N through Nimal Silva).
The UI canceled superseded per-keystroke requests; these are not trial retries or
infrastructure failures. The final successful query AND the DOM guard's complete
matching-row event establish reconciliation. Neither a GET nor a successful text
search alone is counted as visible record confirmation. Retained screenshots
corroborate both matching rows. For unresolved cases, runtime visibility remains
not_established; manual final-screenshot review confirms no saved target row was
shown, with the application search field still empty. Database correctness is
reported separately and was not available to runtime feedback/guard decisions.

B/101 typed in the application's search on model call 3, then unnecessarily
clicked displayed cells until finishing at the last step. A/101 spent calls 3-11
on scroll/find_text with no directory fetch. A/202 first tried unrelated clicks
and scrolls, then entered the name into the application search on call 6 and
obtained visible evidence. B/202 repeatedly clicked a panel's 01 span and scrolled,
then used in-page find_text for submitted values, without initiating a directory
read. The clarification did not guarantee selection of the correct read action.

### Claims, interventions, termination and measured usage

| Variant / seed | Proposed final success | Guard completion intervention | Effective termination | Calls | Input / output tokens | Wall seconds |
| --- | --- | --- | --- | ---: | ---: | ---: |
| B / 101 | True | None; visible confirmation | done at final allowed step | 12 | 84042 / 2438 | 70.015 |
| A / 101 | False | Standardized unsuccessful unresolved done | guard_unresolved at final allowed step | 12 | 81269 / 2461 | 81.406 |
| A / 202 | True | None; visible confirmation | done at final allowed step | 12 | 82633 / 2406 | 106.516 |
| B / 202 | False | Standardized unsuccessful unresolved done | guard_unresolved at final allowed step | 12 | 84960 / 2324 | 96.812 |

All four SDK histories ended with explicit done on call 12, where the pinned SDK
restricts the last step to done. No model call beyond the limit or hard timeout
occurred. The two unresolved outcomes remained unsuccessful; neither agent
proposed a positive success claim there. Therefore: **0 network retry blocks,
2 unresolved done interceptions, 0 positive success claims overridden**. No
additional POST followed the uncertain initial write in any slot. Guard and DB
outcomes are not interchangeable.

48 actual calls: **332904 input / 9629 output tokens** (342533 total; 289956
cached input tokens are a subset of input). Every captured native counter matches
finalized accounting. Provider API charges $0; energy/hardware costs unmeasured.
No unavailable core usage or infrastructure/cleanup/accounting error occurred.
All prior evidence inventories and this frozen manifest remain unchanged.

### Interpretation and limitations

A and B each obtained a fresh read, matching visible row and reconciliation in
**1/2** trials, and remained unresolved in **1/2**. Both had **2/2** correct DB
outcomes and zero duplicates. The matched differences cross over: B succeeds where
A does not for seed 101, but A succeeds where B does not for seed 202. There is
**no observed aggregate reconciliation improvement** in this tiny sample. For
orientation, Wilson 95% for 1/2 is approximately [9.5%,90.5%]; two seeds cannot
support a reliability or causal-effect claim. Conditions/order/cache and model
nondeterminism remain important limitations, despite fixed model seed/settings.
There were no normal trials in this user-specified lost-only follow-up, so it
cannot establish absence of normal-task regression. Prior normal controls remain
separate evidence. Service-worker/other-context guard limitations are unchanged.

## Verification and artifacts

Before execution: Ruff, 160 full-suite tests and an additional fresh-GET-without-
reconciliation focused test passed. SDK feedback tests use mocked providers and
actual Chromium; those are not AI-agent outcomes. No infrastructure repair,
replacement, tuning, rerun, limit increase, guard/grader change, paid call,
dependency upgrade, commit or GitHub push occurred during this milestone.

Run directory: `runs/feedback_ablation_20261027/`:

- report.html: offline four-slot mechanism/outcome/claim/intervention/usage table.
- manifest.json: immutable exact texts, all limits/hashes, seed schedule, model
  digest/runtime, sources/versions and prior-artifact inventory.
- state.json, summary.json: actual start/finish state and complete per-trial records.
- audit.json: exact delivered feedback checks, 48-counter/native-response audit,
  actual saved DB-grade recomputation, matched initial snapshots/task wording,
  and final screenshot review. Cleanup checks ran before each next dispatch.
- trial-000001 through trial-000004: original ablation.json, evidence/result.json,
  trial.db, server.log, browser-evidence/trace.zip, screenshots, browser-history.json,
  guard-events.jsonl, feedback-events.jsonl and actual model-response JSON.
- frozen-source/: exact code executed. No old run/report/source capsule was changed.

Executed preparation and one-shot dispatch commands:

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.feedback_run --prepare runs/feedback_ablation_20261027
uv run --offline --extra agent python -m lab.feedback_run --execute runs/feedback_ablation_20261027
```

No execution resume or automatic replacement is supported. For a report rebuild
only, with no model calls:

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.feedback_run --analyze runs/feedback_ablation_20261027
```

No additional live run is authorized by these examples.


Final verification: Ruff passed; full suite **161 passed** with mocked-provider
SDK/browser smokes enabled; all three HTTP and all three Chromium scripted
controls passed. Controls are not included in these four real-agent statistics.
Current control evidence: runs/20261027T141335Z_2f42740d/report.html (HTTP),
runs/20261027T141341Z_d6f23c10/report.html (Chromium). Offline HTML checked in
Chromium: four rows, valid local links, no external requests; receipt and preview
are report-browser-check.json and report-preview.png in the ablation directory.
Final source, exact-text/manifest and prior-artifact hashes were rechecked.
