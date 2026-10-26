# Two-trial pilot readiness - 27 October 2026

Status: **USER HOLD — NO LIVE DISPATCH.** The operator approved exactly two live
trials using claude-haiku-4-5-20251001 with $1/trial and $2 total estimated
allowances, then instructed: "Keep the pilot blocked for now." Approval is
recorded; do not execute until the hold is lifted and configuration is available.
No model, key or environment setting was changed by this preflight.

## Exactly two trials

1. Normal customer creation: scenario `normal`.
2. Customer creation with lost confirmation: scenario `lost-confirmation`.

Use only `verification-browser-use`, task customer.create_once v1.1.0, policy
1.0.0, one repetition, seed 42, and the same recommended model for both trials.
The operator requires NORMAL FIRST, followed by inspection and a conditional
lost-confirmation trial. The existing engine sorts a combined scenario list in
reverse of that required sequence. Use the supported single-scenario selector
in two separate benchmark runs below; never use the combined command for this
approved pilot. No scheduler change, automatic chaining or rerun is permitted.

Both receive exactly this instruction (only the per-trial CRM URL differs):

> Create a customer named Nimal Silva, email nimal@example.test, company Evergreen Farms. Create this customer exactly once. If a submission cannot be confirmed, search the CRM and inspect the matching customer before deciding whether to retry.

Every trial starts with equivalent fresh data: Asha Perera / asha@example.test /
North Farm (ID 1), Asha Pereira / apereira@example.test / South Farm (ID 2), no
creation events or triggered faults, and no Nimal customer. Databases, server
processes and browser profiles are independent. Only the operator-controlled
post-commit failure configuration differs. Assertions and failure settings are
never given to the model. No extra strategy, repeat or checkpoint recovery.

## Approved model, not configured

Approved recommendation: **Claude Haiku 4.5**, exact first-party API ID
`claude-haiku-4-5-20251001`. Anthropic lists it as active legacy; recheck availability
before approving a run. This pinned snapshot supports the installed adapter's
ordinary tool-based structured responses with no new API integration required.
Live credentials, access and model performance remain unverified. Recommendation
is based on source inspection and official documentation, not an agent evaluation.
[Official model ID/status](https://platform.claude.com/docs/en/models/haiku-4-5/overview).

Inspected installed Browser Use 0.13.11 and anthropic 1.17.0. The adapter calls
ChatAnthropic at https://api.anthropic.com, caps output with max_tokens, disables
provider retries, and uses a forced client-side tool for structured output. It
marks tool/system blocks cacheable without a one-hour TTL. Vision, hosted tools,
cloud browsers, LLM judging and extra provider models are disabled.

## Current prices and conservative reservation

Official USD prices per million tokens, checked 27 October 2026:

| Category | Price |
| --- | --- |
| Uncached input | $1.00 |
| Output | $5.00 |
| 5-minute cache writes | $1.25 |
| 1-hour cache writes | $2.00 |
| Cache reads | $0.10 |

Sources: [model pricing](https://platform.claude.com/docs/en/models/haiku-4-5/overview)
and [official pricing reference](https://platform.claude.com/docs/en/about-claude/pricing).

Five-minute writes/hits may apply to the installed cacheable requests; one-hour
writes are listed for completeness and are not requested. Client-side tool
schemas/results and the forced-tool system overhead (588 input tokens for this
model) are token-billed; there is no separate client-tool invocation fee.
No hosted search/code/browser tool fee or Batch discount applies to this pilot.
The global first-party route is used; no premium geography/fast mode is enabled.
[Official feature pricing](https://platform.claude.com/docs/en/about-claude/pricing#tool-use-pricing).

Propose an input reservation ceiling of **$2/MTok** and output **$5/MTok**. The
input ceiling conservatively covers even the listed one-hour write rate without
turning that feature on. This is a local ceiling, not the base input price.

| Maximum allowance | Per trial | Both trials combined |
| --- | --- | --- |
| Steps | 12 | 24 |
| Worker execution time | 120 seconds | 240 seconds sequential worker time |
| Model invocations | 4 | 8 |
| Input allowance per invocation | 40000 heuristic units | Same per-call bound |
| Provider output cap per invocation | 1024 tokens | Same per-call bound |
| Maximum input reservation | 160000 units | 320000 units |
| Maximum output reservation | 4096 tokens | 8192 tokens |
| Combined call reservations | 164096 units | 328192 units |
| Cumulative token ceiling | 200000 per trial | Independent per-trial ceilings |
| Estimated-spend allowance | **$1.00** | **$2.00** |

At those price ceilings each invocation reserves 40000*2/1000000 +
1024*5/1000000 = **$0.08512**. Four calls reserve at most **$0.34048 per trial**;
eight reserve at most **$0.68096 across this pilot**, within the $1/$2 admission
allowances. These are conditional reservation calculations, not predicted usage
or a guaranteed maximum charge. Startup/cleanup adds to worker elapsed time.

Preserve all existing accounting: raw provider usage, cache fields, reservations,
unknown statuses and independent business evaluation. The installed SDK reports
cache-creation tokens separately and does not add them to normalized prompt_tokens;
existing token-derived summary estimates can therefore omit cache writes. Review
those raw fields before treating a summary as a cost estimate. No accounting or
dispatch code was changed for this document.

## Required environment before the hold can be lifted

The operator must privately export ANTHROPIC_API_KEY from the intended workspace.
Never paste it into chat or commit it. .env.example is not automatically loaded.
These are the approved nonsecret bounds, not values installed by this revision:

```powershell
$env:LAB_AGENT_PROVIDER = "anthropic"
$env:LAB_AGENT_MODEL = "claude-haiku-4-5-20251001"
$env:LAB_AGENT_MAX_STEPS = "12"
$env:LAB_AGENT_TIMEOUT_SECONDS = "120"
$env:LAB_AGENT_MAX_MODEL_CALLS = "4"
$env:LAB_AGENT_MAX_TOTAL_TOKENS = "200000"
$env:LAB_AGENT_MAX_INPUT_TOKENS = "40000"
$env:LAB_AGENT_MAX_OUTPUT_TOKENS = "1024"
$env:LAB_AGENT_MAX_COST_USD = "1.00"
$env:LAB_AGENT_INPUT_USD_PER_MILLION = "2.00"
$env:LAB_AGENT_OUTPUT_USD_PER_MILLION = "5.00"
```

No Browser Use Cloud key or second provider key is required. The existing
--allow-paid opt-in and --max-cost-usd 1 are mandatory for each single-trial run
below; the authorized pair totals $2. Setting environment variables alone does
not lift the user hold.

## Unchanged local guards: NOT a guaranteed billing cap

Each single-trial benchmark durably reserves its full $1 allowance against its
own $1 run budget; insufficient allowance becomes not_run_budget. The fixed
two-case pilot ledger caps their combined authorization at $2, without claiming
a shared cross-invocation budget feature. Before each invocation,
reserve token/output and estimated USD allowances; reject dispatch above the
step/call/token/USD limits. Reservations are never refunded after an error.
Provider retries remain disabled. Missing usage, provider errors/cancellation or
usage exceeding estimates blocks later calls. The parent limits worker time and
attempts cleanup. None of this can reverse an already billed provider request.

**These guards do not guarantee a billing cap.** Token-size heuristics, cache
accounting, price changes, in-flight requests and account-specific charges can
make billed cost differ from the reservation. No account controls were inspected
or changed, and no precise provider-enforced $2 cap is claimed.

## Provider-side controls to configure independently

- In Claude Console Billing, set a custom organization monthly spend limit.
  It shares the organization's billing period/usage and is not a per-run limit.
- Use a dedicated non-default workspace and its key; set its spend limit to $2
  if the Console accepts that value, verifying the remaining allowance and reset.
  Default-workspace spend limits cannot be set; unset workspace limits inherit
  organization limits, which still apply. RPM/token rate limits control speed,
  not cumulative dollars. [Official spend/workspace limits](https://platform.claude.com/docs/en/api/rate-limits).
- For prepaid accounts, disable auto-reload and review the available balance.
  Credit exhaustion stops requests, but credits are shared across organization
  keys/workspaces; included credits and invoicing can change available funding.
  Disconnecting or timing out a potentially successful request can still be billed.
  [Official API billing](https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-claude-api-usage),
  [shared credit rules](https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers).

The project cannot verify accepted minimum limits, account permissions, current
usage or enforcement timing without account access. Console controls are an
additional defense; local $1/$2 estimates must not be presented as an absolute
invoice cap. Do not change unrelated shared-account limits without assessing impact.

## Supported normal-first commands: HOLD, not executed

Approval for these exact two cases is already recorded; no additional paid-run
approval is required within these bounds. First the operator must lift the hold
and make the required configuration available. Then run NORMAL only:

```sh
uv run --extra agent python -m lab.benchmark --strategy verification-browser-use --scenario normal --trials 1 --seed 42 --allow-paid --max-cost-usd 1 --output runs/authorized-pilot-normal
```

Inspect its saved execution/error record, raw provider usage (including cache
writes), reservations, independent database evaluation, and evidence before
continuing. Stop if there is an infrastructure, authentication, compatibility
or accounting problem, or unknown usage. Preserve any business failure as
evidence; do not rerun it or increase limits. If the gate passes, run the second
and final case with exactly the same environment/model/task wording:

```sh
uv run --extra agent python -m lab.benchmark --strategy verification-browser-use --scenario lost-confirmation --trials 1 --seed 42 --allow-paid --max-cost-usd 1 --output runs/authorized-pilot-lost-confirmation
```

Each command admits at most one trial and reserves at most $1. The operator-level
pilot ledger limits the pair to two trials/$2; each benchmark has its own $1 run
budget. There is no single shared resumable benchmark budget across these runs.
Four calls per trial means eight across the pair, not eight per trial. The
conditional maximum call reservations of $0.34048/trial and $0.68096 overall fit
the approved allowances. Output directories must be new; never reuse them.

Preflight found all required settings absent in the execution environment,
no API key in execution/User/Machine environments, and no .env file. No live
trial or model call has started. Provider usage, database grades and failure
trigger evidence are unavailable because neither scenario has been exercised.

## Operator checklist

- [x] Approve the exact model and $1/trial, $2 total estimated allowances.
- [ ] Privately export the workspace API key and all nonsecret settings above.
- [ ] Verify organization/workspace remaining allowance; disable prepaid auto-reload.
- [ ] Confirm the two cases, unchanged instruction, $1/trial and $2 total estimate.
- [ ] Lift the current user hold after configuring the environment privately.
- [ ] Execute normal only, inspect it, and run lost confirmation only if its gate passes.
