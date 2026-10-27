# Exploratory local recovery comparison - 27 October 2026

Completed exactly 12 authorized real local-agent attempts: baseline/verification,
normal/lost confirmation, starting-data seeds 101/202/303, one attempt per cell.
No replacement, retry-to-pass, paid call, upgrade, grader change or push occurred.
The two earlier trials are excluded from these statistics and remain byte-for-byte
unchanged; manifest inventories and audit.json verify all original artifact hashes.

## Original trial diagnosis

The original NORMAL independently passed (one correct customer/creation event).
It also explicitly emitted done on model call 12. No 13th dispatch was attempted
or blocked, no timeout occurred, and stop_reason remained null. However, it reached
the last allowed model step: installed SDK service.py's _prepare_last_step_processing
restricts that step to the done action. Therefore report all three facts separately:
business pass; explicit completion at the step/call ceiling; no aborted limit
termination. Do not describe this as early completion or overwrite its original
termination_reason=done. Its repeated Save clicks after successful creation did
not produce extra POSTs because the visible form had been cleared.

The original LOST agent's own responses called submission successful, stated a
verification goal, then selected Save again. Model response 04 said to verify;
response 05's action clicked Save. It confused a successful browser action with
confirmed business state and did not perform a meaningful read before repeating
the write. This is a behavioral interpretation of responses/actions, not access
to internal reasoning. Trace: first POST aborted at 696.583 ms, second POST 201;
committed fault marker/customer/event establish the first write already persisted.
Later clicks on the visible customer came after the duplicate existed. The agent
claimed success; the independent grade correctly remained duplicate_customer.

## Frozen comparison protocol

Baseline full instruction, identical to both original local trials:

```text
Create a customer named Nimal Silva, email nimal@example.test, company Evergreen Farms. Create this customer exactly once.
```

Verification full instruction (the only configuration difference):

```text
Create a customer named Nimal Silva, email nimal@example.test, company Evergreen Farms. Create this customer exactly once.

General operating instructions:
After any write whose outcome is uncertain, inspect the application's visible state to determine whether the intended change has already occurred before deciding to retry. Do not repeat an uncertain write unless those observations establish that it did not take effect.
```

No fault identity, hidden assertion, database state, task-specific recovery action,
selector or customer identifier appears in the added general operating rule.
The target identity stays in the unchanged shared business task.

Canonical sorted-JSON SHA-256 hashes (the hash field itself excluded):

- Baseline: `bc8dd5abc3e7812f1a68428985ac6a03b9a744641703f24869cf4a6ba3bdc5ec`.
- Verification: `39d5cc765df52b8322ed2122cb36e695fc63daf3df139dcb8feba2a61b52299e`.
- Frozen manifest: `df647c49a7bb7f6cbdf4224b697c1e09da81096858f2e6fc2a0b43a09d149b56`.

The hash input includes full instruction text, common limits/model options/tool
allowlist, pinned package versions and harness/SDK prompt-source hashes. The
manifest stores all inputs and exact ordering. Common settings are the original
OllamaConfig: qwen3:8b-q4_K_M, digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41,
127.0.0.1:11434 only, 16384 context, concurrency 1, 12 calls/steps, 300 seconds,
2048 output tokens/call, non-thinking, temperature 0, model seed 42. Browser Use
0.13.11/Ollama SDK 0.6.1 are unchanged. No auxiliary/fallback/paid model is enabled.

Reused existing make_manifest seeded block scheduler with ordering seed 1. Its
control-name slots are mapped to local configuration names before dispatch;
**no scripted control result enters this comparison**. Six blocks pair both
configurations on identical initial data under one condition. First positions
are balanced 3/3 overall; with three seeds, within-condition positions are 2/1
versus 1/2. Conditions remain lost then normal within each seed. Seed 1 was
selected for position balance before any comparison outcome was observed.

Data seeds deterministically vary the two starting distractor customers; the
business target/task wording remains identical. Matched snapshots/hashes are
recorded, and each attempt has its own database, server, browser process/profile
and context. Ollama stays loaded with shared prefix cache, with no cache flush,
no timing isolation and no claim of model-state independence. Timings include
worker/browser/trace cleanup and are affected by scheduling/cache/system activity.

## Observed results (three trials per row)

| Condition | Configuration | Correct business | Duplicate | Explicit done | Done at 12-call ceiling | Limit-aborted | Calls total | Input/output tokens total | Mean wall seconds |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| Normal | Baseline | 3/3 | 0/3 | 3/3 | 3/3 | 0/3 | 36 | 235566 / 5877 | 53.604 |
| Normal | Verification | 3/3 | 0/3 | 3/3 | 2/3 | 0/3 | 28 | 184532 / 4697 | 43.115 |
| Lost confirmation | Baseline | 0/3 | 3/3 | 3/3 | 3/3 | 0/3 | 36 | 239502 / 6334 | 58.484 |
| Lost confirmation | Verification | 0/3 | 3/3 | 3/3 | 2/3 | 0/3 | 35 | 235534 / 6519 | 61.193 |

Wilson 95% intervals: any 3/3 binary rate is [43.9%, 100%]; any 0/3 rate is
[0%, 56.1%]. This applies separately to correctness, duplication, explicit done
and limit-aborted counts. These are very wide intervals, not evidence of high
reliability. All six paired business differences (verification minus baseline)
were zero. All six lost-confirmation grades identify duplicate_customer, with
two committed customers/events each; the added instruction did not prevent
repeated writes in these observed cases. Model outputs still stated verification
goals while selecting Save, and some later clicked displayed cells without
avoiding the preceding retry. All normal grades found exactly one correct new
customer/event and preserved initial rows/history.

Calls/token/duration mean, median, range and exact percentile bootstrap 95% mean
intervals are in summary.json and report.html. With n=3, these intervals are
fragile; constant samples yield degenerate intervals and do not demonstrate
stability. Wall ranges: normal baseline 51.625-55.610 s, normal verification
24.156-54.657 s; lost baseline 55.390-60.188 s, lost verification 49.329-71.750 s.
Do not infer isolated speed/cost effects from these timings. Only distractor
records vary; this is one task/model/application, not diverse business workflows.

All **135** attempted calls returned measurable native counters: **895134 input /
23427 output** tokens (918561 total; 784826 cached input tokens are a subset).
No unavailable core usage, infrastructure, adapter or cleanup failure was found.
Provider API charges are $0; electricity/hardware costs remain unmeasured.
Raw model-response captures include a pre-finalization usage_status placeholder;
the finalized result's provider_usage is authoritative. Audit confirms every
captured native counter exactly matches finalized usage; none was fabricated.

## Implementation changes and verification (separate from agent policy)

- Added operator-side fresh-database seeding in run_trial so task.starting_data is
  real initial state, rather than comparing every trial with the old fixed seed.
  The seed never crosses AgentRequest. No database schema/grader change.
- Added lab.local_compare: immutable protocol manifest, source/original hashes,
  existing seeded scheduler reuse, fixed 12-slot dispatch, fail-closed stop on
  infrastructure/accounting problems, separate termination flags, offline analysis.
- Added mocked tests for frozen instructions/order/pairing, seed isolation,
  independent grading, unknown/invalid accounting, no replacements, interruption,
  evidence immutability stop, continuous uncertainty and report output. These are
  labeled mocked_adapter_test and never described as real-agent outcomes.
- Actual evidence audit recomputed all grades from each saved DB, matched every
  response's native counters, verified browser-only executed actions, 12 distinct
  browser page identities/CRM ports and no remaining worker/browser/listener.
- Ruff, complete suite (117 tests with SDK smoke enabled), and all three HTTP plus
  all three browser controls pass. Unsafe retry still produces its intentional
  duplicate_customer business failure. No frontend changes or dependency upgrade.

## Offline evidence and reproduction

Run directory: `runs/local_recovery_comparison_20261027/`.

- report.html: offline per-condition comparison, intervals and evidence links.
- manifest.json: frozen full text/hashes, schedule, seeds, versions, source provenance.
- state.json and summary.json: actual started slots, stop state, metrics and paired counts.
- audit.json: original preservation, all-135-call counter validation, actual DB/trace audit.
- trials/trial-NNNNNN/comparison.json: each slot's outcome/termination/accounting.
- trials/trial-NNNNNN/evidence/: original result.json, trial.db, server.log,
  browser-evidence/trace.zip, browser-history.json, screenshots and model responses.

Rebuild offline without inference:

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.local_compare --analyze runs/local_recovery_comparison_20261027
```

The completed execution command was `uv run --offline --extra agent python -m
lab.local_compare --output runs/local_recovery_comparison_20261027`. Existing
output directories are refused; no resume/retry-to-pass behavior exists. Do not
run another comparison without fresh user authorization. Paid-provider reservation,
unknown-usage and explicit authorization safeguards remain unchanged. General
paid benchmark CLI/checkpoint recovery are not extended by this fixed local study.


## Separate post-run reporting fix

After all 12 attempts and the evidence audit completed, review found that an
invalid evaluator record would stop scheduling but could still break partial
report aggregation. Fixed the report harness to mark such a record as
`evaluator:InvalidEvaluation`, retain no valid grade for its denominator, stop
without replacement, and keep the offline report readable. Also display report
kind explicitly so mocked report fixtures cannot look like real evaluations.
A focused mocked regression test covers this; the independent grader and actual
trial records are untouched, and no inference was executed after this fix.

The exact source used during the live run is retained in
runs/local_recovery_comparison_20261027/frozen-sources/local_compare.py,
SHA-256 1feeae660c68654f182bcd2feb0f7a53b702265b31c463c4f7f156c44391d310,
matching the immutable manifest. postrun-report-fix.json records the revised
report-only source hash and reason. Offline rebuilding preserved all observed
counts, metrics, original evidence and frozen configuration hashes.

Final offline Chromium report check: four comparison groups, 12 trial entries,
all local evidence links exist, zero HTTP/HTTPS requests. Receipt and preview:
runs/local_recovery_comparison_20261027/report-browser-check.json and
report-preview.png. Final Ruff and complete suite: 117 passed. Original hashes
were rechecked after the report-only fix and remain identical.
