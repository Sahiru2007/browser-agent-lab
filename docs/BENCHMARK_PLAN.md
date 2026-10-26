# Reproducible recovery benchmark: v1 and remaining plan

Status: Benchmark Engine v1 implements sequential seeded multi-trial scheduling,
paired scenario/repetition blocks, isolated trials, per-trial JSON, offline
aggregation/reporting and Wilson binary intervals. Existing controls and the
Browser Use adapter are reused. Both basic and verification-guided agent policies
are selectable, but no real-agent benchmark or paid call has been executed.
Checkpoint recovery is NOT implemented. This document retains future design
requirements below; it does not declare all acceptance gates completed.

## Comparison arms

| Arm | Planned behavior | Current support |
| --- | --- | --- |
| Blind retry | On uncertain confirmation, submit again without checking state | Scripted negative control only; label separately from AI results |
| Basic Browser Use | Same base business task and browser tools, no recovery-specific guidance or checkpoint layer | Implemented selectable v1.1.0 neutral task; live model outcome unverified |
| Verification-based recovery | On uncertain submission, search the CRM and inspect matching records before deciding whether to retry | Scripted positive control and selectable v1.1.0 agent task plus policy guidance; live agent behavior unverified |
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
