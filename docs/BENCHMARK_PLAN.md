# Planned milestone: reproducible recovery benchmark

Status: design only. The current runner executes individual agent trials and
scripted controls. Multi-trial agent scheduling, recovery policy arms,
checkpointing, aggregation and statistical comparisons are NOT implemented.
No real-agent benchmark results exist yet.

## Comparison arms

| Arm | Planned behavior | Current support |
| --- | --- | --- |
| Blind retry | On uncertain confirmation, submit again without checking state | Scripted negative control only; label separately from AI results |
| Basic Browser Use | Same base business task and browser tools, no recovery-specific guidance or checkpoint layer | Adapter exists, but current task includes verification guidance; a neutral task version is needed |
| Verification-based recovery | On uncertain submission, search the CRM and inspect matching records before deciding whether to retry | Scripted positive control and task guidance exist; live agent behavior unverified |
| Checkpoint-based recovery | Track workflow phases and observed browser evidence, then resume by verifying an uncertain submission before retrying | Not implemented |

Keep the scripted blind-retry baseline distinct from model-driven arms in tables
and charts. If an AI blind-retry arm is later added, explicitly specify and version
its forced retry policy and label it independently. Do not compare scripted speed
or zero model cost as if it measured the capability of an AI agent.

The current v1.0.0 prompt instructs verification before retry. Do not relabel it
as a neutral basic-agent baseline. Introduce a new task/policy version containing
the same business objective and customer data but a neutral base instruction.
Freeze the base task across agent arms; version recovery guidance/controllers
separately so any differences are intentional and reviewable.

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
