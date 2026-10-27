# Exploratory local editing pilot

## Frozen pre-execution protocol

Authorized: exactly six new local-only unguarded trials, one per company/email
edit task and seed 101/202/303. No injected failure, no retries/replacements, no
instruction tuning. The task wording is the v1.0.0 template with seed-specific
ordinary email/company values. Both tasks share initial data within each seed;
Asha Perera and Asha Pereira remain distinguishable by email. Seeded task order
within each seed is frozen before dispatch. No reliability or timing-isolation
claim is warranted.

Use OllamaConfig unchanged: qwen3:8b-q4_K_M, digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41,
16384 context, one concurrent request, 2048 output tokens/call, 12 calls/steps,
300 seconds/trial. Native structured model responses, temperature 0, seed 42,
think=false and shared keep_alive/cache match prior baseline. No additional
operating instructions or creation-specific recovery guard. Browser Use 0.13.11
and the existing positive browser action list are unchanged. Only URL and ordinary
task enter AgentRequest; operator-only seeds/assertions/database stay outside.
Model nondeterminism and shared server/prefix caches remain; no cache flushing.

The fixed runner freezes configuration/task/source hashes and copies execution
sources before starting. It checks actual local server cloud/storage/concurrency
settings and digest without inference, then rechecks runtime digest/settings,
trace evidence and cleanup after every attempt. Infrastructure/accounting errors
stop dispatch; failures are retained, never replaced. Each fresh DB is independently
reopened/regraded after server shutdown. Agent claims remain separate from grade.
Correct customer selection is operationalized as committed audit write targets;
actual selection clicks/visible UI are retained in trace/history for inspection.

Checkpoint: 2826117, verified editing implementation only. Earlier uncommitted
feedback-ablation changes were preserved separately. Minimal follow-on changes:
agent_run --task company|email selects existing task objects; editing only supports
normal scenario. Benchmark selectors are unchanged. lab.edit_pilot provides this
fixed six-slot execution and model-free report rebuilding, not an edit benchmark.

Execution (the user has authorized this run; do not repeat without authorization):

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.edit_pilot --execute runs/editing_pilot_20261027
```

Offline rebuilding: `uv run --offline --extra agent python -m lab.edit_pilot --analyze runs/editing_pilot_20261027`.

No paid API calls; provider API charges $0, electricity/hardware unmeasured.
Results will be appended after inspecting all retained attempts.


## Completed six-trial pilot - 27 October 2026

The fixed schedule completed once: email/101, company/101, company/202, email/202,
email/303, company/303. No attempt was replaced or retried by the operator.
Configuration SHA256: 37295971ad84fd426b4198ccd832b003b66bcc7f48a5cfa08351d616939115da.
Each task's exact text, seed state and hash are in the immutable manifest. Source
hashes, installed SDK prompt sources and model digest were frozen and rechecked.
No instruction, tools, limits or grader change occurred during execution.

| Task | Seed | DB grade | Agent claim | Calls | Input/output tokens | Duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| email | 101 | PASS | True | 12 | 81,403 / 2,075 | 74.438 |
| company | 101 | PASS | False | 12 | 82,583 / 2,264 | 78.687 |
| company | 202 | PASS | False | 12 | 83,475 / 2,108 | 58.328 |
| email | 202 | PASS | False | 12 | 82,378 / 2,358 | 77.547 |
| email | 303 | PASS | True | 12 | 83,179 / 2,292 | 76.094 |
| company | 303 | PASS | True | 12 | 83,332 / 2,505 | 79.469 |

All six first record-detail reads selected the intended customer, and every
substantive PATCH targeted that customer with only the requested field. Both task
types passed 3/3 independently graded DB outcomes (pooled 6/6). All original IDs,
unrequested fields and other records were preserved. No customers were created or
deleted; each DB contains exactly one truthful customer.updated event. All six
saved databases were reopened and independently regraded again after completion;
all match the runner snapshots/grades. These are observations on three matched
seeds, not proof of reliability. Pooled Wilson 95% interval is approximately
61%-100%; task/seed dependence further limits generalization.

Agent workflow results differ from business grades: 3 true and 3 false success
claims. Every trial explicitly finished at the 12-call ceiling; none completed
early, hit the hard timeout or had a blocked thirteenth dispatch. Company/101 and
company/202 reported incomplete verification after stale/invalid element-index
actions. Email/202 falsely reported the changes were not saved, despite the
correct commit. SDK action/model failures were recorded in company/101,
company/202 and email/303; these are model task failures, not laboratory errors.
The traces show 37 extra empty PATCH no-op saves (6,0,0,17,6,8 by schedule), all
200 and event-free. Company/101 additionally opened the other similar-name record
during verification, without modifying it. A passing DB grade does not establish
clean selection throughout, useful verification, truthful claims or efficiency.

Measured native usage: 72 model calls, 496350 input tokens, 13602 output tokens,
424545 cached input tokens; summed whole-trial duration 444.563 s. All 72 native
responses are retained and within the per-call output limit. No usage estimates
or fabricated counts. Provider API charges $0; electricity/hardware unmeasured.
No infrastructure, authentication, accounting, trace-save or cleanup errors;
per-trial receipts verify no remaining CRM listener/worker/local trial browser.
All 1232 pre-pilot historical files remain SHA256-identical. Original records and
frozen recovery configurations were not rewritten. No paid calls, upgrades,
recovery feature or push.

Timing caveat: Ollama/model/prefix cache and hardware were shared. A separate
regression suite briefly overlapped the first trial, then was deliberately stopped
to avoid browser-cleanup interference. It was not a pilot retry. No timing
isolation or deterministic model behavior is claimed.

## Evidence

Project-relative output: runs/editing_pilot_20261027/.
- report.html: offline detailed outcomes/claims/usage and evidence links.
- manifest.json: configuration, exact tasks, ordering, source/SDK hashes, historical
  file inventory, actual server settings and model digest; frozen-source/ copies.
- state.json: finished, six started slots, no stop reason.
- summary.json and independent-audit.json: all outcomes, repeated DB regrades,
  actual detail-read/write targets, PATCH bodies and aggregate accounting.
- preservation.json: 1232 files checked, no changes.
- Each schedule-named trial directory: result.json, pilot-result.json, trial.db,
  browser-evidence/trace.zip, browser-history.json, step screenshots and all 12
  model-response-NN.json native responses. Final responses and termination are in
  the JSON reports; agent claims never override grading.

Pilot orchestration and minimal CLI dispatch are follow-on local changes after
the editing checkpoint. They do not add editing recovery or change the benchmark
engine. Additional real trials require fresh authorization; --analyze is offline.


Post-pilot verification passed: Ruff, full suite **197 passed** with mocked-provider
SDK/real-Chromium smokes enabled, TypeScript/Vite build, all three HTTP and all
three original browser controls, and both editing browser controls with saved-DB
regrading. Blind retry still fails intentionally with duplicate_customer.
New tests cover matched task seeds, both edit CLI selectors, fault rejection before
dispatch, independent regrading regardless of success claims, stale-grade rejection
and an offline unstarted-slot report. They do not count as real agent observations.
Control reports: runs/20261027T154442Z_57a819b8/report.html (HTTP),
runs/20261027T154448Z_57c97268/report.html (browser),
runs/edit_pilot_post_controls_20261027/report.html (edits).
Pilot HTML verified in Chromium: six trial rows, 21 valid local evidence links,
zero external requests; report-browser-check.json and report-preview.png retained.
Editing checkpoint is committed; subsequent minimal dispatch/pilot/report changes
remain uncommitted. Earlier unrelated feedback work remains intact. No push.


## Portfolio response-language and efficiency clarification

See [CASE_STUDY.md](CASE_STUDY.md) for evidence-only analysis added after this pilot.
The three false Boolean success flags are not three false-negative factual claims:
company/101 and company/202 acknowledge the edit but lack verification confirmation;
email/202 explicitly denies a saved edit. All have final messages. Retained state
messages show Changes saved. at call 3 in every trial. Ten subsequent model steps
per trial start after the successful edit response (60 total, conservative operator
post-commit hindsight), not proof that every later call was unnecessary. Exact
DB commit timestamps and isolated dispatch/inference timings are unavailable.
The 37 no-op saves and six passing business grades remain unchanged. The pilot and
feedback work was subsequently committed in 660f089; earlier "uncommitted" statements
above describe the historical checkpoint, not current repository state.
