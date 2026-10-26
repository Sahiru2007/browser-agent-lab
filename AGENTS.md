# Browser Agent Lab

This is an evaluation-engineering project, not a general-purpose agent.

## Commands
- Install: `uv sync`; `npm --prefix frontend ci`; `uv run playwright install chromium`
- Check: `uv run ruff check .`; `uv run pytest -q`; `npm --prefix frontend run build`
- Browser controls: `uv run python -m lab.run`
- HTTP controls when browsers are unavailable: `uv run python -m lab.run --transport http`
- Demo application: `uv run uvicorn lab.app:create_app --factory --host 127.0.0.1 --port 8000`

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
