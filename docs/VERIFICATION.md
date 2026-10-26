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

## Benchmark Engine v1 verification - 27 October 2026

Started from local commit 1a7af3d with a clean working tree. Implemented the v1
engine, metrics/reporting, manifest schema and neutral task/policy separation;
no new dependencies, paid API calls, checkpoint recovery, Git commit or push.
Preserved the optional adapter's tool policy, credentials boundary, budget guard
and independent grading. Existing scripted behavior and evaluator rules remain.

Scripted trials now grade final committed state after the server stops, including
when the driver raises an error. The benchmark wrapper records errors separately
from the independent business outcome. Driver duration is recorded by both
existing runners, and benchmark wall time also includes orchestration/cleanup.

| Check | Actual result |
| --- | --- |
| Ruff across the project | Passed |
| Complete pytest with LAB_TEST_BROWSER_USE=1 and installed optional SDK | 73 passed, no skips |
| Frontend TypeScript/Vite production build | Passed |
| Original HTTP controls | Three CONTROL OK; exit 0 |
| Original Chromium controls | Three CONTROL OK; exit 0 |
| Seeded HTTP benchmark, 3 repetitions x 2 scenarios x 2 strategies | 12 completed isolated trials; exit 0 |
| Seeded Chromium benchmark, 2 repetitions x 2 scenarios x 2 strategies | 8 completed isolated trials; exit 0 |
| Independent regrading of example databases | All 20 snapshots matched raw reports and reproduced the benchmark grades |
| Offline reconstruction of both reports | Passed; no provider configuration or calls |
| HTML loaded in Chromium with network offline and JavaScript disabled | Both rendered; 4 comparison groups and all individual evidence links present; no external requests |
| git diff --check | Passed |

The full available suite was rerun after the final interruption/evidence fixes.
The optional SDK test uses real Chromium but a completely mocked model; it is
not a successful real AI-agent evaluation. Engine fixtures are explicitly labeled
mocked_adapter_test and cannot be relabeled as real trials by an injected executor.
The actual example benchmarks below use scripted controls only.

Engine tests cover canonical seeded pairing/order, immutable output directories,
separate paths for every slot, run-wide budget admission with no refunds after
errors, explicit paid opt-in, neutral/policy task versioning, Wilson reference
values, incomplete token usage and cost subtotals, correct failed/missing-trial
denominators, interruption artifacts, raw error suppression, HTML escaping,
evidence-link containment, missing-evidence labeling and offline-only analysis.
An actual 8-trial HTTP test checks separate SQLite state and unique server PIDs.
A separate interruption test aborts an actual HTTP control and confirms that its
server is stopped. Another driver-failure test commits a customer then raises:
the business grader passes the committed effects while execution still fails.

### Generated examples

Executed with ordering seed 42, no model:

```sh
python -m lab.benchmark --scenario normal lost-confirmation --strategy blind-retry verify --trials 3 --seed 42 --transport http --output runs/benchmark_v1_http_20261027_a
python -m lab.benchmark --scenario normal lost-confirmation --strategy blind-retry verify --trials 2 --seed 42 --transport browser --output runs/benchmark_v1_browser_20261027_a
python -m lab.benchmark --analyze runs/benchmark_v1_http_20261027_a
python -m lab.benchmark --analyze runs/benchmark_v1_browser_20261027_a
```

Commands used the project's .venv/Scripts/python.exe. Ruff and pytest likewise
used that environment; npm.cmd avoids PowerShell's npm.ps1 policy restriction.
The ordinary uv run forms in README target the same project environment.

| Transport | Strategy/scenario | Success | Duplicate-action rate | Median wall seconds |
| --- | --- | --- | --- | --- |
| HTTP | Blind retry / normal | 3/3 | 0/3 | 1.734 |
| HTTP | Verification / normal | 3/3 | 0/3 | 1.734 |
| HTTP | Blind retry / lost confirmation | 0/3 | 3/3 | 2.453 |
| HTTP | Verification / lost confirmation | 3/3 | 0/3 | 2.438 |
| Chromium | Blind retry / normal | 2/2 | 0/2 | 2.851 |
| Chromium | Verification / normal | 2/2 | 0/2 | 3.016 |
| Chromium | Blind retry / lost confirmation | 0/2 | 2/2 | 3.805 |
| Chromium | Verification / lost confirmation | 2/2 | 0/2 | 3.766 |

There were no execution errors or missing evaluations in these 20 trials, so
operational/business success match. Every lost-confirmation blind-retry result
contains exactly duplicate_customer with two matching new customers/events; that
business failure is expected and its scripted control succeeds. Normal/recovery
have one correct new customer/event. Wilson 95% intervals are stored in the JSON
and HTML (for example 3/3 is approximately [43.85%, 100%], 0/3 [0%, 56.15%]).
These small deterministic-control samples demonstrate engine behavior, not agent
generalization or comparative AI capability. Timings are measured and include
fresh browser/server startup where applicable. Model calls, token usage and
estimated/billed model costs are unavailable, not invented zero-cost AI results.

Artifacts (all ignored by Git):

- runs/benchmark_v1_http_20261027_a/report.html
- runs/benchmark_v1_browser_20261027_a/report.html
- manifest.json, summary.json and per-slot trials/trial-NNNNNN/result.json in each
  benchmark directory, plus raw runner results/databases/logs and browser traces
  and screenshots under each slot's evidence/ directory.
- report-preview.png in each benchmark directory confirms offline rendering.
- Original HTTP controls: runs/20261026T184300Z_2b9e9206/report.html
- Original Chromium controls: runs/20261026T184308Z_b91bbb5b/report.html

### Remaining scope and interpretation

The seed makes schedule/order/task data deterministic, not process IDs, ports,
timings or model outputs. V1 is sequential, with no execution resume, parallel
load testing, checkpoint recovery, held-out customer variants or paired bootstrap
comparisons. After an abrupt stop, analyze can reconstruct partial evidence and
unknown unfinished outcomes; it cannot recover unflushed OS/provider state or
turn an interrupted trial into a success. No hard-kill or every browser crash
mode was exhaustively tested. Existing Windows orphan-process and local-only
security limitations remain as documented in README.

Live basic/verification Browser Use benchmark arms are implemented but unverified
with real Anthropic calls. They require environment-only key/model/prices,
existing per-trial limits, explicit total estimated budget, provider-side spend
controls and separate paid authorization. The token/cost accounting preserves
unknown coverage and observed subtotals; upper-rate estimates and reservations
are not invoices or guaranteed billing caps. No checkpoint arm can be selected.

## Final benchmark review, local commit and pilot hold - 27 October 2026

Reviewed all pending engine/runners/metrics/schema/tests/docs before the requested
local commit. Added guards and eight regression cases for invalid model-call
counts and malformed/inconsistent evaluations. False/float/string/negative call
counts cannot turn unknown usage into measured zero. Invalid evaluations are
recorded as evaluator execution errors and excluded from valid business grades.
The independent database evaluator and tool/provider boundaries are unchanged.

Final no-cost verification:

| Check | Result |
| --- | --- |
| Ruff | Passed |
| Complete available suite, including mocked SDK/Chromium smoke | 81 passed, no skips |
| TypeScript/Vite production build | Passed |
| Original HTTP controls | Three CONTROL OK; exit 0 |
| Original Chromium controls | Three CONTROL OK; exit 0 |
| Offline reconstruction of the 12-trial HTTP and 8-trial browser examples | Passed |
| Git credential/output ignore checks | Passed |

Latest original-control evidence:

- runs/20261026T185806Z_271a8bbf/report.html (HTTP)
- runs/20261026T185813Z_0ccac855/report.html (Chromium)

Normal/recovery still pass with one customer/event; blind retry still produces
the expected duplicate_customer failure and a passing control. All agent
interactions in tests are mocked. No paid model call or live trial was executed.

Pilot preparation is recorded in PILOT_READINESS.md. In the inspected execution
environment, the provider, model, key, all limits and prices are absent. The
proposed four-trial envelope has at most 16 calls and 656384 reserved combined
units, subject to prices and token/USD admission; USD 4 is the proposed run-wide
estimated allowance. No actual model or priced cost estimate is configured.
Examples do not authorize spending. Local reservation guards and a worker
deadline cannot guarantee provider billing; account-side controls are unverified.

Only relevant source, schema, tests and documentation are intended for this local
commit; credentials, dependencies and generated evidence stay ignored. No GitHub
push is authorized. Live trials remain on hold until configuration, an actual
priced usage review and separate explicit approval.
