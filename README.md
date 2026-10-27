# Browser Agent Lab

A local laboratory for testing whether browser workflows produce the correct
business effects. Milestone 01 verifies customer creation and detects duplicate
creation after a successful submission loses its confirmation.

**Scripted controls and real local-agent trials are reported separately.**
The local Ollama adapter has completed one NORMAL trial (business pass) and one
LOST-CONFIRMATION trial (business fail: duplicate_customer). This is two-case
integration evidence, not a statistical benchmark. No paid trial has run.

Verified on Windows on 27 October 2026: lint, 145 tests including mocked SDK/browser
smokes, frontend build and all six HTTP/Chromium scripted controls.
See [docs/VERIFICATION.md](docs/VERIFICATION.md) for exact evidence and limitations.

## Quick start

Local Windows storage policy: before any download/install, configure the project
shell with `. .\scripts\use-e-storage.ps1`. User-level E: cache/model/temp settings
are persisted; the helper also selects E: project runtimes for the current shell.
If scripts are blocked, open `powershell.exe -NoProfile -ExecutionPolicy RemoteSigned`
first. Keep installer downloads under E:\AI\Downloads and other caches under
E:\AI\Caches. See [docs/STORAGE.md](docs/STORAGE.md) for actual runtime verification,
retained originals/backups and Windows exceptions.

Ollama 0.40.11 is now installed separately on E: with a loopback-only server.
The approved qwen3:8b-q4_K_M weights and local agent adapter are now verified.
See [docs/OLLAMA.md](docs/OLLAMA.md) for paths, startup, configuration and trial evidence.

Requirements: Python 3.11+, uv, Node.js 22.12+ (or a compatible newer LTS), npm.
Commands work from the repository root in PowerShell, Bash, or a Codex terminal.
If PowerShell blocks `npm.ps1`, use `npm.cmd` in the commands below. After installing
system tools, reopen your terminal to pick up the updated PATH.

```sh
uv sync --locked
npm --prefix frontend ci
uv run playwright install chromium
npm --prefix frontend run build
uv run pytest -q
uv run python -m lab.run
```

On Linux, install browser system dependencies if necessary:
`uv run playwright install --with-deps chromium`.

If Chromium downloads are unavailable, you can still exercise the actual server
and independent database grader using HTTP controls:

```sh
uv run python -m lab.run --transport http
```

This fallback does not test browser rendering, form interactions, or Playwright
locators. Reports explicitly identify their transport.

The last command starts a fresh application for each control, drives Chromium,
checks committed database state, and prints the generated report path.

Expected controls:

| Case | Business outcome | Control result |
| --- | --- | --- |
| Normal creation | PASS: one customer | CONTROL OK |
| Lost confirmation with verification | PASS: one customer | CONTROL OK |
| Lost confirmation with blind retry | FAIL: duplicate customer | CONTROL OK |

The third **business failure is intentional**. A passing control means the grader
detected it. Exit code zero means all three controls behaved as expected, not
that all three business workflows succeeded.

Reports go into unique folders beneath `runs/`, with JSON, HTML, traces,
screenshots, a server log, and a separate database for every trial. Run folders
are ignored by Git. For a small repeated smoke check:

```sh
uv run python -m lab.run --repeats 3
```

Traces and screenshots are generated only by the browser transport.

## Open the demonstration CRM

```sh
uv run uvicorn lab.app:create_app --factory --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000. Stop with Ctrl+C. The frontend must already be built.
The manual app uses `lab.db`; control runs never reset or reuse that database.

For frontend development, run `npm --prefix frontend run dev` in a second terminal.
Its `/api` requests are proxied to port 8000. Rebuild after frontend changes before
running the browser controls, which exercise built assets.

To enable the manual lost-confirmation scenario in PowerShell:

```powershell
$env:LAB_FAULT = "lost_confirmation"
$env:DATABASE_URL = "sqlite:///manual-fault-demo.db"
uv run uvicorn lab.app:create_app --factory --host 127.0.0.1 --port 8000
```

Use a new database filename for a fresh manual scenario; the one-shot trigger
is persisted in its fault table. The runner handles this automatically.

## Optional PostgreSQL

Docker is not required for the SQLite controls. With Docker available:

```sh
docker compose up -d
uv sync --extra postgres
```

Set `DATABASE_URL` to `postgresql+psycopg://lab:lab@127.0.0.1:5432/lab` before starting
the manual app. Credentials in compose.yaml are for a local synthetic development
database. This optional path needs separate validation on a Docker-enabled machine.

## Structure

| Path | Role |
| --- | --- |
| `frontend/` | React + TypeScript demonstration CRM |
| `lab/app.py` | Customer API and post-commit fault |
| `lab/database.py` | Tables, seed data, operator snapshots |
| `lab/evaluate.py` | Database-state and audit-history grader |
| `lab/run.py` | Isolated scripted browser control runner |
| `tests/` | Grader adversarial cases and API checks |
| `docs/STATUS.md` | Scope, limitations, and next milestones |
| `AGENTS.md` | Instructions for future Codex coding sessions |

## Working with Codex

Open this folder as a local project or in VS Code with Codex. Ask it to read
AGENTS.md, README.md, and docs/STATUS.md before making changes. Implement one
milestone per branch and inspect both the code diff and checks before merging.

## Optional Browser Use agent trials

Install the pinned open-source SDK without changing the scripted control commands:

```sh
uv sync --locked --extra agent
uv run --extra agent playwright install chromium
npm --prefix frontend run build
```

Browser Use 0.13.11 is pinned because repository main advertised an unpublished
version during implementation. The adapter follows the installed release's
`Agent`, `Browser`, `Tools`, `ChatAnthropic`, and `Agent.run(max_steps=...)` APIs.
Sources: [official agent settings](https://docs.browser-use.com/open-source/customize/agent/all-parameters),
[browser settings](https://docs.browser-use.com/open-source/customize/browser/all-parameters),
[provider setup](https://docs.browser-use.com/open-source/supported-models),
and [official repository](https://github.com/browser-use/browser-use).

Export every variable in .env.example's agent section in your shell. The example
file is documentation only and is not loaded automatically. Supply a real
ANTHROPIC_API_KEY, provider `anthropic`, an available model ID, all execution
limits, and conservative current input/output USD-per-million price ceilings.
No model or prices are selected automatically. Keep credentials in environment
variables; do not put actual keys in commands saved to source files or reports.
This `browser-use` adapter remains Anthropic-only. The separate `ollama` adapter
below needs no provider credentials or monetary price configuration.

After explicitly authorizing a paid trial, the exact command for one normal case is:

```sh
uv run --extra agent python -m lab.agent_run --adapter browser-use --scenario normal --allow-paid
```

To run the controlled failure instead, replace `normal` with `lost-confirmation`.
Every invocation runs exactly one trial, without automatic repetitions. Do not
run either command as a no-cost verification check. Missing configuration, key,
or `--allow-paid` fails before any model call. Agent commands use
`runs/agent_<timestamp>_<id>/result.json`; exit codes are 0 for independently
verified business success, 1 for business failure, and 2 for execution errors.
Execution errors may coexist with committed effects and a database evaluation.

The versioned operator task is in lab/tasks.py: ID/version, instruction, seed
data, expected customer/cardinality/audit outcome, and failure mode. Only the CRM
origin and instruction enter AgentRequest. The adapter receives execution limits
but no database URL, assertions, seeds, or fault configuration. The worker is
launched with a filtered environment, a temporary working directory/profile, and
no inherited database/fault secrets. It has only a positive list of browser
navigation, form, tab, scrolling and completion actions. File, upload, JS
evaluation, extraction-model, search-engine, shell and code tools are removed.
SDK telemetry, cloud sync, auto dotenv loading, LLM judging, planning, fallback
models, and conversation logging are disabled. The existing DB/audit checker
grades committed state after the adapter exits and the trial server stops.

Limits and budgeting for the Anthropic adapter:

- Steps are capped by Agent.run; model calls are independently counted, including
  failed calls. Provider retries are disabled. The parent process enforces total
  worker wall time (including SDK/browser startup); cleanup can take extra time.
- Before every call, reserve max_input_tokens + max_output_tokens against the
  cumulative token budget, and their configured price against max_cost_usd.
  Reservations are never refunded, even if the call fails or uses fewer tokens.
- DOM-only inputs are screened using serialized UTF-8 message/schema byte counts
  plus 8192 units of overhead. Vision is disabled. Oversized prompts are rejected
  before dispatch. Output is capped with the provider's max_tokens setting.
- This input-size check is a conservative heuristic, not a provider tokenizer or
  a guaranteed dollar cap. Supplied prices can be stale or omit cache-write
  premiums, billing multipliers or provider overhead. An in-flight call cannot
  be unbilled; a timeout can leave usage unknown. Use provider-side spend limits
  as well. Reports retain reservations and available provider token/cache usage;
  missing or underestimated usage blocks subsequent calls. No current pricing
  is hardcoded. The SDK's optional pricing lookup is disabled.

Reports label `real_ai_agent_trial`, `scripted_browser_control`,
`scripted_http_control`, or `mocked_adapter_test` separately. Agent reports include
task/version, provider/model, framework version, configured limits, duration,
usage/reservations, final agent message/claim, errors and independent evaluation.
Success claims never override database failures. SDK/provider exception messages
and stdout are discarded; known key echoes are redacted. Raw profiles/scratch
files are temporary. A killed worker can have unknown final message/usage, which
is recorded as unavailable rather than zero. The report is operator-only: it
contains the assertions/fault settings that the agent never received.

Isolation remains a local development boundary, not an OS security sandbox. The
SDK process runs as the local user and its trusted code holds the API key. Browser
domain restrictions are defense in depth, not a network firewall; redirects,
subresources or compromised browser/SDK code may bypass them. Only use this
synthetic local CRM. Worker timeout cleanup kills its process group/tree; on
Windows, an abnormal worker exit that orphans Chromium can escape tree cleanup.
Normal SDK cleanup and tested timeout paths close their resources, but provider
execution cannot be canceled reliably from here. No shared user Chrome profile,
remote browser, login state or external target is used.

No-cost tests:

```sh
uv run pytest -q
```

Optional real-SDK/Chromium smoke with a fully mocked model (PowerShell):

```powershell
$env:LAB_TEST_BROWSER_USE = "1"
uv run --extra agent pytest -q
```

Without the opt-in, that one optional smoke test skips. Mocked tests are not
real-agent evaluations. Live provider authentication, model quality, billed cost,
and recovery by an actual AI agent remain unverified. No paid calls were made
while implementing this milestone. See docs/VERIFICATION.md for actual results.

## Benchmark Engine v1

Run seeded, paired repetitions of the existing scripted strategies without a model:

```sh
uv run python -m lab.benchmark --scenario normal lost-confirmation --strategy blind-retry verify --trials 3 --seed 42 --transport http --output runs/my-http-benchmark
uv run python -m lab.benchmark --scenario normal lost-confirmation --strategy blind-retry verify --trials 2 --seed 42 --transport browser --output runs/my-browser-benchmark
```

`--trials` means repetitions **per scenario and strategy**: the first command
starts 12 isolated trials. The output directory must not exist; prior evidence is
never overwritten. Omitting `--output` creates a unique directory under runs/.
Use runs/ to keep artifacts ignored by Git; custom paths elsewhere are not
automatically added to .gitignore.
Defaults are both scenarios, both scripted strategies, one repetition, browser
transport and ordering seed 0. No checkpoint strategy exists.

Each block pairs the same scenario/repetition across strategies, shuffling arm
order with the recorded seed. IDs, task data, policies and schedule are deterministic;
ports, process IDs, timings and model outputs are not. Every trial gets a fresh
database/server and browser context/profile. Browser controls launch a fresh
Chromium process as well. Execution is sequential; this is not a load test.

Real-agent strategies are `basic-browser-use` (neutral task v1.1.0) and
`verification-browser-use` (same objective plus versioned recovery guidance).
The existing v1.0.0 task and scripted controls remain unchanged in behavior.
Agent arms use the existing Browser Use adapter, filtered environment, restricted
tools, limits and independent grader. Only browser transport is allowed for agent
arms. Live execution requires all existing environment configuration, explicit
paid authorization and `--max-cost-usd` for the entire run. For example, **only
after separate paid authorization**, two agent arms across two scenarios with
one repetition each can use:

```sh
uv run --extra agent python -m lab.benchmark --strategy basic-browser-use verification-browser-use --scenario normal lost-confirmation --trials 1 --seed 42 --allow-paid --max-cost-usd 4 --output runs/live-agent-pilot
```

That example assumes the per-trial estimated cap is USD 1. Before each agent
trial the full per-trial cap is durably reserved from the run-wide budget; no
refund is made for failures, low usage or unknown usage. Trials exceeding the
remaining allowance are labeled `not_run_budget`, never silently dropped. The
scheduled trial count bounds calls to the runner; no automatic retries occur.
This project has not run that paid command or measured real-agent performance.

Outputs are manifest.json, summary.json, report.html and
trials/trial-NNNNNN/result.json, with raw runner JSON/database/logs and browser
screenshots/traces beneath each trial's evidence/ directory. The manifest records
the seed, complete schedule, task/policy versions, model/limits, lockfile hashes,
source commit and dirty-working-tree digest, and installed framework versions.
Its schema is [docs/benchmark-manifest-v1.schema.json](docs/benchmark-manifest-v1.schema.json).
The offline report needs no internet, CDN or JavaScript and links individual trial
evidence. Recompute it without execution, credentials or model calls:

```sh
uv run python -m lab.benchmark --analyze runs/my-http-benchmark
```

Reports separate scripted HTTP/browser controls, real-agent trials and mocked
tests by kind, strategy, scenario, task/policy version and model. Operational
success uses all started trials; business success and duplicate-action rates use
valid independent evaluations, with missing evaluations counted explicitly.
Binary rates include Wilson 95% intervals. They describe the observed sample;
intervals for deterministic scripted controls are not measurements of AI ability.
Repeated-click counts are not the definition of duplicate business effects.

Every metric has a `measured`, `estimated`, `unknown` or `unavailable` status.
Timing summaries include wall/driver durations where recorded, median and p95.
Model calls, reported input/output/cache tokens, upper-rate cost estimates and
conservative budget reservations are retained separately; scripted model metrics
are unavailable rather than zero-cost AI results. Partial usage remains unknown
with known subtotals and explicit coverage. Provider invoices are unavailable.
Timeout/interruption wall times include cleanup and do not imply completed-task
latency. Costs still depend on operator-supplied price ceilings and the adapter's
documented estimation limits; use provider spending caps.

Trial records and reservations are written atomically before dispatch. Ctrl+C
retains completed/interrupted/not-started slots and generates a partial report;
after abrupt termination, `--analyze` recognizes unfinished records without
rerunning them. This is evidence recovery, not checkpoint-based task recovery or
resume. No bootstrapped paired differences or held-out customer variants exist
yet. See [docs/BENCHMARK_PLAN.md](docs/BENCHMARK_PLAN.md) for remaining work.

Exit codes: 0 means scheduling finished without execution/control errors (the
scripted blind-retry business failure is expected), 1 means a real-agent business
failure, 2 means execution errors or budget-skipped trials, and 130 means an
interrupted run. Offline analysis returns 0 when reconstruction succeeds; it does
not declare the underlying trials successful.

The current live-run configuration check and proposed bounded pilot are documented
in [docs/PILOT_READINESS.md](docs/PILOT_READINESS.md). Live execution is on hold;
example limits are not active model configuration or authorization.

## Local-only Ollama agent

Uses the existing optional dependency (`uv sync --locked --extra agent`), without
upgrading Browser Use 0.13.11 or Ollama SDK 0.6.1. Inspect/start the E: server as
shown in [docs/OLLAMA.md](docs/OLLAMA.md); do not pull another model implicitly.

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.agent_run --adapter ollama --scenario normal
# A separate trial, only when explicitly authorized:
uv run --offline --extra agent python -m lab.agent_run --adapter ollama --scenario lost-confirmation
```

Each command runs once; these are not instructions to repeat the retained trials.
No API key, .env loading, `--allow-paid` or paid-provider configuration is needed.
The explicit selector chooses the fixed approved endpoint/model/settings:
127.0.0.1:11434, qwen3:8b-q4_K_M and its recorded digest, 16384 context,
one concurrent request, 12 calls/12 steps, 300 seconds and 2048 output tokens/call.
The parent enforces worker duration; bounded cleanup may add wall time. Output
capacity is at most 24576 tokens/trial, not a prediction of actual usage. Context
is per call, not a cumulative input-token allowance. Failed invocations count.

Preflight checks the actual loopback-only listener, server cloud/concurrency/model
storage environment and installed model digest. It never downloads a missing model.
Requests use supported ChatOllama host/options/client_params with proxy inheritance
and redirects disabled and a request guard requiring the exact local /api/chat URL.
No cloud/fallback/extraction/judge/planner/compaction model is enabled; only the
existing positive browser-action list is exposed. Workers inherit no provider keys.

Native response hooks retain prompt/completion/cache counters even when SDK JSON
validation fails. Missing counters are labeled unavailable, never fabricated;
local calls may continue without monetary pricing under their own call/time/output
limits. **Anthropic unknown-usage and reservation safeguards are unchanged.**
Local reports use `real_local_ai_agent_trial`, with zero provider API charges
separate from unmeasured electricity/hardware costs. They retain final responses,
model outputs, action history, screenshots, trace.zip, database and independent grade.
Playwright observes the SDK's CDP-driven browser: action history supplies semantic
actions, while the trace supplies network/screenshots; it is not a replay script.

The neutral task version 1.1.0 is identical between scenarios and gives no recovery
prescription. Fresh app databases, servers, browser processes/profiles/contexts are
used. Ollama itself and its prompt cache remain shared, affecting latency/cache
counts; context allocation does not validate full-context task quality. Local user
process isolation is not an OS/network sandbox. A hard-killed worker may leave
incomplete trace/final-response evidence, while progress accounting and committed
DB grading remain available. Multi-trial benchmark CLI integration for this new
local provider is not implemented; use the single-trial CLI above. Paid pilot hold
and existing paid benchmark dispatch guards remain intact.

## GitHub repository

Private repository: https://github.com/Sahiru2007/browser-agent-lab

For a separate new copy, authenticate using `gh auth login` and create your own
private repository (do not reinitialize an existing checkout):

```sh
git init -b main
git add .
git commit -m "Add CRM reliability laboratory and browser controls"
gh repo create browser-agent-lab --private --source=. --remote=origin --push
```

Review author details and files before committing. Existing Git repositories
should use their current remote. GitHub Actions runs on pushes and pull requests;
check its status on GitHub separately from local verification. Choose a license
before publicly distributing the project.


## Exploratory local recovery comparison

A frozen 12-trial comparison is complete: baseline and a general uncertain-write
verification instruction, each tested once on three matched starting-data seeds
under normal and lost-confirmation conditions. Both configurations passed 3/3
normal trials and created duplicates in 3/3 lost-confirmation trials. The added
instruction did not prevent duplicate writes in this sample. All agents issued
done; ten did so at the final allowed step. This is exploratory evidence, not
proof of reliability, and shared Ollama cache prevents timing-isolation claims.

See [the protocol and results](docs/LOCAL_RECOVERY_COMPARISON.md). The offline
report is runs/local_recovery_comparison_20261027/report.html. Recompute without
model calls using `uv run --offline --extra agent python -m lab.local_compare
--analyze runs/local_recovery_comparison_20261027`. No additional live run is
implied by this documentation. Original two-trial evidence is preserved unchanged.


## Experimental browser write guard

A separate local-only guarded configuration enforces request blocking at the
browser context, rather than relying only on a recovery prompt. After a write,
unknown outcomes keep further writes blocked until a fresh read shows one visible
record matching all submitted details. It returns an explicit unsuccessful
unresolved result when that evidence is missing; it never substitutes for grading.
No database/fault information, uniqueness constraint or idempotency is used.

Four real local trials are retained: both normal trials resolved visibly; both
lost-confirmation trials remained unresolved. All four had one correct committed
customer and no duplicate. No live repeated write was attempted, so network-gate
blocking is established by technical browser tests, not those four outcomes.
The guard intercepted two unresolved done actions and overrode one positive
success claim. This is an exploratory CRM-specific experiment, not generic
recovery or proof of reliability. See [the full rule and results](docs/RECOVERY_GUARD.md).

Offline report: runs/recovery_guard_20261027/report.html. Rebuild without inference:
`uv run --offline --extra agent python -m lab.guard_run --analyze runs/recovery_guard_20261027`.
The four-slot execution requires fresh authorization to repeat. Existing baseline,
verification, paid-provider guards and original evidence remain unchanged.


The retained unresolved guard cases are diagnosed in
[GUARD_DIAGNOSIS.md](docs/GUARD_DIAGNOSIS.md): no post-submission directory reads,
8/9 in-page search-loop calls, final-step unresolved termination. No correct fresh
record was rejected. Unsupported-context coverage and the future-message wording
fix are recorded separately. No new model calls were made for that diagnosis.


A fresh four-trial feedback ablation is documented in
[FEEDBACK_ABLATION.md](docs/FEEDBACK_ABLATION.md). Original versus clarified feedback
each reconciled 1/2 lost-confirmation trials; all four committed business outcomes
passed, with no duplicates. Fresh GET and matching visible row evidence are
reported separately. This small shared-cache study establishes no aggregate
recovery improvement. Offline report: runs/feedback_ablation_20261027/report.html.
Use lab.feedback_run --analyze for model-free rebuilding; do not rerun live slots.


## Customer editing controls

Search for an existing customer, open their labeled details link, and edit company
or email. Saves are validated and atomically audited; no-op saves add no event.
Two versioned email-identified tasks have independent identity/field/audit grading.
After building the frontend, run `uv run --offline --extra agent python -m lab.edit_run`.
These are scripted browser controls, not AI-agent results. See
[architecture](docs/ARCHITECTURE.md) and [task contracts](docs/TASKS.md).
No edit-specific faults or live editing-agent trials have been added.


The subsequent six-attempt unguarded local editing pilot is complete; see
[EDITING_PILOT.md](docs/EDITING_PILOT.md). All six independent DB grades pass,
but only three agent success claims are true; all trials finish at the call ceiling.
These exploratory observations supersede the earlier milestone's "no live editing
trials" status. Agent CLI now supports --task company|email with --scenario normal;
benchmark selectors and creation-specific recovery scope remain unchanged.
