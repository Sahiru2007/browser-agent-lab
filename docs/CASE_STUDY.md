# Browser Agent Lab: correct effects, uncertain completion

Portfolio release candidate, 27 October 2026. This case study consolidates retained
synthetic-local evidence; it does not introduce new trials or change any grade.
The engineering question is whether a browser workflow produces the requested
committed effects when its feedback is incomplete. The tested model is local
Qwen3 8B, not a claim about browser agents or models generally.

## What is independently measured

A FastAPI/React CRM, isolated SQLite state, controlled post-commit confirmation
loss, browser-only drivers and a separate database/audit checker make errors
observable. The operator owns tasks, resets and assertions. Agents receive only
the URL, ordinary instruction and permitted browser tools. No database access,
shell, JavaScript execution, extraction model, search engine or grading tools.
Each trial has a fresh DB, server, browser/profile/context; the model server/cache
is shared. Agent reports, business grades, visible recovery and efficiency are
separate measurements. Scripted controls and mocked tests are not AI observations.

## Results by experiment

| Retained cohort | Attempts | Correct business | Other observations |
| --- | ---: | --- | --- |
| Original creation integration | 2 | normal 1/1; lost 0/1 | Lost case duplicated despite success claim |
| Matched creation comparison, normal | 6 | baseline 3/3; verification 3/3 | Both policies completed normal tasks |
| Matched creation comparison, lost | 6 | baseline 0/3; verification 0/3 | Each policy duplicated in 3/3 |
| Experimental guard, normal/lost | 4 | 4/4 | 2 normal confirmed; 2 lost unresolved |
| Guard feedback A, lost | 2 | 2/2 | 1 confirmed, 1 unresolved |
| Guard feedback B, lost | 2 | 2/2 | 1 confirmed, 1 unresolved; no aggregate improvement |
| Unguarded edits, no fault | 6 | company 3/3; email 3/3 | 3 positive success flags; 37 no-op saves |

These are distinct, non-overlapping attempts, not interchangeable benchmark arms.
Sample sizes are tiny, local-only and task-specific. For 3/3, Wilson 95% spans
43.9%-100%; for 0/3, 0%-56.1%. The pooled edit 6/6 interval is 61%-100%, with
matched tasks/seeds further limiting independence. None establishes reliability.

## Lost confirmation and instruction-only recovery

The original lost-confirmation trial aborted its first POST around 697 ms. The
server had already committed a correct customer and creation event, then delayed
the response. The model subsequently clicked Save again without a fresh read,
creating a second customer/event. It claimed success; independent grading returned
`duplicate_customer`. Browser action success was not business confirmation.

In the frozen 12-trial comparison, general verification instructions were the
only policy difference. Both configurations passed all three normal cases and
duplicated all three lost cases. Stating an intention to verify did not reliably
produce the necessary fresh read before another write. The observed zero paired
business difference is not proof that instruction changes never help.
[Comparison protocol and traces](LOCAL_RECOVERY_COMPARISON.md).

## Guarded effects are not necessarily recovered workflows

The separate experimental guard marks uncertain writes UNKNOWN, blocks equivalent
retries within its supported browser-context route, permits read-only reconciliation
and intercepts unresolved completion. It requires fresh application data and a
visible row matching submitted name, email and company together; in-page text
search or a GET alone is insufficient. It never uses hidden DB/fault information.

The four guard trials all have correct committed state and no duplicates. Only
the two normal cases reconciled visibly; both lost cases ended unresolved. The
unresolved agents made no post-submission directory reads and spent 8/9 calls
looping on scroll/find_text. No correct fresh evidence was rejected. There were
**zero live retry-blocking interventions** because no retry request was attempted.
Two unresolved done actions were intercepted; one positive claim was overridden.
Actual retry blocking is demonstrated by separate Chromium/CDP technical tests,
not by those four agent outcomes. [Rule and coverage](RECOVERY_GUARD.md),
[evidence diagnosis](GUARD_DIAGNOSIS.md).

## Feedback ablation

Four fresh lost-confirmation attempts compared original UNKNOWN feedback with an
added explanation of in-page search versus application search/refresh. Each arm
reconciled one of two trials, on opposite seeds; all four DB grades pass. Only
fresh reads followed by full matching visible records counted as reconciliation.
The clarification produced **no observed aggregate improvement**; this is neither
a reliability claim nor a causal finding of equivalence. No feedback was tuned
between attempts. [Frozen texts and per-trial evidence](FEEDBACK_ABLATION.md).

## Editing: six correct effects, mixed completion language

Each task selects an existing customer by email among similar names and changes
only company or email. Stable identity, all unrelated fields/records, no creation
or deletion, and an exact before/after audit event are independently required.
All six saved DBs pass, including independent reopening/regrading. Each substantive
PATCH targeted the intended customer. One trial later opened the distractor during
verification without changing it. A normalized no-op save returns changed=false
and adds no audit event; it is not a nontrivial edit and cannot satisfy one.

All six emitted explicit done at 12 calls. This is final-step completion, not early
completion; no thirteenth dispatch or hard timeout was observed. The three false
**Boolean success flags** must not all be called false-negative factual claims:

| Trial | Actual final response meaning | Interpretation |
| --- | --- | --- |
| Company/101 | Acknowledges update; says verification failed because an element index was unavailable; calls task partial | Missing verification confirmation, with qualified completion; not an explicit denial of the write |
| Company/202 | Acknowledges update; says verification failed; calls task partial | Verification uncertainty despite acknowledged edit; not an explicit failed-write claim |
| Email/202 | Says update failed and changes were not saved | Explicit factual failure claim contradicted by committed state: a false negative about the write |

All three have final messages; none is missing a response. State messages for call
3 contained `Changes saved.` in all six trials. Email/202 subsequently received
`No changes to save.` yet concluded that saving failed. These are observable UI
inputs, not evidence of what the model understood. The company agents' uncertainty
about their later verification does not make their statement that the edit
occurred false. Raw messages/flags/grades remain unchanged.
[Full pilot protocol and responses](EDITING_PILOT.md).

## Descriptive editing efficiency

| Trial | Calls | No-op saves | Whole-trial seconds | Write-producing call | Later calls after successful response |
| --- | ---: | ---: | ---: | ---: | ---: |
| Email/101 | 12 | 6 | 74.438 | 2 | 10 |
| Company/101 | 12 | 0 | 78.687 | 2 | 10 |
| Company/202 | 12 | 0 | 58.328 | 2 | 10 |
| Email/202 | 12 | 17 | 77.547 | 2 | 10 |
| Email/303 | 12 | 6 | 76.094 | 2 | 10 |
| Company/303 | 12 | 8 | 79.469 | 2 | 10 |
| Total | 72 | 37 | 444.563 | - | 60 |

Method: PATCH payload/response bodies in retained Playwright network traces
identify the one changed=true edit and the changed=false saves. UTC request start
plus recorded request duration bounds response completion. Browser history step
numbers 1-12 match native response action arguments, allowing SDK-added defaults;
step 0 is automatic navigation, not a model call. Ten subsequent numbered model
steps start after the successful response in each trial. Since the application
commits before replying and the independent audit confirms the desired update,
these **60 calls are a conservative, operator-hindsight post-commit count**.
They are not 60 proven unnecessary calls: verification and an explicit finish
can be useful. No-op HTTP saves and model calls are different units; one call
can trigger multiple actions.

Exact DB commit timestamps, exact model-dispatch wall timestamps, an optimal-call
baseline, isolated inference times, energy use and hardware cost are unavailable.
Step-start times give a conservative bound on later model calls, not a precise
commit-to-dispatch measurement. `Changes saved.` was in the next model-visible
state, but full DB assertions were never available to the agent. The operator's
knowledge of preserved records/audit must not be attributed to it.

Usage is measured natively: 496350 input / 13602 output tokens; 424545 cached
input tokens are a subset of input. Provider API charges $0; energy/hardware
unmeasured. Model/prefix cache and hardware are shared, with no timing isolation.
A separate regression process briefly overlapped the first trial before being
stopped; no pilot attempt was restarted. These timings support description, not
causal speed comparisons. Business passes are unchanged by efficiency findings.

Reproduce this analysis without inference (read-only; writes JSON only to stdout):

```powershell
uv run --offline --extra agent python scripts/summarize-editing-evidence.py runs/editing_pilot_20261027
```

Derived local receipt: `runs/portfolio_rc_20261027/editing-efficiency.json`.
Its source hashes identify raw result/history/trace inputs; frozen manifests and
all historical grades remain untouched.

## Limits and reviewer access

Qwen3 `qwen3:8b-q4_K_M`, model digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`,
Browser Use 0.13.11, context 16384, output cap 2048/call, concurrency one,
12-call ceiling and 300 s timeout apply to these local experiments. Fixed seeds
are not a guarantee of deterministic model behavior. The SDK restricts its final
allowed step to done, which affects observed completion. No cloud fallback or
paid inference was used; no new inference was authorized for this release work.

The guard is CRM/create-specific, not editing recovery or general idempotency.
Supported same-context JSON create traffic is tested; routed unsupported writes
are blocked. Service-worker traffic and other contexts are unsupported, and a
negative test demonstrates bypass/duplicate grading outside the route's scope.
No universal browser/network/OS isolation is claimed. No auth, edit fault injection,
checkpoint recovery or edit-conflict control is implemented.

Raw runs/DBs are deliberately Git-ignored. Local reports below exist on the author
machine, not in a fresh clone; Markdown protocol/method/results are reviewable in
Git. For independent evidence review, arrange local access or an explicitly
reviewed/redacted evidence export separately. No raw bundle is published here.

| Study | Local offline report (project-relative) |
| --- | --- |
| Original creation | `runs/agent_20261027T104036Z_f677e01c/result.json` and `runs/agent_20261027T104235Z_60a31f72/result.json` |
| Recovery comparison | `runs/local_recovery_comparison_20261027/report.html` |
| Guard | `runs/recovery_guard_20261027/report.html` |
| Feedback | `runs/feedback_ablation_20261027/report.html` |
| Editing | `runs/editing_pilot_20261027/report.html` and `independent-audit.json` |

See [demonstration walkthrough](DEMO.md), [architecture](ARCHITECTURE.md),
[tasks](TASKS.md) and [verification chronology](VERIFICATION.md).
