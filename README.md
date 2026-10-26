# Browser Agent Lab

A local laboratory for testing whether browser workflows produce the correct
business effects. Milestone 01 verifies customer creation and detects duplicate
creation after a successful submission loses its confirmation.

**Current results are scripted controls, not AI-agent benchmark results.**
No model API key or paid service is needed for this milestone.

An optional Browser Use adapter is now implemented. Its SDK/browser smoke test
uses a mocked model; no real-agent success or paid run has been verified.

Verified on Windows on 26 October 2026: frontend build, 13 tests, lint, and all
three scenarios through both HTTP and Chromium browser controls.
See docs/VERIFICATION.md for evidence and remaining limitations.

## Quick start

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
Other providers are deliberately unsupported in this first adapter.

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

Limits and budgeting:

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

The next benchmark milestone is specified in [docs/BENCHMARK_PLAN.md](docs/BENCHMARK_PLAN.md).
It plans repeated comparisons of blind retry, basic Browser Use, verification
recovery and checkpoint recovery, with independently graded outcomes and usage,
timing and cost metrics. Scheduling, checkpoints and aggregate analysis are not
implemented yet.

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
