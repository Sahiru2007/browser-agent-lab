# Browser Agent Lab

This is an evaluation-engineering project, not a general-purpose agent.

## Commands
- Install: `uv sync`; `npm --prefix frontend ci`; `uv run playwright install chromium`
- Check: `uv run ruff check .`; `uv run pytest -q`; `npm --prefix frontend run build`
- Browser controls: `uv run python -m lab.run`
- HTTP controls when browsers are unavailable: `uv run python -m lab.run --transport http`
- Demo application: `uv run uvicorn lab.app:create_app --factory --host 127.0.0.1 --port 8000`
- Optional SDK: `uv sync --locked --extra agent` (Browser Use 0.13.11).
- Mocked SDK smoke with real Chromium (PowerShell): `$env:LAB_TEST_BROWSER_USE="1"; uv run --extra agent pytest -q`.
- First paid trial, ONLY when explicitly authorized and environment configured:
  `uv run --extra agent python -m lab.agent_run --adapter browser-use --scenario normal --allow-paid`.

## Invariants
- Evaluate committed database state and audit history independently of the tested agent.
- Keep database credentials, reset capabilities, graders, and fault configuration away from agents.
- Distinguish evaluator/infrastructure errors from task failures.
- Never describe scripted controls as AI-agent benchmark results.
- Each trial gets a fresh database, browser context, and server process.
- Keep normal tasks alongside failure scenarios.
- Do not add paid model calls without a configured provider and an explicit run budget.
- Do not commit secrets, databases, installed dependencies, or generated run directories.
- Keep README and docs/STATUS.md accurate after each milestone.
- Run only on the supplied synthetic local app unless the user authorizes another target.
- Keep `lab.tasks.Task` operator-only. Pass only AgentRequest URL/instruction to adapters;
  worker configuration must never include assertions, seeds, faults or database access.
- Preserve separate report kinds for HTTP/browser controls, real trials, and mocked tests.
  Agent claims and framework judge output never replace the independent DB evaluator.
- Do not restore SDK file, upload, extract, search-engine, JS or shell tools. Maintain
  the positive browser-action list and test it against the pinned SDK after upgrades.
- Keep SDK telemetry/cloud sync/dotenv loading disabled. Never persist raw provider
  errors, SDK logs, profiles or credentials. Reports may contain synthetic task data.
- Model budgets reserve before every invocation; document heuristic cost limitations.
  `--allow-paid` is necessary but does not replace explicit user run authorization.
