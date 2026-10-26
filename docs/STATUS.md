# Status

Milestone 01 implements a React customer form, FastAPI application, SQLAlchemy
database access, independent grader, and three scripted browser control cases.
It is a development foundation, not an AI-agent evaluation product yet.

## Current control cases
1. Normal create: one correct customer and audit event; should pass.
2. Lost confirmation, verify before retry: find committed customer; should pass.
3. Lost confirmation, blind retry: two records; grader should fail business outcome.

Lost confirmation is simulated by committing the transaction, then delaying the
response for two seconds. The UI aborts after 700 ms. The first create triggers
the fault once per trial. Subsequent creates respond normally.

The application intentionally permits duplicate emails to make duplicate effects
observable. This is not a recommendation for production CRM database design.

## Next milestones
- Add a Browser Use adapter, provider configuration, step/time/cost limits, and
  clearly separated agent results. Use browser-only privileges.
- Version task definitions and add more creation/editing workflows.
- Add authentication and session-expiry scenarios; UI variants and slow reads.
- Introduce an append-only audit ledger for create/edit/delete verification.
- Add a separate read-only PostgreSQL evaluator role, migrations with Alembic,
  and per-trial PostgreSQL isolation. Current snapshots use operator DB access.
- Add repeated paired comparisons, uncertainty estimates, and held-out tasks.
- Add a report interface and a documented external staging-app integration.

## Limitations
- No real AI agent or model API call yet; controls are scripted Playwright drivers.
- An HTTP transport also exercises the server/grader when Chromium is unavailable.
  This is not a substitute for browser verification; reports identify transport.
- No login, customer editing, pagination, or external-site support yet.
- SQLite runner only; Compose provides an optional PostgreSQL development service.
- No concurrency guarantees for fault scheduling; runner executes sequentially.
- Initial schema creation uses SQLAlchemy create_all, not migrations.
- Local developer sandbox only; no production deployment or 24/7 hosting.

## Setup verification - 26 October 2026

- Installed GitHub CLI 2.103.2, uv 0.13.5, and Node.js LTS 24.22.1;
  existing Git 2.47.0 and Python 3.11.9 were available.
- Installed locked Python/frontend dependencies and Playwright Chromium.
- Ruff passed, all 13 tests passed, and TypeScript/Vite production build passed.
- All three HTTP controls and all three Chromium controls behaved as expected.
  Blind retry intentionally failed business evaluation with duplicate records.
- Expanded Git exclusions for credentials, SQLite files, local tooling, and outputs.
- Git initialized on main; authenticated GitHub account: Sahiru2007.
- Created private repository https://github.com/Sahiru2007/browser-agent-lab
  with the requested description. Local verification is complete.
- No paid model calls, AI-agent runs, or PostgreSQL checks were performed.

See VERIFICATION.md for evidence and remaining limitations.
