# Verification - 26 October 2026

Executed against the supplied synthetic local CRM on Windows:

| Check | Result |
| --- | --- |
| Locked Python dependency installation | Passed: uv sync --locked |
| Locked frontend dependency installation | Passed: npm ci; zero reported vulnerabilities |
| Ruff | Passed |
| pytest | 13 passed; one Starlette TestClient deprecation warning |
| TypeScript and Vite production build | Passed using Node 22.23.4 and system Node 24.22.1 |
| Playwright Chromium installation | Passed |
| HTTP controls | All three CONTROL OK |
| Chromium browser controls | All three CONTROL OK |
| Git exclusions | Checked credentials, databases, node_modules, runs, local tools |

Both transports verified normal creation and recovery after lost confirmation:
exactly one matching customer and its audit event. Blind retry created two
customers and the independent grader detected the expected business failure.
These are scripted controls, not AI-agent benchmark results.

Every trial used a fresh SQLite database and Uvicorn process. Every browser trial
used a fresh browser context, with screenshots and Playwright traces captured.
Evaluator snapshots read committed customer and audit state independently of
the driver and UI confirmation messages. All six reports had no execution error.

Ignored local evidence:

- HTTP: runs/20261026T174729Z_9225e6ba/report.html
- Chromium: runs/20261026T175014Z_6ceaff8a/report.html
- Per-trial JSON, database, server log; browser trials also contain final.png
  and trace.zip.

System tools: Git 2.47.0.windows.2, GitHub CLI 2.103.2, Python 3.11.9,
uv 0.13.5, Node LTS 24.22.1. The initial Node 20.18 was unsupported; a
temporary ignored local Node 22 installation ran the successful build before
the system upgrade completed. Local bootstrap tools remain ignored in .tools/.
Use npm.cmd if PowerShell execution policy blocks npm.ps1.

GitHub CLI browser authentication succeeded as Sahiru2007. Created and verified
the private repository https://github.com/Sahiru2007/browser-agent-lab with the
requested description. Starter commit 88dbd22 was pushed to origin/main and its
full SHA independently matched GitHub's main commit. GitHub Actions passed all
checks on that starter commit, including HTTP and Chromium controls:
https://github.com/Sahiru2007/browser-agent-lab/actions/runs/40373294999
The successful run uploaded control artifacts. GitHub reported a nonfatal
deprecation annotation for the actions' Node 20 runtime (forced to Node 24);
update action versions during future dependency maintenance.
No Docker/PostgreSQL run, AI-agent run, or paid model
call was performed. The TestClient deprecation warning is nonfatal; review it
when upgrading dependencies.

example-control-results.json preserves the original synthetic HTTP examples.
The local reports above are the evidence for this setup verification.

## Fresh local milestone verification - 26 October 2026

Started from a clean main working tree at 08e4f79. Preserved the implementation,
lockfiles, evaluator, expected outcomes, and existing history. No push performed.

Versions checked: Python 3.11.9, uv 0.13.5, Node.js 24.22.1, npm 11.1.0.
PowerShell requires npm.cmd because npm.ps1 is blocked by its execution policy.
The sandbox process helper failed before command execution with
`helper_unknown_error: setup refresh had errors`; all subsequent commands ran
successfully with approved execution outside the sandbox. This was an
environment issue, not an application, driver, or evaluator failure.

| Command | Actual result |
| --- | --- |
| uv sync --locked | Passed; existing lockfile unchanged |
| npm.cmd --prefix frontend ci | Passed; 21 packages, zero reported vulnerabilities |
| uv run playwright install chromium | Passed; required browser available |
| uv run ruff check . | Passed |
| uv run pytest -q | 13 passed; one existing TestClient deprecation warning |
| npm.cmd --prefix frontend run build | Passed: TypeScript and Vite |
| uv run python -m lab.run --transport http | All three CONTROL OK; exit 0 |
| uv run python -m lab.run | All three Chromium controls CONTROL OK; exit 0 |
| Independent evidence inspection | All six saved databases regraded successfully; all browser traces inspected |

Reports (ignored, relative to repository root):

- HTTP: runs/20261026T180417Z_a5cce32f/report.html
- Browser: runs/20261026T180424Z_e3fe5c9f/report.html
- Browser evidence summary: runs/20261026T180424Z_e3fe5c9f/evidence-inspection.json

Each report folder contains summary.json. Browser trial subfolders below each
contain result.json, trial.db, server.log, final.png, and trace.zip:

| Browser trial subfolder | Business result | Verified effects |
| --- | --- | --- |
| normal_reference_ed2f3ada | PASS | One matching new customer and one creation event; POST 201 |
| recover_after_lost_confirmation_22bc44b2 | PASS | One matching new customer/event; browser search returned that record without retry |
| detect_unsafe_retry_adcfb94d | Expected FAIL | Two matching new customers/events; exactly duplicate_customer reported |

Inspected trace.trace, trace.network, referenced response bodies, and screenshot
entries in all three archives. All traces recorded Chromium navigation, three
form fills, and Save clicks. Recovery recorded a fourth fill into the search
field and a one-cell assertion. Blind retry recorded two Save clicks and two
POSTs. Final screenshots were present for every browser trial.

Recovery's first POST ended with net::ERR_ABORTED after 708 ms; its subsequent
search GET returned the committed customer about 843 ms after that POST began,
before the two-second delayed confirmation could complete. Blind retry's first
POST aborted after 713 ms; the second POST returned 201 with customer ID 4. Its
fault row referred to customer ID 3, and both creation events persisted. The
application's engine.begin block commits customer, event, and fault together
before entering asyncio.sleep(2), confirming the fault happens after commit.

All six result files had execution_error null and matched their summary entries.
Direct SQLAlchemy snapshots of all six final SQLite databases matched the saved
after states; independent evaluator calls reproduced their evaluations. Initial
states contained only the two seed customers and no audit events. Existing
customers remained unchanged. There were no application, driver, or evaluator
errors; duplicate_customer is the intentional third business failure.

Browser trial databases live in distinct trial folders. Server logs show separate
processes (31724, 40588, 25672) and ports (60311, 51151, 50663) for normal,
recovery, and blind retry respectively. Source inspection confirmed new_context
and context.close for every trial; the three trace archives contain separate
context metadata and distinct page identities. The browser process is shared,
but browser contexts, databases, and server processes are fresh per trial.

Port 8000 had no listener before startup; no unrelated process was stopped.
Started the normal demo with LAB_FAULT=none and sqlite:///lab.db. Verified
/api/health, the frontend HTML, and the rendered customer directory in Chromium.
Local URL: http://127.0.0.1:8000. Ignored runtime files: runs/demo/server.pid,
runs/demo/stdout.log, runs/demo/stderr.log, runs/demo/demo.png, and lab.db.
The demo is a local background process, not persistent hosting.

No implementation fixes were necessary, so no post-fix test rerun was required.
Only status/verification documentation changed. Optional PostgreSQL remains
unverified; no Browser Use adapter, AI-agent calls, or additional features were
added. No blocker currently requires user action.

## Browser Use adapter milestone - 26 October 2026

Implemented the optional adapter without paid calls. Preserved earlier uncommitted
local-verification documentation updates. No Git commit or push was performed.

Reviewed official Browser Use agent/browser parameters, provider examples and
repository source (links in README). Repository main advertised 0.13.13, but
dependency resolution rejected it as unpublished. Checked PyPI and pinned the
published 0.13.11 release. Inspected installed constructors, action registry,
model protocol, usage fields, history and cleanup APIs. The optional extra adds
many transitive lockfile entries; the base project does not install those packages.

| Verification | Actual result |
| --- | --- |
| uv sync --locked --extra agent | Passed; Browser Use 0.13.11 installed |
| Ruff with agent extra | Passed |
| Full suite with LAB_TEST_BROWSER_USE=1 and agent extra | 47 passed |
| Actual SDK + local Chromium + mocked model smoke | Passed; zero provider calls |
| uv sync --locked without extras | Passed; optional SDK removed |
| Ruff without SDK | Passed |
| Base pytest suite without SDK | 46 passed, 1 optional smoke skipped; existing TestClient warning |
| npm.cmd --prefix frontend run build | Passed |
| HTTP controls | All three CONTROL OK; exit 0 |
| Chromium controls | All three CONTROL OK; exit 0 |

The optional smoke uses an in-memory mocked model, forbids Anthropic client
creation, and runs the actual SDK/browser. It verifies the tool allowlist after
Agent construction, reservations, reported token usage and cleanup. The model
claims success without creating a customer; the database grader correctly FAILS
that trial. This is a mocked adapter test, NOT a real-agent evaluation.

Focused tests also cover adapter selection, every required configuration field,
missing credentials, invalid/nonfinite limits, token/USD/call budget exhaustion,
oversized prompts, unavailable usage, filtered worker environment, URL validation,
actual worker timeout/failure cleanup, and server cleanup after adapter errors or
timeouts. Mocked success claims with missing or duplicate customers still fail
the unchanged evaluator. Key echoes/raw exception strings are excluded from
reports. Mocked reports are labeled mocked_adapter_test.

The first run exposed a test-only Windows assumption: a closed localhost port can
time out instead of immediately refusing connection. The cleanup assertion now
accepts either failure; business assertions were unchanged. SDK import initially
hit a user-config directory permission error; workers now use a temporary
BROWSER_USE_CONFIG_DIR. All checks above were rerun after these corrections.

Final scripted-control reports:

- HTTP: runs/20261026T181917Z_75f9ef02/report.html
- Chromium: runs/20261026T181924Z_e9da8714/report.html

Normal/recovery created one matching customer and event; blind retry created two
and reported exactly duplicate_customer. Reports include customer.create_once
version 1.0.0 metadata. Browser trial folders retain result.json, final.png,
trace.zip, server.log and isolated trial.db. These are scripted controls.

Unverified: live provider authentication, model workflow/recovery, actual billing,
PostgreSQL and other providers. Text-size heuristics and operator price ceilings
are not guaranteed provider billing caps. Unknown/underestimated usage blocks
later calls but cannot undo billing. Timeouts can lack final usage/message;
worker progress preserves reservations when available. Use provider spend limits.
This is not an OS/network sandbox: trusted SDK code runs as the local user, and
Windows abnormal worker exit may orphan Chromium descendants. Normal and timeout
cleanup paths were tested, not every crash mode. Base dependencies are currently
installed; the live command installs the optional extra.

First live run requires ANTHROPIC_API_KEY, explicit provider/model, and all
LAB_AGENT limits/pricing variables in .env.example. Its example envelope is 12
steps, 120 seconds worker time, 4 model calls, 200000 reserved tokens, 40000 input
and 1024 output units per call, and USD 1.00 estimated budget. Supply current
price ceilings and an available model ID. Only after explicit paid authorization:

```sh
uv run --extra agent python -m lab.agent_run --adapter browser-use --scenario normal --allow-paid
```

No paid trial was authorized or executed in this milestone.

## Final adapter review and local commit verification

Reviewed all pending source/configuration/test/documentation changes and the
dependency lock. The optional SDK is pinned; registry sources use PyPI. Existing
grader logic and control outcomes were preserved. No actual credential material
or generated artifacts were found in the reviewed commit files. Git ignore checks
confirmed .env, .env.local, nested .env, credentials.json, private keys, databases,
node_modules, .tools and runs are excluded; .env.example is a placeholder-only
tracked template. Staged content is scanned before the local commit, without
printing environment secrets.

Review corrections:

- Redact decoded nested values before JSON serialization so quotes, backslashes
  and newlines in credentials cannot defeat redaction.
- Retain the reservation and block additional dispatch after provider exceptions
  or cancellation with unknown usage; preserve the original stop reason.
- Validate the positive browser-action list after SDK Agent construction at
  runtime, before the first model call, rather than relying only on smoke tests.
- Always attempt worker kill/reap if Windows taskkill is unavailable or times out.
  This does not eliminate the previously documented orphan-descendant limitation.

| Final check | Actual result |
| --- | --- |
| uv sync --locked --extra agent | Passed |
| Playwright Chromium installation check | Passed |
| uv run --extra agent ruff check . | Passed |
| LAB_TEST_BROWSER_USE=1; uv run --extra agent pytest -q | 52 passed, no skips |
| npm.cmd --prefix frontend run build | Passed |
| uv run --extra agent python -m lab.run --transport http | Three CONTROL OK; exit 0 |
| uv run --extra agent python -m lab.run | Three Chromium CONTROL OK; exit 0 |
| Independent snapshots/regrading | All six persisted trial databases matched reports and reproduced grades |
| Browser trace inspection | Three trials contain actual clicks; blind retry contains two Save clicks |
| git diff --check | Passed |

The full suite was rerun after adding the last cleanup regression test; 52 tests
passed. The five review regressions cover failed/canceled provider calls,
escaped-secret redaction, runtime tool rejection and Windows cleanup fallback.
The optional SDK remains installed after this review. No paid model call was made.

Generated local evidence (ignored):

- HTTP: runs/20261026T182826Z_fcb28fe5/report.html
- Chromium: runs/20261026T182834Z_2d79e294/report.html

Both transports preserved normal creation and verification recovery with one
correct new customer/event. Blind retry produced two matching customers/events,
independent business FAIL with exactly duplicate_customer, and CONTROL OK.
Agent tests are mocked; these controls are scripted. Neither is a live model
benchmark result. There was no application, driver or evaluator error in the
six final control trials.

Added docs/BENCHMARK_PLAN.md as a design-only next milestone. It specifies the
four comparison arms, neutral task/policy versioning, paired repeated trials,
checkpoint protocol, run-wide budget admission, metrics/denominators and
acceptance tests. Multi-trial scheduling, checkpoint recovery and aggregation
remain unimplemented. The current task's recovery guidance must not be relabeled
as a neutral basic-agent baseline.

First live Anthropic run still requires an environment-only key, explicit model,
all execution limits and current conservative pricing ceilings, provider-side
spend controls, and separate explicit authorization for paid execution. The exact
command and example budget are documented above and in README/.env.example.
Live authentication, model behavior, billed cost and abnormal-crash isolation
remain unverified. No GitHub push is part of this local commit milestone.
