# Browser Agent Lab

This is an evaluation-engineering project, not a general-purpose agent.

## Persistent E: storage policy
- All project downloads, installations, environments, caches and generated files
  must stay on E:. Project: E:\projects\browser-agent-lab; Ollama models:
  E:\AI\OllamaModels; installer archives: E:\AI\Downloads; other caches:
  E:\AI\Caches. Managed Python may live in E:\AI\Python.
- Before ANY download/install, inspect actual destination paths and dot-source
  `. .\scripts\use-e-storage.ps1`. Use `-Persist` only when updating the user's
  persistent storage settings. The script routes uv/npm/pip/Playwright/model and
  temporary storage to E: and prefers existing E:-resident project tool copies.
- If PowerShell blocks local scripts, start a shell with
  `powershell.exe -NoProfile -ExecutionPolicy RemoteSigned`, then dot-source it.
  Do not weaken the permanent user/machine execution policy.
- Keep .venv and frontend/node_modules inside this E: project. Do not let uv
  silently bind a replacement venv to a C: interpreter. Verify sys.base_prefix,
  uv cache/python/tool paths, npm cache/prefix, and launched browser executable
  and profile/temp paths in real child processes after configuration changes.
- No large installer/model/browser download may silently fall back to C:.
  Explain unavoidable Windows system-component/installer exceptions BEFORE
  proceeding. Prefer explicit E: install targets or portable distributions.
  Ollama's installer supports `/DIR="E:\AI\Ollama"`; do not run it implicitly.
- Do not delete or move existing installations/caches until their exact paths
  have been identified and the proposed change explained. Prefer preserving the
  original and copying required assets. Never stop unrelated running programs.
- New terminals/apps must inherit the settings; already running processes may
  retain old paths. Do not claim Ollama runtime verification from environment
  values alone if no Ollama process is installed/running.

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


## Local Ollama adapter
- `uv run --offline --extra agent python -m lab.agent_run --adapter ollama --scenario normal`
  runs one real local trial only when authorized. Lost-confirmation uses the same
  command with that scenario; do not automatically rerun model task failures.
- Keep exact loopback endpoint/model digest validation, OLLAMA_NO_CLOUD=1, one
  concurrent request, 16384 context, <=12 calls, <=300 seconds and <=2048 output
  tokens/call. No implicit pulls, cloud credentials, fallback or auxiliary models.
- Local native usage is measured when available and otherwise unavailable; local
  execution does not require monetary pricing. Keep zero provider API charges
  separate from unmeasured hardware/electricity. Do not relax paid unknown-usage
  or reservation guards. Preserve separate real_local_ai_agent_trial reports.
- Keep neutral version 1.1.0 wording identical across these local scenarios; no
  fault disclosure or operator recovery instruction. Retain failed grades.

- The completed fixed 12-slot recovery comparison is documented in
  docs/LOCAL_RECOVERY_COMPARISON.md. Use lab.local_compare --analyze for offline
  report rebuilding; do not execute additional live slots without authorization.
  Preserve its frozen manifest and both original trial directories unchanged.
  Report explicit done at the final allowed step separately from a blocked call
  or timeout; never infer business correctness from agent completion.


## Experimental uncertain-write guard
- GuardConfig / ollama-guard is a separate configuration; never alter baseline or
  verification frozen configurations to enable it. Rule/scope: docs/RECOVERY_GUARD.md.
- RecoveryGuard may use only browser actions/network/visible UI, never DB/fault,
  grading, reset or server-log information. Do not weaken the independent grader.
- Preserve pre-dispatch write blocking, complete visible-detail reconciliation
  after a fresh read, explicit unresolved failure, and guard event logging.
  Search/find_text alone is not success evidence. Never silently perform recovery
  actions or complete the agent's task. Service-worker paths remain unsupported.
- Distinguish blocked network retries, unresolved done interceptions and positive
  success claims actually overridden. A committed-state pass can coexist with
  unresolved agent recovery; report both. Do not call this generic idempotency.
- Four authorized guard trials are complete; use lab.guard_run --analyze for
  offline analysis. No additional live calls without authorization. Keep all
  earlier evidence and runs/recovery_guard_20261027/frozen-source unchanged.

## Customer editing
- Scripted edit controls: `uv run --offline --extra agent python -m lab.edit_run`.
- Preserve creation grading/audit format. EditTask remains operator-only; route
  evaluation through evaluate_task. See docs/ARCHITECTURE.md and docs/TASKS.md.
- Require stable customer identity, exact requested change, unchanged other fields
  and records, and atomic truthful audit. No-op saves produce no new event.
- Editing controls are not AI trials; the experimental guard is creation-specific.

