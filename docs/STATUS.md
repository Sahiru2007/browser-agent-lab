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
- Verify the optional Browser Use adapter with an explicitly authorized live
  provider/model and budget; no live AI-agent result is claimed yet.
- Add more versioned creation/editing workflows.
- Add authentication and session-expiry scenarios; UI variants and slow reads.
- Introduce an append-only audit ledger for create/edit/delete verification.
- Add a separate read-only PostgreSQL evaluator role, migrations with Alembic,
  and per-trial PostgreSQL isolation. Current snapshots use operator DB access.
- Add repeated paired comparisons, uncertainty estimates, and held-out tasks.
- Add a report interface and a documented external staging-app integration.

## Limitations
- Optional Browser Use adapter implemented; no live model trial verified yet.
  Existing controls remain scripted Playwright drivers, not agent results.
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
- Starter commit 88dbd22 pushed to origin/main; remote SHA matched local HEAD.
  GitHub Actions run 40373294999 passed all checks, including Chromium controls.
- No paid model calls, AI-agent runs, or PostgreSQL checks were performed.

See VERIFICATION.md for evidence and remaining limitations.

## Local browser verification milestone - 26 October 2026

- Reinstalled dependencies from both existing lockfiles; ensured the matching
  Playwright Chromium was installed. No dependency or implementation changes needed.
- Re-ran Ruff, all 13 tests, frontend production build, HTTP controls, and Chromium
  controls successfully. All six controls returned CONTROL OK with no execution errors.
- Independently read and regraded each saved trial database, comparing it with
  result.json. Inspected each browser trace's form actions and network evidence.
- Normal: one correct customer and creation event; business PASS.
- Lost confirmation with verification: aborted POST, then browser search found the
  committed customer; one customer/event, business PASS, no retry.
- Blind retry: aborted first POST followed by successful second POST; two correct
  customers/events, business FAIL with duplicate_customer, as intended.
- Confirmed separate trial databases, server processes, and browser contexts.
  Latest evidence paths and timings are in VERIFICATION.md.
- Started the normal demonstration CRM at http://127.0.0.1:8000 and verified
  health, frontend response, and rendered customer directory in Chromium.
- Only documentation changed; no GitHub push, model calls, or new features.
- Remaining limitations: nonfatal TestClient deprecation warning; optional
  PostgreSQL remains unverified. Sandbox process startup failed, so commands ran
  with approved execution outside it. No outstanding user action is required.

## Browser Use adapter milestone - 26 October 2026

- Added optional pinned Browser Use 0.13.11 extra, a small adapter boundary,
  customer.create_once v1.0.0 operator task, and a separate one-trial agent runner.
- Agent receives only the CRM URL/instruction and a restricted browser action
  registry. Assertions, seed data, fault mode and database remain operator-owned.
- Explicit Anthropic provider/model/key and step/time/call/token/USD budgets are
  required. No defaults authorize model use; live CLI also requires --allow-paid.
- Added model-call reservations, provider usage capture, filtered worker
  environment, temporary profiles, deadline supervision and independent grading
  even after execution errors. Agent success claims cannot override DB failure.
- SDK telemetry/cloud sync, automatic dotenv, LLM judging, and file/code tools
  are disabled. Reports distinguish real trials, controls and mocked tests.
- Mocked tests and a real-SDK/Chromium smoke passed without provider calls.
  Full final verification and generated report paths are recorded below in
  VERIFICATION.md. Live authentication, model performance and billing are unverified.
- Cost guard is an estimate using user-supplied price ceilings and text-size
  heuristics; use a provider-side spending cap. This is not an OS/network sandbox.
- No paid calls, Browser Use success benchmark, Git commit or GitHub push made.

## Adapter review and benchmark preparation - 26 October 2026

- Reviewed task/adapter separation, tool capabilities, usage budgets, subprocess
  cleanup, independent grading, dependency lock and credential exclusions.
- Fixed JSON-escaped credential redaction, blocked further calls after provider
  errors/cancellation with unknown usage, and retained their original stop reason.
- Enforced the browser-only tool policy after actual SDK Agent construction.
  Added a worker kill/reap fallback if Windows tree cleanup cannot execute.
- Added focused security/budget regression tests. Final results and evidence paths
  are in VERIFICATION.md. No paid APIs or GitHub push are part of this review.
- Final review verification passed: Ruff, 52 tests (including the opt-in SDK
  smoke with a mocked model), frontend build, all three HTTP controls and all
  three Chromium controls. Direct database regrading and trace action checks
  confirmed the intentional blind-retry duplicate failure remained unchanged.
- Reviewed Git exclusions and staged-file credential checks; only relevant source,
  tests, configuration, lockfile and documentation belong in the local commit.
- Added [BENCHMARK_PLAN.md](BENCHMARK_PLAN.md): proposed arms, paired trial
  manifests, checkpoint protocol, aggregate budgets, metrics and acceptance gates.
  This is a development plan, not implemented benchmark functionality.

## Benchmark Engine v1 - 27 October 2026

- Implemented deterministic seeded, paired multi-trial scheduling with scenario,
  strategy, repetition count, transport and output-directory CLI options.
- Reuses existing HTTP/browser controls, Browser Use adapter and independent
  grader. Fresh database/server/browser context per trial; sequential execution.
- Selectable scripted blind-retry/verify and real-agent basic/verification-guided
  policies. Added neutral agent task v1.1.0 while preserving v1.0.0 behavior.
- Added atomic per-trial records and start journal, run-wide estimated-budget
  admission, interruption-aware offline reconstruction, metrics/coverage and HTML
  comparison/evidence reports. Success rates have Wilson 95% intervals.
- Metric provenance distinguishes measured, estimated, unknown and unavailable;
  mocked, scripted and real-agent kinds are never pooled together.
- Added manifest schema and focused engine tests. Final commands/results and
  generated examples are recorded in VERIFICATION.md.
- Verified Ruff, 73 tests with the mocked SDK/Chromium smoke enabled, frontend
  build, all original HTTP/browser controls, 12 actual HTTP benchmark trials and
  8 actual Chromium benchmark trials. Offline reports rendered without network
  access or JavaScript. All 20 saved benchmark databases were independently regraded.
- No checkpoint recovery, paid calls, live model outcomes, Git commit or push.
  Remaining work includes live pilot authorization/configuration, held-out tasks,
  checkpoint policies, exact billing and paired bootstrap comparisons.

## Benchmark review and pilot preparation - 27 October 2026

- Reviewed and prepared Benchmark Engine v1 for a local commit. Hardened usage
  parsing so invalid call counts cannot create measured zero token usage; invalid
  or inconsistent evaluations become execution errors, never successful trials.
- Added eight regression cases. Final full suite: 81 passed with the mocked SDK
  smoke enabled; Ruff and frontend build passed. Existing scripted controls and
  offline reconstruction remain verified; no paid APIs were used.
- Added PILOT_READINESS.md. Actual provider/model, key, all limits and prices are
  absent from the inspected environment. No model is configured. The proposed
  four-trial envelope is NOT active configuration and NOT paid authorization.
- Proposed limits: up to 16 model calls, 656384 combined reserved input/output
  units, USD 4 run-wide estimated allowance (USD 1 per trial); actual pricing
  remains unknown until an explicit model and conservative prices are supplied.
- Local budget guards reserve before dispatch; they are not a provider billing
  cap. Provider-side spending controls are still unverified. Live trials are on
  hold pending configuration and explicit approval. Do not push this local work.
