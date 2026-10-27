# Reproducible recovery benchmark: v1 and remaining plan

Status: Benchmark Engine v1 implements sequential seeded multi-trial scheduling,
paired scenario/repetition blocks, isolated trials, per-trial JSON, offline
aggregation/reporting and Wilson binary intervals. Existing controls and the
Browser Use adapter are reused. Both basic and verification-guided agent policies
are selectable, but its paid-provider benchmark path remains live-unverified. Separate completed
local comparison/pilot harnesses provide real-agent observations; see CASE_STUDY.md.
No paid call has been executed.
Checkpoint recovery is NOT implemented. This document retains future design
requirements below; it does not declare all acceptance gates completed.

## Comparison arms

| Arm | Planned behavior | Current support |
| --- | --- | --- |
| Blind retry | On uncertain confirmation, submit again without checking state | Scripted negative control only; label separately from AI results |
| Basic Browser Use | Same base business task and browser tools, no recovery-specific guidance or checkpoint layer | Implemented selectable v1.1.0 neutral task; separate local comparison observed normal 3/3, lost 0/3 |
| Verification-based recovery | On uncertain submission, search the CRM and inspect matching records before deciding whether to retry | Scripted positive control and selectable v1.1.0 agent task plus policy guidance; separate local comparison observed normal 3/3, lost 0/3 |
| Checkpoint-based recovery | Track workflow phases and observed browser evidence, then resume by verifying an uncertain submission before retrying | Not implemented |

Keep the scripted blind-retry baseline distinct from model-driven arms in tables
and charts. If an AI blind-retry arm is later added, explicitly specify and version
its forced retry policy and label it independently. Do not compare scripted speed
or zero model cost as if it measured the capability of an AI agent.

The current v1.0.0 prompt instructs verification before retry. Do not relabel it
as a neutral basic-agent baseline. Introduce a new task/policy version containing
the same business objective and customer data but a neutral base instruction.
The engine now supplies neutral v1.1.0 as the shared agent objective; recovery
guidance is appended only for verification-browser-use. The policy identity is
the strategy name plus policy version 1.0.0. Old v1.0.0 tasks/control metadata are
preserved. Future task/policy edits must bump the appropriate version.

## Implemented v1 scope

- CLI: `python -m lab.benchmark`, with scenario/strategy selection, repetitions,
  ordering seed, transport and a fresh output directory; `--analyze` is offline.
- Manifest schema: benchmark-manifest-v1.schema.json. Canonical scenario/strategy
  ordering and seeded arm shuffling create a reproducible paired schedule.
- Durable trial slots, start journal, conservative run-wide agent budget admission,
  no automatic retries, interruption-aware partial reports and local evidence links.
- Separate metric groups by result kind, strategy, scenario, transport, task/policy
  versions and provider/model. Wilson 95% intervals for binary rates; explicit
  denominators and missing evaluations. Timing/call/token/estimated-cost coverage
  is labeled measured, estimated, unknown or unavailable; reservations are separate.
- Each trial reuses existing runner/grader isolation. Scripted driver errors now
  still trigger independent grading after server shutdown. Assertions/faults stay
  operator-owned; model tools/security limits remain unchanged.
- Source commit/dirty-tree content digest, tracked-patch digest, dependency lock
  hashes and installed package versions are recorded. Actual control Chromium
  version is recorded per browser trial. Raw traces and SQLite evidence stay local.

V1 does not implement resumable execution, checkpoints, parallel execution,
held-out customer variants, exact provider invoice reconciliation or paired
bootstrap comparisons. Seeded scheduling does not make provider outputs or OS
timings deterministic. A live run still needs explicit provider/key/model,
per-trial limits, total budget and separate paid authorization. The Python CLI
requires --allow-paid for agent strategies; the development work did not use it.

## Reproducible trial manifest and execution

1. Add a checked-in manifest schema containing benchmark/task/policy versions,
   normal and lost-confirmation scenarios, fixed synthetic customer variants,
   repetitions, ordering seed, model/provider, framework/browser versions,
   dependency-lock hashes, source commit and dirty-tree patch hash when relevant.
2. Run a small no-cost mocked scheduler/aggregation pilot, then a separately
   authorized live pilot. Select and freeze sample size before collecting the
   comparison dataset. Do not stop early because results look favorable.
3. Use paired blocks: each task/scenario/repetition runs every arm against the
   same initial synthetic state. Randomize arm order with a recorded seed.
   Include normal tasks alongside failure scenarios and report them separately.
   Provider/model nondeterminism remains even with fixed ordering seeds.
4. Every attempt gets a new database, server process and browser context/profile.
   Keep assertions, failure scheduling, resets and grading operator-only. Agent
   recovery may use browser observations, never database snapshots or graders.
5. Give model-driven arms identical provider/model, browser tool policy, and
   step/time/call/token/USD ceilings. Record recovery-policy overhead. Require a
   run-wide authorized maximum trial count and aggregate estimated spend in
   addition to per-trial limits. Reserve the next trial's allowance before launch;
   do not schedule it if the remaining budget is insufficient. Use provider caps.
6. Stop the driver and server before independent grading. Always attempt grading
   after an execution error when the initial snapshot is available. Record task
   failure and infrastructure/adapter/evaluator errors as separate dimensions.
   Do not silently drop failures or retry infrastructure errors; any replacements
   must be predeclared and linked to the original attempt.

## Checkpoint protocol to implement

Use a narrow structured state machine: not started, form filled, submission
attempted/uncertain, record verified, complete. Record only observed UI evidence,
the synthetic task identity and policy version. A checkpoint is not proof of a
database commit. On restart after submission, search and verify the existing
customer before repeating a write. Test interruption before click, after click,
after commit/before confirmation, and after verification. Test stale or malformed
checkpoints and conflicting observations. Give the model no filesystem or code
tools: a trusted adapter/controller manages this limited state. Review whether
checkpoint storage itself could leak assertions or fault settings.

## Planned metrics and definitions

| Metric | Planned calculation |
| --- | --- |
| Operational success rate | Trials with no execution error and passing independent grader / all started trials; report n and 95% binomial interval |
| Business success rate | Passing independent evaluations / trials with valid evaluations; show missing evaluations and infrastructure counts alongside it |
| Duplicate-action rate | Evaluations containing duplicate_customer / all valid evaluations; also show duplicate counts per started trial and ambiguous/unknown cases |
| Execution time | Per-trial wall time plus driver-only time; median and p95 by arm/scenario; retain timeout observations as censored and show their limits |
| Model calls | Attempted calls, successful calls and failed/unknown-usage calls per trial and arm; include policy-related calls |
| Token usage | Reported input, output and cache tokens; preserve unavailable usage as unknown, never zero; show reservations separately |
| Estimated cost | Reported usage times a versioned, dated pricing table, including cache premiums/multipliers; also show conservative reserved cost and any unknown-cost trials |

Define a duplicate action from committed business/audit effects, not just repeated
clicks. Report raw retry-click/submission counts separately if useful. An agent's
success claim never enters success-rate grading. Keep provider billing reconciliation
separate from estimates; estimates are not invoices or hard billing caps.

Report per-arm/scenario denominators, repetitions, infrastructure error categories,
normal versus failure results, paired differences and uncertainty intervals.
Use a paired bootstrap over task/scenario blocks for comparison intervals when
the dataset supports it; document small-sample limitations. Retain raw per-trial
JSON and artifact references so summaries can be recomputed without model calls.
No pooled headline should hide normal-task regressions or excluded trials.

## Acceptance gates

- Existing HTTP and browser controls keep their expected outcomes.
- Mocked multi-trial tests prove trial isolation, policy selection, seeded ordering,
  aggregate-budget admission, cleanup, unknown usage handling and metric denominators.
- Injected fixtures exercise no-op success claims, duplicates, incorrect data,
  interruptions and infrastructure errors without weakening the existing grader.
- Checkpoint resume tests demonstrate no repeated write after an uncertain commit.
- A separate analysis command recomputes summaries from saved trial JSON only.
- Live pilots require an explicitly configured model/key and authorized total
  budget. Publish results only after the manifest, all arms and evaluation gates
  are implemented and verified. No paid run is authorized by this plan.


## Completed exploratory local recovery comparison - 27 October 2026

Exactly 12 local-agent trials completed: 2 frozen configurations x 2 conditions x
3 matched starting-data seeds. Normal: baseline 3/3 and verification 3/3 business
passes, no duplicates. Lost confirmation: both 0/3 passes and 3/3 duplicates.
All agents explicitly finished; 10/12 did so at the 12-call ceiling (SDK's final
step is done-only); no blocked-limit, timeout, infrastructure or accounting error.
Wilson 95% intervals are [43.9%,100%] for 3/3 and [0%,56.1%] for 0/3.
This small comparison does not demonstrate reliability or a recovery improvement.

Recorded full instruction/configuration hashes, seeded balanced ordering, shared
Ollama cache conditions, native usage, independent grades and all trial evidence.
135 calls: 895134 input / 23427 output tokens; provider API charges $0, local
hardware/electricity unmeasured. All native counts and DB grades audited; original
trials remain byte-for-byte unchanged. Added operator-side per-task initial-data
seeding and a fixed local comparison harness, with no grader/dependency changes.
Ruff, 117 tests (mocked SDK smokes enabled) and all six scripted controls pass.

Full protocol, diagnosis, counts/uncertainty, implementation changes and limitations:
[LOCAL_RECOVERY_COMPARISON.md](LOCAL_RECOVERY_COMPARISON.md).
Offline report: runs/local_recovery_comparison_20261027/report.html; immutable
manifest, summary and audit alongside it. No replacement/rerun, paid calls or push.
Checkpoint recovery and broad reliability claims remain out of scope.

Post-run report-only fix: malformed evaluator records now retain a partial report
and stop without replacement; explicit report-kind labels distinguish mocked
fixtures. Frozen execution source/hash is preserved alongside
postrun-report-fix.json. No real trial or grader was modified and no extra
inference occurred. See LOCAL_RECOVERY_COMPARISON.md for the separate fix record.


## Experimental uncertain-write guard - 27 October 2026

Separate GuardConfig/OllamaGuardAdapter now gates browser-context POST requests
before dispatch and requires a fresh read plus one matching visible name/email/
company row before resolving success. No DB/fault/grader input enters guard
recovery decisions. Baseline/verification configurations and all old evidence
are unchanged; no application idempotency/uniqueness constraint was introduced.
Supported scope is this synthetic CRM's same-context HTTP flow, not arbitrary
sites/service workers. Enforcement was verified with actual Chromium/CDP click
and Enter repeats, rejection/correction, uncertain writes, visible reconciliation,
unresolved stops and independent grading, plus mocked pinned-SDK model responses.

Exactly four authorized real local trials completed once (normal/lost confirmation
x seeds 101/202): all four independent DB grades pass with one customer/event,
zero duplicates. Only the two normal cases reached visible confirmation; both
lost cases stopped explicitly unresolved, so autonomous recovery is NOT proven.
No live retry requests were attempted or network-blocked. Guard intercepted two
unresolved done actions; one was already unsuccessful and one positive claim was
overridden. These are distinct intervention counts, not two blocked retries.
45 calls; 302591 input / 7979 output tokens. No infrastructure/accounting/cleanup
errors. Ruff, 137 tests and all six existing scripted controls pass. No paid call,
upgrade, grader change or push. Provider API charges $0; energy/hardware unmeasured.

Rule specified before implementation, actual feasibility limits and detailed
results: [RECOVERY_GUARD.md](RECOVERY_GUARD.md). Offline report:
runs/recovery_guard_20261027/report.html, with manifest, audit, frozen execution
sources and per-trial guard event logs. Post-run changes were report-only
intervention-count enrichment; original results remain unchanged.
