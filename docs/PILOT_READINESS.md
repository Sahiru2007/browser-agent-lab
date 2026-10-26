# Live pilot preparation - 27 October 2026

Status: **NOT READY; live execution is on hold.** No paid call is authorized by
this document, the local commit, or the presence of --allow-paid in examples.

The inspected execution environment has no LAB_AGENT_PROVIDER, LAB_AGENT_MODEL,
execution-limit variables, pricing ceilings or ANTHROPIC_API_KEY. The key was
checked only for presence; no credential value was printed or saved. .env.example
contains placeholders and proposed limits only; it is not automatically loaded.
No model has been selected or configured. Exact dollar estimates cannot be
calculated until a model and current conservative prices are supplied.

## Proposed pilot, awaiting configuration and authorization

Use the existing Anthropic adapter, browser-only tool policy and independent
database grader. One repetition, seed 42, basic-browser-use and
verification-browser-use, across normal and lost-confirmation: **4 isolated
trials**. No checkpoint arm, automatic retry, resume or extra repetition.
This is a small readiness pilot, not evidence of general model capability.

| Proposed maximum | Per trial | Entire four-trial pilot |
| --- | --- | --- |
| Steps | 12 | 48 |
| Worker execution time | 120 seconds | 480 seconds sequential worker time |
| Model invocations | 4 | 16 |
| Input allowance per call | 40000 heuristic token units | Same per-call bound |
| Provider output cap per call | 1024 tokens | Same per-call bound |
| Maximum reserved input units | 160000 | 640000 |
| Maximum reserved output tokens | 4096 | 16384 |
| Combined reservation at 4 calls/trial | 164096 | 656384 |
| Configured cumulative token ceiling | 200000 | Per-trial ceiling, not an additional shared allowance |
| Estimated USD allowance | 1.00 | 4.00 |

These are proposed bounds, not current environment settings or predicted usage.
Price admission can permit fewer calls. Wall time also includes server startup,
browser/worker cleanup and orchestration; 480 seconds is not a whole-run deadline.
Input token units use the adapter's text-size heuristic, not exact tokenization.

Let Rin and Rout be the configured conservative USD-per-million input/output
ceilings, including applicable cache-write premiums and provider multipliers.
One call reserves C = 0.04*Rin + 0.001024*Rout USD. At most four calls per trial
reserve 4*C; the four-trial pilot reserves at most 16*C for calls, subject to the
USD 1 per-trial limit. The scheduler separately reserves the full USD 1 allowance
per admitted trial, totaling USD 4. Without valid prices, 16*C is unknown.

## Enforcement already implemented

- Both the benchmark CLI and scheduler require explicit paid opt-in for real
  agent arms. Environment configuration and the pinned SDK are validated first.
- Before starting each agent trial, the scheduler durably reserves its full
  configured allowance against --max-cost-usd. Insufficient balance produces a
  not_run_budget slot; it never silently starts an extra trial. No refunds.
- Before each model invocation, reserve the input/output allowance and its
  estimated price. Reject calls exceeding count, cumulative token or USD caps.
  Reservations remain consumed for failed calls. SDK/provider retries are disabled.
- Missing usage, provider errors/cancellation or usage above estimates block
  further calls. Unknown usage is never reported as measured zero.
- Parent supervision limits worker elapsed time and attempts process-tree cleanup.
  This cannot reverse charges for a request already received by a provider.
- These are local estimated-spend guards, **not a guaranteed provider billing
  cap**. Prices and token estimates can be wrong. Provider-side project limits or
  restricted prepaid credit must be independently configured/verified; this
  project has not verified an Anthropic account spending limit.

## Before any live execution

1. Select and export the exact available Anthropic model ID, provider=anthropic,
   all LAB_AGENT limits, and current conservative input/output price ceilings.
   Keep the API key only in the operator environment. Do not paste it into chat,
   source, pilot documents, manifests or shell commands saved to the repository.
2. Configure and verify provider-side spending controls independently. Validate
   that the selected price ceilings include cache/billing multipliers.
3. Recheck the final source commit, lockfiles and no-cost controls; generate a
   fresh output directory for the authorized run.
4. Present the actual model, all effective limits and priced maximum reservation
   for explicit approval. The current instruction is to WAIT, so do not execute.

Only after that approval, the planned command is:

```sh
uv run --extra agent python -m lab.benchmark --strategy basic-browser-use verification-browser-use --scenario normal lost-confirmation --trials 1 --seed 42 --allow-paid --max-cost-usd 4 --output runs/authorized-live-pilot
```

This command has not been run. It is invalid until the environment is configured.
