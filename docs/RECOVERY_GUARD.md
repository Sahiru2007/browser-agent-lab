# Experimental uncertain-write guard v1

## Rule specified before implementation

Scope: the supplied synthetic single-customer creation UI, not arbitrary websites.
Guard decisions consume only dispatched browser request method/URL/body, browser
response/failure events, submitted browser actions and rendered visible UI. No
DB, fault flag, server log, expected outcome or grading information is available.

1. Before forwarding the first write, atomically mark its outcome unknown and
   record its submitted fields. Equivalent retries are blocked. Conservatively
   block ALL further mutating requests while unknown (including changed payloads).
2. Continue to allow reads/navigation/search/scroll and visible-state inspection.
   Never issue a reconciliation request or click on behalf of the agent.
3. A search action or HTTP 201 alone is insufficient. A read initiated AFTER the
   write must finish, and a visible directory row must show the submitted full
   name, email and company together, exactly one matching row. Those rendered
   details establish observed state satisfaction, not hidden DB uniqueness or
   attribution to a particular server transaction. The independent grader remains
   necessary. Multiple matching visible rows do not reconcile success.
4. A received 422 response with explicit validation details is a known rejected
   write in this CRM's public API contract, and allows corrected/repeated action.
   Timeouts, canceled requests, 5xx and generic errors remain unknown.
5. After observed success, block equivalent/additional writes for this single-write
   experiment; allow the agent to explicitly finish. Do not silently complete it.
6. If done is requested while unknown, return an explicit unsuccessful unresolved
   final outcome. Also retain unknown state as unresolved at limits/cleanup.
   Preventing a duplicate is never an automatic business/task pass.

## Enforcement feasibility and planned boundary

Pinned Browser Use 0.13.11 exposes Tools.act and Agent.run hooks. Step hooks alone
are insufficient to gate individual writes. Install BrowserContext.route before
agent actions on the already isolated CDP-connected context; this intercepts
click, Enter and multi-action submissions before dispatch. Use normal continue_
(no route.fetch/replay) so the UI's own cancellation behavior remains intact.
A Tools.act wrapper exposes decisions in ActionResult and intercepts unresolved
done. It does not add JS/files/shell actions to the agent.

Scope limitations: route interception does not cover service-worker-handled
traffic. Require none in this supplied app/context, stop on a detected worker;
this is not a reliable arbitrary-site/service-worker firewall. No WebSocket,
beacon GET-side-effect, external tab/context or OS sandbox guarantee is claimed.
The app uses same-context JSON fetch POST and read-only GET; verify these actual
paths before any live guarded trial. Browser-only DOM selectors belong to this
CRM-specific observer, not to a task-specific recovery prompt. No automatic UI
reconciliation, application uniqueness constraint or idempotency is introduced.

Implementation, tests and live observations will be recorded below separately.
Sources: https://playwright.dev/python/docs/network and installed pinned
browser_use/tools/service.py and browser_use/agent/service.py.


## Pre-live enforcement verification

Before any real guarded model call: Ruff passed; full regression suite passed
134 tests before three final pure guard/report tests were added. All 22 focused
guard/pinned-SDK tests then passed, including actual Chromium/CDP click and Enter
routing, successful and uncertain committed writes, actual 422 rejection followed
by correction, concurrent repeats, strict complete/unique/fresh visible record
evidence, unsupported service-worker refusal, explicit unresolved done and a wrong
write failing the independent grader despite no duplicate. SDK provider responses
in smoke tests were mocked; none are real AI benchmark outcomes.
All three HTTP and all three Chromium controls retained their expected outcomes.

The guard wraps only the new GuardConfig path. Original OllamaConfig fields,
baseline and verification instruction texts, original manifests/results and paid
unknown-usage/reservation controls remain unchanged. No application-side constraint
or idempotency is added. Request routing is installed before the SDK's automatic
initial navigation. Enabling routing disables browser HTTP cache; timings are not
isolated from this overhead or the shared Ollama prefix cache. No extra model
calls or increased step/call/time/output limits are granted to reconciliation.

Authorized live check is exactly four guard-only slots in this predeclared order:
normal seed 101, lost confirmation seed 101, normal seed 202, lost confirmation
seed 202. Each uses the original neutral task wording, fresh DB/server/browser,
model qwen3:8b-q4_K_M with the existing digest, 16384 context, one request,
12 calls/steps, 300 seconds and 2048 output tokens per call. No reruns or
replacement slots. Stop further dispatch on infrastructure or accounting problems.
The guard runner retains every result and independently grades DB state; a correct
committed state can coexist with an explicit unresolved guard outcome.


## Implementation and completed exploratory check

Added separate GuardConfig/OllamaGuardAdapter (`ollama-guard`) and a browser-only
RecoveryGuard. Original OllamaConfig fields and baseline/verification task texts
are unchanged. Trusted guard code uses context-level request routing and public
Tools.act extension; no new agent action is registered. It observes actual POST
payloads and rendered row details, not operator expected-customer assertions.
The positive browser-action list and paid-provider safeguards remain intact.
No app/schema/uniqueness/idempotency change was made.

Frozen guarded configuration hash:
`83abe3dd1d64915e229479beabfd7a8f516f3e0bbb2805f66554d062be35bef9`.
Model digest remains
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
Full task/settings/version/source/rule hashes, server runtime and ordered matched
seed schedule are in the immutable manifest. All limits are inherited unchanged.

Exactly four real local attempts ran once, without replacement:

| Condition | Data seed | Independent DB grade | Guard outcome | Duplicate | Calls | Input/output tokens | Wall seconds |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| Normal | 101 | PASS: one customer/event | confirmed_visible; done at call ceiling | 0 | 12 | 81970 / 2108 | 62.000 |
| Lost confirmation | 101 | PASS: one customer/event | UNRESOLVED at final allowed step | 0 | 12 | 80664 / 2185 | 69.078 |
| Normal | 202 | PASS: one customer/event | confirmed_visible; done before ceiling | 0 | 9 | 59032 / 1607 | 43.531 |
| Lost confirmation | 202 | PASS: one customer/event | UNRESOLVED at final allowed step | 0 | 12 | 80925 / 2079 | 69.422 |

Correct committed business effects: **4/4**; visible resolved guarded completion:
**2/4**; unresolved **2/4**; duplicates **0/4**. A DB pass is not proof that the
agent reconciled or successfully completed the guarded workflow. Both normal
cases received a fresh UI list response and showed the submitted full name,
email and company together in one row. Both lost-confirmation cases had an
aborted POST (695.364 / 707.721 ms), a committed creation/fault marker and no
subsequent POST. The guard never consumed those DB/fault observations; they
were checked by the operator after execution only.

Live interventions, derived from immutable guard event logs:

- **0 retry requests blocked at the network gate**: neither real lost-confirmation
  agent attempted a repeated write. Do not claim the network gate blocked a live
  duplicate, or attribute the observed no-retry behavior solely to enforcement.
  Its ability to block actual repeat dispatch is verified by the browser/CDP tests.
- **2 unresolved done interceptions**. Seed 101 already proposed success=false;
  the guard standardized its unresolved result. Seed 202 proposed success=true;
  **1 positive success claim was overridden**. Both returned explicit unsuccessful
  UNRESOLVED final messages. Original proposed messages remain in model responses
  and event logs; they were not deleted or rewritten.
- **2 visible-record reconciliations**, both under normal conditions.
- In both lost cases, the model repeatedly scrolled and used find_text on the
  stale page, rather than initiating a fresh directory read. Finding text (which
  may appear in an input field) is not evidence of a saved directory record.
  The guard remained unknown and did not silently perform a search/refresh.

All four SDK histories finish with done; the effective lost-case termination
is guard_unresolved, not success. Three trials ended on the final allowed
12th call, where the pinned SDK restricts the action set to done. No extra call
was dispatched/blocked by the model budget and no hard timeout occurred.
The driver CLI's exit 0 means the four-slot schedule finished, not that all
agent workflows succeeded. Read the separate DB and guard outcome fields.

Measured usage: **45 calls, 302591 input / 7979 output tokens** (310570 total;
262268 cached input tokens are a subset of input). Native response counters
match every finalized usage entry. Provider API charges **$0**; electricity and
hardware costs remain unmeasured. No infrastructure/accounting/cleanup errors.
No extra real inference ran after the four slots. Shared Ollama cache, route
cache-disabling and observer overhead prevent timing-isolation claims. Two seeds
per condition and one task/model are exploratory, not proof of recovery reliability.
In particular, lost-confirmation autonomous reconciliation was not demonstrated.

## Verification and retained evidence

Ruff and the full optional-SDK regression suite passed: **137 tests**, with
LAB_TEST_BROWSER_USE=1. All three HTTP and all three Chromium scripted controls
passed, preserving the intentional blind-retry duplicate_customer business failure.
Real model outcomes above are separate from scripted controls and mocked SDK tests.
Offline report was opened in Chromium: four trial rows, all local links valid,
no HTTP/HTTPS requests. No frontend or dependency change was required.

Full run directory: `runs/recovery_guard_20261027/`:

- report.html, summary.json: offline outcome/intervention/termination/usage table.
- manifest.json: full frozen rule/configuration/hash, matched states, order and source provenance.
- audit.json: actual saved DB/trace/native-counter verification and no remaining
  trial workers/browsers/CRM listeners. All prior two-trial and 12-trial artifacts
  remain byte-for-byte unchanged.
- trial-0001 through trial-0004: original guard-result.json and evidence/result.json,
  trial.db, server.log, browser-evidence/guard-events.jsonl, trace.zip, screenshots,
  browser-history.json and actual model-response JSON.
- frozen-source/: exact source/rule bytes used by the live run, matching its manifest.
- postrun-analysis-note.json: separate report-only enrichment deriving intervention
  counts from existing event logs. No guard decision or trial record was changed.
- report-browser-check.json and report-preview.png: model-free report checks.

Scripted-control evidence: runs/20261027T114739Z_62e18ab2/report.html (HTTP),
runs/20261027T114746Z_70644da7/report.html (Chromium).

Rebuild only, without inference:

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.guard_run --analyze runs/recovery_guard_20261027
```

The executed command was `uv run --offline --extra agent python -m lab.guard_run
--output runs/recovery_guard_20261027`; it refuses an existing output directory.
Do not execute new slots without user authorization. This guard is not generic
idempotency/checkpoint recovery, a browser/network firewall, or a replacement for
the independent evaluator. Service-worker, other-context and non-HTTP write paths
remain unsupported. No paid calls, dependency upgrades, grader changes or push.


## Evidence-only unresolved-trial diagnosis - 27 October 2026

See [GUARD_DIAGNOSIS.md](GUARD_DIAGNOSIS.md) for timestamped seed-101/202 timelines,
12-call allocation, actual network results, visible-detail findings and explicit
boundary coverage. Both unresolved agents performed zero post-submission reads;
eight/nine calls looped on scroll/find_text. No correct fresh row was rejected.
No reconciliation defect explains the failures; limits and matching stay intact.
Only a reporting defect was corrected for future runs: unresolved text now says
writes remain prohibited instead of implying that requests were actually blocked.
Original results/words/event logs/frozen configurations are unchanged.

The case study still has four passing DB outcomes, two confirmed/two unresolved
workflows, zero live retry blocks and one positive completion claim overridden.
A new scripted negative test demonstrates other-context bypass and an intentionally
failing duplicate grade; it is not a real-agent trial. Routed unsupported paths
are tested as blocked; service-worker traffic and other contexts are not universally
protected. No new model calls, new guard features, relaxed rule or grader changes.
A feedback-only four-slot follow-up is proposed, not executed or authorized here.
