# Browser Agent Lab

A local laboratory for testing whether browser workflows produce the correct
business effects. Milestone 01 verifies customer creation and detects duplicate
creation after a successful submission loses its confirmation.

**Current results are scripted controls, not AI-agent benchmark results.**
No model API key or paid service is needed for this milestone.

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

## GitHub

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
