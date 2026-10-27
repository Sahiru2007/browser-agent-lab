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

## Two-trial pilot planning check - 27 October 2026

Documentation-only revision: replaced the four-trial proposal with exactly two
scenarios and a single verification-browser-use policy. Inspected Browser Use
0.13.11, anthropic 1.17.0, installed ChatAnthropic request/usage serialization,
current task wording and existing scheduler/budget guards. No accounting,
dispatch or SDK source was modified.

Reviewed current official Anthropic model, pricing, spend/workspace-limit and
API-credit documentation; direct source links and checked prices are preserved
in PILOT_READINESS.md. Explicitly recommended claude-haiku-4-5-20251001 as an
available legacy snapshot; no model was configured and access remains untested.
The adapter requests cacheable tool/system blocks and reports cache creation
separately from normalized prompt_tokens, so existing token-derived cost summaries
can omit writes. This limitation is disclosed, not silently changed.

No-cost validation checks the proposed command's schedule has exactly two slots,
one for each scenario, both with the same instruction/initial customers. The
canonical scheduler runs lost-confirmation first; the document distinguishes
case enumeration from dispatch order. Checked $1/trial, $2 aggregate admission,
40000 input plus 1024 output reservation per call, four calls per trial: 328192
combined units for both trials. At $2/$5 input/output ceilings, reservations are
$0.08512/call, $0.34048/trial and $0.68096 for both, conditional on the configured
bounds. These are not billing guarantees or actual model usage measurements.

No live command, credentials request, provider account mutation or paid API call
was made. No implementation tests were rerun for documentation-only changes;
the earlier 81-test result is historical. git diff --check and offline plan
validation are the checks for this revision. The recommendation, full required
environment, exact two-trial command and operator checklist are in PILOT_READINESS.md.

## Authorized normal-first pilot: preflight only - 27 October 2026

The operator approved exactly two live trials of claude-haiku-4-5-20251001 with
$1/trial and $2 total estimated allowances, then explicitly requested that the
pilot remain blocked. This approval is retained; execution is on user hold.

Read the current pilot plan, runner scheduling and call-budget code. Checked
nonsecret environment settings and API-key presence without printing credentials.
All required execution settings were absent; AgentConfig validation failed on
missing LAB_AGENT_PROVIDER. The API key was absent in execution/User/Machine
environments and there was no .env file. No provider client or trial was started,
so authentication, model compatibility and live accounting could not be verified.

Before any dispatch, reported that the limit is four model calls per trial,
eight total. At the approved 40000 input/1024 output units per call and $2/$5
per-million price ceilings, estimated reservations are $0.08512/call,
$0.34048/trial, $0.68096 combined. Full trial allowances sum to $2. None was
reserved for actual execution. These guards do not guarantee a billing cap.

PILOT_READINESS.md replaces the combined reverse-order command with supported
single-scenario runs, each using --trials 1 and --max-cost-usd 1: normal first,
manual evidence/accounting gate, lost confirmation second only if eligible.
The same verification policy, model, wording and equivalent initial data apply.
The pair's fixed two-case authorization bounds the total at $2; the engine does
not provide a shared cross-run budget or automatic gate. No reruns or limit
increases are authorized.

Ignored preflight artifact: runs/pilot_preflight_20261026T193033Z/preflight.json.
It is labeled pilot_preflight_not_trial_results, with zero live trials started
and zero model calls dispatched. Both cases are not_started; database evaluations
and provider usage are null, and failure triggers are not_exercised. No actual
cost, successful business outcome or failure-trigger behavior is claimed.

No source code, accounting/dispatch control, credential or provider account was
changed. No trial, retry, paid API call, commit or GitHub push was performed.
Only offline plan/documentation checks apply to this preflight. The remaining
blockers are private environment configuration and the operator lifting the hold;
the two-trial approval itself need not be requested again within its stated limits.

## E: storage enforcement and runtime verification - 27 October 2026

Inspected actual tool/cache paths and running processes before downloading. The
old Playwright store (718 MiB) and npm cache (1059.4 MiB) were on C:; the venv's
base Python was C: despite its E: prefix. The existing uv cache was E:\AI\Cache\uv.
Explained the proposed copies, retained venv backup and Windows exceptions before
changing installations. No C: source installation/cache was deleted or moved.

Persisted E: user-level paths and added scripts/use-e-storage.ps1 for repeatable
project process setup. The first attempt was blocked by PowerShell execution
policy; only process-scoped RemoteSigned was used afterward. Permanent execution
policy was not changed. Playwright's dry-run then confirmed all browser/download
install targets on E:. Copied required browser assets and uv cache without
removing originals. Managed CPython 3.11.17 downloaded its 23.9 MiB archive to
E:\AI\Downloads\uv-python and installed in E:\AI\Python. Restored all 118 locked
packages offline into a new project .venv, after retaining the old one at
E:\AI\Caches\backups\browser-agent-lab-venv-before-e-storage-20261027.

Runtime evidence: runs/storage_verification_20261027/runtime-paths.json and
browser.png. Actual running uv, uv-launched Python, Node, Playwright's Node driver
and Chromium image paths were observed on E:. Python's base runtime was E:, not
C:. Live browser profile arguments and actual Python/Node temp files were on E:.
npm wrote and verified local tarball content in E:\AI\Caches\npm\_cacache; logs
were also on E:. The directory cache-add probe failed with an npm packing error;
the offline local-tarball probe succeeded. No registry package download was needed.

Worker environment tests also verify inherited nonsecret cache/temp settings,
while preserving exclusion of DB/fault settings and unrelated provider keys.

| Migrated-environment check | Actual result |
| --- | --- |
| Offline locked dependency restore with optional SDK | Passed; 118 packages |
| Ruff | Passed |
| Full suite with mocked SDK/Chromium smoke | 81 passed |
| Frontend production build, E: Node/npm | Passed |
| HTTP controls | Three CONTROL OK |
| Chromium controls from E: browser store | Three CONTROL OK |

Control evidence: runs/20261027T094818Z_c3b0a20d/report.html (HTTP) and
runs/20261027T094824Z_e51e97df/report.html (Chromium). Blind retry remains the
intentional duplicate_customer business failure. No paid model call occurred;
the live pilot remains on user hold.

Persistent OLLAMA_MODELS points to E:\AI\OllamaModels, and a child inherited it,
but no Ollama executable/process/service/responding local server was found.
Do not claim actual Ollama server storage verification. Existing identity/config
files were not opened or moved. No Ollama or model installation/download occurred.
Windows/system DLLs, registry settings, machine-service temp and existing unrelated
C: applications remain exceptions; no system installer was run in this task.
See STORAGE.md for the complete effective-path map and preservation record.

## Ollama standalone installation verification - 27 October 2026

Read AGENTS.md/STORAGE.md and loaded the E: helper first. Checked PATH, standard
directories, uninstall registry, processes/services and port 11434: no existing
Ollama executable/server/listener found. Existing E: model directories were
retained; their before/after file inventories are identical (zero files).

Reviewed official Windows standalone instructions and the current release.
Downloaded only official ollama-windows-amd64.zip v0.40.11, 1586356606 bytes, to
E:\AI\Downloads. Verified SHA-256
bda4a493ba8a7c24d57263cd843cd68cee84f44aed4299eeed532acad7eda12a.
Extracted under Downloads and copied 75 files / 2231045135 bytes to E:\AI\Ollama.
Executable signature: Valid, Ollama Inc. Explained existing Windows/NVIDIA C:
components before installation; no system component, driver or GUI installer
was installed. No previous installation, cache, identity or model was removed.

Started the hidden standalone server using scripts/start-local-ollama.py.
Verification from a separate process after the starter exited:

| Check | Actual result |
| --- | --- |
| Running image/PID | E:\AI\Ollama\ollama.exe, PID 30844 |
| CLI and GET /api/version | 0.40.11 |
| Actual listening sockets | Only 127.0.0.1:11434; no wildcard/LAN listener |
| Actual server OLLAMA_MODELS | E:\AI\OllamaModels |
| Cloud / pruning | OLLAMA_NO_CLOUD=1 / OLLAMA_NOPRUNE=1 |
| Profile/config/temp/cache/log roots | E:; inspected server environment |
| GET /api/tags and /api/ps | Passed; zero installed and zero loaded models |
| Existing model-file preservation | Before/after inventory unchanged |
| Startup helper lint | Ruff passed |

No pull/run/chat/generate request was made. A small public registry manifest was
read to recommend qwen3:8b-q4_K_M; no weight blobs were fetched. Official artifact
sum: 5225388164 bytes. Memory estimate at 16384 context: 4.87 GiB weights plus
2.25 GiB FP16 KV plus runtime buffers, approximately 8-10 GiB VRAM and 8-12 GiB
host-memory headroom. This is an estimate, not an observed model allocation.
NVIDIA SMI reported 12282 MiB total VRAM, 10343 then 10103 MiB free; RAM is about
32 GiB total with 12.7-13 GiB available. WMI's 4 GiB AdapterRAM field was not used
as the GPU capacity because NVIDIA SMI supplies the actual dedicated memory.

Inspected installed Browser Use 0.13.11/ChatOllama and project provider guards:
SDK supports JSON-schema formatting but returns usage=None; project adapter
accepts Anthropic only. No compatibility, inference quality or local-agent
benchmark success is claimed. Local-provider/usage integration remains separate.

Evidence: runs/ollama_install_20261027/installation.json and
server-verification.json, plus models-before.json and proposed-model-manifest.json.
Server startup/log paths and the exact proposed model are in OLLAMA.md. No paid
call, pilot or push occurred. Stop before model download until confirmation.


## Approved local model validation - 27 October 2026

The operator subsequently approved downloading only **qwen3:8b-q4_K_M**.
This section supersedes the earlier pending-approval statements above.
Loaded scripts/use-e-storage.ps1 before download/execution. Pulled this tag only;
Ollama lists exactly one model. All six stored blobs passed independent SHA-256
checks against their filenames. Existing installations/model files were preserved.

- Model digest: `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Actual model artifact size from /api/tags: **5,225,388,164 bytes** (4.87 GiB),
  Q4_K_M. Sum of logical file lengths under E:\AI\OllamaModels immediately after
  pull: **5,225,396,472 bytes**, including manifests/metadata; not allocated disk clusters.
- Actual running server PID 30844 uses E:\AI\Ollama\ollama.exe and E: model,
  temp and CUDA-cache paths. Runner PID 6000 executable/dependencies also on E:.
  Cloud disabled; server still listens only on 127.0.0.1:11434.

Three separate sequential native /api/chat requests used think=false,
num_ctx=16384, temperature=0, seed=42 and output caps 64/128/128 respectively.
No generated tool was executed; no browser-agent trial or paid call occurred.

| Check | Result | Wall seconds | Input/output tokens |
| --- | --- | ---: | ---: |
| Plain inference | PASS: exact LOCAL_OK | 68.063 | 22 / 3 |
| JSON schema | PASS: exact synthetic name/email object | 0.391 | 34 / 20 |
| Tool generation | PASS: lookup_customer(email=alice@example.test) | 0.312 | 154 / 22 |

Native counters total **210 input / 45 output tokens** across three calls;
JSON/tool responses report 3/1 cached input tokens respectively (4 cached total).
Cold first request included 34.063 seconds reported model-load time. These tiny
checks establish capability, not sustained throughput or browser-task reliability.

Measured context allocation was **16384**, one slot/request (API ps, CLI ps and
runner logs agree). CLI reports **100% GPU**; logs confirm **37/37 layers on GPU**,
CUDA model buffer 4643.78 MiB and CUDA FP16 KV buffer 2304 MiB. API reports
**7,536,965,058 bytes (7.02 GiB) GPU model allocation**. No CPU layer offload was
observed. Host model/compute buffers remain (333.84 / 96.04 MiB), so GPU placement
does not mean zero CPU work or host memory.

One-second NVIDIA samples: whole-device VRAM 1660 MiB before load, peak
**9055 MiB** (7395 MiB increase), 2945 MiB free at peak; GPU utilization reached
**100%**. These totals include unrelated desktop processes. Windows WDDM reports
per-process GPU memory as N/A; precise NVIDIA per-process attribution unavailable.
Combined Ollama/runner peak sampled RSS **1,337,303,040 bytes (1.25 GiB)**;
system available RAM fell from 15,566,172,160 to minimum 14,322,167,808 bytes.
RSS and device memory are separate measurements, not additive exclusive usage.

The log briefly says `llm server error` while waiting for runner startup, then
initializes and serves all three requests successfully; no request errored and no
retry was issued. A context-below-training-capacity notice is expected (16k vs
40960). These tests allocate a 16k context but use short prompts; they do not test
16k-token prompt quality, long sessions, concurrent load, or Browser Use integration.
The Anthropic-only adapter and ChatOllama unknown-usage limitation remain unchanged.

Evidence: `runs/ollama_model_validation_20261027/summary.json`, `results.json`,
`tags.json`, `show.json`, `disk-files.json`, `blob-verification.json`,
`pull.jsonl`, separate text/json/tool request and response JSON, `ps-*.json`,
`hardware-samples.json`, `server.json`, `compute-apps.json`, and `runtime-log.txt`.
These ignored E: artifacts contain synthetic local tests, not benchmark results.
API fields follow the [official chat API](https://docs.ollama.com/api/chat) and
[loaded-model API](https://docs.ollama.com/api/ps).


## Local-only Browser Use adapter - 27 October 2026

Implemented separate OllamaConfig/OllamaAdapter and LocalModel around the installed,
unchanged Browser Use 0.13.11 ChatOllama (Ollama Python SDK 0.6.1). Inspected installed
SDK plus [official supported models](https://docs.browser-use.com/open-source/supported-models)
and [official Ollama example/source](https://github.com/browser-use/browser-use/blob/main/examples/models/ollama.py).
SDK host, ollama_options and client_params APIs are used; native HTTP response hooks
recover usage which this pinned ChatOllama otherwise discards. No dependency upgrades.

Configuration: exact http://127.0.0.1:11434, qwen3:8b-q4_K_M; digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41;
16384 context, one request, <=12 model calls/12 model steps, <=300 seconds,
<=2048 output tokens/call, think=false, temperature=0, seed=42. Maximum configured
output capacity is 24576 tokens/trial. Each CLI invocation is one trial; no retries.
The five-minute worker deadline includes setup; bounded cleanup adds wall time.

Local endpoint/model validation, actual server loopback/cloud/concurrency/model
storage preflight, disabled proxy/redirect inheritance, and credential-free local
worker environment prevent configured cloud fallback. Existing browser-action allowlist,
CRM-only domain restriction, no JS/shell/files/upload/extract tools and disabled
telemetry/dotenv/cloud sync/judging/planning/compaction are preserved. The extraction
LLM slot references the same bounded local model but its action is absent; no auxiliary
model is enabled. The worker receives only AgentRequest URL/instruction and model
settings, never task assertions, seed data, faults or database/reset/grading access.
Existing paid credentials, USD reservations and stop-on-unknown-usage guards are unchanged.

Local usage is measured from actual native counters or explicitly unavailable;
missing usage does not require monetary pricing or stop otherwise bounded local
inference. Native counts survive SDK schema errors. Model/action response failures
are distinguished from provider transport, startup, trace/cleanup and evaluator errors.
Provider API charges are zero; electricity/hardware costs are unmeasured, not zero.
Evidence includes sanitized action history, actual model responses, screenshots,
Playwright observer trace/network and original result/database. Raw provider error
strings, profiles and SDK logs are not copied into reports.

Verification completed with E: storage helper loaded:

- Ruff passed; complete test suite: **102 passed**, LAB_TEST_BROWSER_USE=1.
  Includes mocked native usage (known/unavailable), call/time/output configuration,
  loopback-only dispatch, concurrency serialization, paid/local separation,
  timeout cleanup and real SDK+Chromium with mocked Ollama HTTP. Mocked success
  claims still fail independent grading when no customer exists.
- Frontend production build passed.
- All three HTTP controls and all three Chromium controls passed. Blind retry
  retains its intentional duplicate_customer business failure.
- Mocked trace-observer smoke initially exposed a Windows asynchronous pipe
  finalization warning. Explicit observer close and driver cleanup resolved it;
  clean smoke rerun passed with no remaining test browser process. Cleanup is bounded.
- Exactly **two real local-agent trials**, NORMAL first, inspected before LOST
  CONFIRMATION. No model-task reruns, paid API calls, evaluator changes or push.

| Real local trial | Independent business grade | Calls | Input/output tokens | Cached input | Wall seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| Normal | PASS: 1 correct customer, 1 event | 12 | 77930 / 1704 | 63752 | 52.938 |
| Lost confirmation | FAIL: duplicate_customer; 2 customers, 2 events | 11 | 72712 / 2023 | 64467 | 54.437 |

Both agents claimed success. Neither claim affected the independent DB grade.
All 23 native call records have measured usage; total **150642 input / 3727 output**
tokens (128219 cached input tokens, a subset of input). Provider API charges: $0.
NORMAL driver duration 51.625 seconds; LOST driver duration 53.125 seconds.
No adapter, accounting, infrastructure or cleanup error in either real trial.
NORMAL uses 13 history entries including automatic URL navigation, but only 12
model calls. It repeatedly clicked Save after successful creation; trace network
has just one successful POST (17 ms), so this inefficiency did not duplicate data.

LOST trace has initial POST status -1 (aborted) at 696.583 ms, followed by another
POST returning 201 at 12.264 ms. Inspected step-05.png shows the unconfirmed-save
message with the original form still populated. Instead of searching before retry,
the model clicked Save again, then later clicked the visible customer and claimed
success. The committed fault marker refers to customer 3, alongside its creation
event; duplicate is customer 4. Existing app code commits customer/event/fault in
one transaction, then delays response 2 seconds; UI abort is 700 ms. Together the
DB, screenshot, code and network evidence confirm post-commit lost confirmation.
This is a **model task failure**, not a laboratory execution error.

Both trials used identical neutral version 1.1.0 task wording with no recovery
prescription or fault disclosure, equal initial DB snapshots, distinct trial.db
files, CRM ports (52228/54569), browser processes/profiles/contexts and server
processes. Actual listener/process inspection after each confirmed no trial CRM,
worker or browser remained. The long-lived local Ollama server/model remains
shared, including prompt cache; cached first-call tokens in LOST reflect this.
These two observations are not a statistical success-rate benchmark. Context
allocation is verified, not full-context reasoning or long-session reliability.
No OS security sandbox/network firewall is claimed; trusted SDK runs as the user.
A hard worker kill can leave trace/final-message evidence incomplete; progress and
committed DB grade remain available. Multi-trial local-provider benchmark CLI
support and checkpoint recovery are not implemented.

Commands (single-trial, do not rerun merely to change the observed result):

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.agent_run --adapter ollama --scenario normal
uv run --offline --extra agent python -m lab.agent_run --adapter ollama --scenario lost-confirmation
```

Evidence (all ignored on E:):

- Combined inspection: runs/ollama_agent_validation_20261027/summary.json.
- NORMAL: runs/agent_20261027T104036Z_f677e01c/result.json.
- LOST: runs/agent_20261027T104235Z_60a31f72/result.json.
- Each trial retains trial.db, server.log, inspection.json and browser-evidence/
  containing browser-history.json, trace.zip, step images and model-response-*.json.
- HTTP controls: runs/20261027T103834Z_3fadc81e/report.html.
- Chromium controls: runs/20261027T103840Z_5be102ed/report.html.

The paid Anthropic pilot remains on hold. No new model weights were downloaded.


## Completed exploratory local recovery comparison - 27 October 2026

Exactly 12 local-agent trials completed: 2 frozen configurations x 2 conditions x
3 matched starting-data seeds. Normal: baseline 3/3 and verification 3/3 business
passes, no duplicates. Lost confirmation: both 0/3 passes and 3/3 duplicates.
All agents explicitly finished; 10/12 did so at the 12-call ceiling (SDK's final
step is done-only); no blocked-limit, timeout, infrastructure or accounting error.
Wilson 95% intervals are [43.9%,100%] for 3/3 and [0%,56.1%] for 0/3.
This small comparison does not demonstrate reliability or a recovery improvement.

Recorded full instruction/configuration hashes, seeded balanced ordering, shared
Ollama cache conditions, native usage, independent grades and all trial evidence.
135 calls: 895134 input / 23427 output tokens; provider API charges $0, local
hardware/electricity unmeasured. All native counts and DB grades audited; original
trials remain byte-for-byte unchanged. Added operator-side per-task initial-data
seeding and a fixed local comparison harness, with no grader/dependency changes.
Ruff, 117 tests (mocked SDK smokes enabled) and all six scripted controls pass.

Full protocol, diagnosis, counts/uncertainty, implementation changes and limitations:
[LOCAL_RECOVERY_COMPARISON.md](LOCAL_RECOVERY_COMPARISON.md).
Offline report: runs/local_recovery_comparison_20261027/report.html; immutable
manifest, summary and audit alongside it. No replacement/rerun, paid calls or push.
Checkpoint recovery and broad reliability claims remain out of scope.

Post-run report-only fix: malformed evaluator records now retain a partial report
and stop without replacement; explicit report-kind labels distinguish mocked
fixtures. Frozen execution source/hash is preserved alongside
postrun-report-fix.json. No real trial or grader was modified and no extra
inference occurred. See LOCAL_RECOVERY_COMPARISON.md for the separate fix record.

Final offline Chromium report check: four comparison groups, 12 trial entries,
all local evidence links exist, zero HTTP/HTTPS requests. Receipt and preview:
runs/local_recovery_comparison_20261027/report-browser-check.json and
report-preview.png. Final Ruff and complete suite: 117 passed. Original hashes
were rechecked after the report-only fix and remain identical.


## Experimental uncertain-write guard - 27 October 2026

Separate GuardConfig/OllamaGuardAdapter now gates browser-context POST requests
before dispatch and requires a fresh read plus one matching visible name/email/
company row before resolving success. No DB/fault/grader input enters guard
recovery decisions. Baseline/verification configurations and all old evidence
are unchanged; no application idempotency/uniqueness constraint was introduced.
Supported scope is this synthetic CRM's same-context HTTP flow, not arbitrary
sites/service workers. Enforcement was verified with actual Chromium/CDP click
and Enter repeats, rejection/correction, uncertain writes, visible reconciliation,
unresolved stops and independent grading, plus mocked pinned-SDK model responses.

Exactly four authorized real local trials completed once (normal/lost confirmation
x seeds 101/202): all four independent DB grades pass with one customer/event,
zero duplicates. Only the two normal cases reached visible confirmation; both
lost cases stopped explicitly unresolved, so autonomous recovery is NOT proven.
No live retry requests were attempted or network-blocked. Guard intercepted two
unresolved done actions; one was already unsuccessful and one positive claim was
overridden. These are distinct intervention counts, not two blocked retries.
45 calls; 302591 input / 7979 output tokens. No infrastructure/accounting/cleanup
errors. Ruff, 137 tests and all six existing scripted controls pass. No paid call,
upgrade, grader change or push. Provider API charges $0; energy/hardware unmeasured.

Rule specified before implementation, actual feasibility limits and detailed
results: [RECOVERY_GUARD.md](RECOVERY_GUARD.md). Offline report:
runs/recovery_guard_20261027/report.html, with manifest, audit, frozen execution
sources and per-trial guard event logs. Post-run changes were report-only
intervention-count enrichment; original results remain unchanged.


## Evidence-only unresolved-trial diagnosis - 27 October 2026

See [GUARD_DIAGNOSIS.md](GUARD_DIAGNOSIS.md) for timestamped seed-101/202 timelines,
12-call allocation, actual network results, visible-detail findings and explicit
boundary coverage. Both unresolved agents performed zero post-submission reads;
eight/nine calls looped on scroll/find_text. No correct fresh row was rejected.
No reconciliation defect explains the failures; limits and matching stay intact.
Only a reporting defect was corrected for future runs: unresolved text now says
writes remain prohibited instead of implying that requests were actually blocked.
Original results/words/event logs/frozen configurations are unchanged.

The case study still has four passing DB outcomes, two confirmed/two unresolved
workflows, zero live retry blocks and one positive completion claim overridden.
A new scripted negative test demonstrates other-context bypass and an intentionally
failing duplicate grade; it is not a real-agent trial. Routed unsupported paths
are tested as blocked; service-worker traffic and other contexts are not universally
protected. No new model calls, new guard features, relaxed rule or grader changes.
A feedback-only four-slot follow-up is proposed, not executed or authorized here.

Checkpoint checks passed: Ruff, 145 tests (optional SDK mocked-provider smoke
included), frontend build, three HTTP and three browser controls. New negative
other-context test intentionally demonstrates a duplicate outside the installed
route's scope and is not part of real-agent statistics. Current control reports:
runs/20261027T122546Z_6f4ba107/report.html and
runs/20261027T122552Z_d442d432/report.html. No new model calls.


## Completed fresh feedback ablation - 27 October 2026

The user-authorized follow-up used lost-confirmation seeds 101/202 for both A
(commit-aeba563 feedback) and B (same text plus the supplied clarification).
This superseded the earlier proposed normal/lost design. Four fresh attempts,
balanced seeded order B/101, A/101, A/202, B/202; no historical substitutions.
A and B each reconciled 1/2 and remained unresolved 1/2, on opposite seeds.
All four DB grades pass with one customer/event and zero duplicates. Fresh reads
and complete visible name/email/company evidence coincided only in the confirmed
cases; GET alone was not counted as reconciliation. All used 12 calls and final
allowed done; no hard timeout. Zero live retry blocks, two unsuccessful unresolved
done interceptions, zero positive claims overridden. 48 calls; 332904 input /
9629 output tokens. No infrastructure/accounting/cleanup failure or replacement.
No aggregate improvement established; two seeds/shared cache/model nondeterminism
preclude reliability or isolated timing claims. No guard/grader/limit/dependency
change, paid call, commit or push. Prior case-study evidence remains unchanged.

Exact texts/configuration hashes, per-trial mechanism/results, claims, interventions,
usage and limitations: [FEEDBACK_ABLATION.md](FEEDBACK_ABLATION.md).
Offline report: runs/feedback_ablation_20261027/report.html; manifest and audit
alongside it. Additional inference is not authorized by this documentation.


Final verification: Ruff passed; full suite **161 passed** with mocked-provider
SDK/browser smokes enabled; all three HTTP and all three Chromium scripted
controls passed. Controls are not included in these four real-agent statistics.
Current control evidence: runs/20261027T141335Z_2f42740d/report.html (HTTP),
runs/20261027T141341Z_d6f23c10/report.html (Chromium). Offline HTML checked in
Chromium: four rows, valid local links, no external requests; receipt and preview
are report-browser-check.json and report-preview.png in the ablation directory.
Final source, exact-text/manifest and prior-artifact hashes were rechecked.


## Customer-editing milestone - 27 October 2026

Implemented labeled customer details and company/email editing; similar-name
customers are selected by business email. Added customer.change_company and
customer.change_email v1.0.0 operator-owned tasks, atomic customer.updated audit,
and independent task-dispatched edit grading. Creation evaluator function and
customer.created format are unchanged. No-op saves are event-free and cannot
satisfy a requested nontrivial change. Architecture/contracts: ARCHITECTURE.md,
TASKS.md. No new edit fault type, AI trial, dependency upgrade or recovery setting
change was made. Prior feedback-ablation work was preserved.

Actual verification:
- Ruff passed; full suite 190 passed with LAB_TEST_BROWSER_USE=1 (SDK interactions
  mocked, real Chromium). Focused edit/app/creation-grading suite: 42 passed.
- TypeScript/Vite production build passed.
- All three HTTP and three Chromium creation controls passed: normal and verified
  lost confirmation have one customer/event; blind retry has two and is correctly
  rejected with duplicate_customer (intentional business failure).
- Both new Chromium editing controls passed, selecting by email among similar
  names, saving only the requested field, no-op saving and reopening details.
  Saved databases independently regraded identically after server shutdown:
  stable identities, zero created/deleted customers, one truthful edit event each.
- Negative cases reject wrong similar-name customer, additional field changes,
  replacement records (including recreation audit at the same ID), missing or
  incorrect/extra audit, success claims without effects, and reverted extra edits.
  API validation/404/no-op semantics and audit-failure transaction rollback pass.
- Trace inspection confirms browser fill/click actions, fresh detail GETs and two
  PATCH 200 responses per edit control (actual change then no-op). All 1,174
  inventoried historical evidence files retain their SHA256 hashes. Original
  creation evaluator AST is unchanged. Generated evidence remains Git-ignored.

Reports (relative to project root):
- HTTP: runs/20261027T144011Z_8e1c885d/report.html
- Original browser: runs/20261027T144017Z_dad839ad/report.html
- Editing: runs/edit_controls_final_20261027/report.html and summary.json
- Per edit: company/ and email/ contain result.json, trial.db,
  browser-evidence/trace.zip, saved.png and reopened.png (screenshots inside
  browser-evidence/).
- Preservation/trace audit: runs/edit_preservation_20261027/verification-receipt.json
  and historical-files.json.

Limitations: scripted editing evidence only; agent and benchmark CLI selectors
remain creation-only. No edit-specific uncertainty/recovery tests, authentication,
email uniqueness or concurrent-edit conflict handling. Experimental guard remains
creation-specific, not a supported edit guard. No paid calls, commit or push.


## Exploratory real local editing pilot - 27 October 2026

Editing implementation checkpoint: 282611712cb1f43eb7466459f70a48746d0d613a.
Unrelated feedback-ablation work was left uncommitted. Minimal follow-on task
selection (--task company|email, normal only) and fixed lab.edit_pilot orchestration
reuse the existing runner/unguarded local adapter/evaluator; no edit recovery.

Exactly six authorized fresh attempts completed, three matched seeds per task,
with frozen Qwen digest, baseline, tools, 16384 context, 2048 output/call,
12-call ceiling, 300 s timeout and concurrency one. No faults or instruction tuning.
All six independently regraded databases pass: intended customer edited, requested
value committed, unrequested fields/other records/identities preserved, one exact
update event, no customer creation/deletion. Actual traces confirm correct first
detail read and substantive write targets. No infrastructure/accounting/cleanup
error and no replacement attempt. All 1232 pre-pilot evidence files unchanged.

All six explicit done at the call ceiling; 3 true and 3 false success claims.
Model/action failure flags in 3 cases are distinct from laboratory errors.
37 extra empty no-op saves; company/101 also read the other record during later
verification without editing it. Six DB passes do not imply reliable/efficient
agent workflows. Measured totals: 72 calls, 496350 input / 13602 output tokens,
424545 cached input tokens, 444.563 s summed duration; API charges $0,
hardware/electricity unmeasured. Shared cache/hardware and brief regression-suite
overlap with the first trial prevent timing-isolation claims. No paid call,
dependency upgrade, recovery/grader change or push.

Full per-trial results, claims, limits and caveats: [EDITING_PILOT.md](EDITING_PILOT.md).
Offline report: runs/editing_pilot_20261027/report.html. Frozen manifest/state,
independent-audit.json, preservation.json and per-trial JSON/DB/history/traces/native
model responses are retained alongside it. This is exploratory (three seeds/task),
not a reliability benchmark. No further inference authorized by documentation.


Post-pilot verification passed: Ruff, full suite **197 passed** with mocked-provider
SDK/real-Chromium smokes enabled, TypeScript/Vite build, all three HTTP and all
three original browser controls, and both editing browser controls with saved-DB
regrading. Blind retry still fails intentionally with duplicate_customer.
New tests cover matched task seeds, both edit CLI selectors, fault rejection before
dispatch, independent regrading regardless of success claims, stale-grade rejection
and an offline unstarted-slot report. They do not count as real agent observations.
Control reports: runs/20261027T154442Z_57a819b8/report.html (HTTP),
runs/20261027T154448Z_57c97268/report.html (browser),
runs/edit_pilot_post_controls_20261027/report.html (edits).
Pilot HTML verified in Chromium: six trial rows, 21 valid local evidence links,
zero external requests; report-browser-check.json and report-preview.png retained.
Editing checkpoint is committed; subsequent minimal dispatch/pilot/report changes
remain uncommitted. Earlier unrelated feedback work remains intact. No push.


## First portfolio release candidate - 27 October 2026

The prior pilot/feedback work was already committed as 660f089 and the editing
implementation as 2826117; there were no uncommitted pilot changes at RC start.
New RC scope is documentation consolidation plus a standard-library, read-only
retained-evidence summarizer. No app feature, trial, grade, limit, frozen task or
configuration changed. README now provides purpose/architecture, reproducible
setup/control commands, sample sizes, supported workflows/faults and caveats.
[CASE_STUDY.md](CASE_STUDY.md) consolidates creation/recovery/feedback/editing;
[DEMO.md](DEMO.md) provides a model-free walkthrough.

Response interpretation is corrected explicitly: the two company agents acknowledge
successful edits but report missing verification confirmation; email/202 explicitly
and incorrectly denies its saved edit. Three false Boolean flags are not three
false-negative factual claims. All six final responses exist. All six business
grades remain PASS. Efficiency: 37 no-op saves, 72 calls and 444.563 s total;
10 steps/trial (60 total) start after successful edit responses, a conservative
operator-hindsight post-commit count. Exact commit/dispatch timestamps, optimal
call counts and isolated inference/energy costs remain unavailable. Every trial's
call-3 state message includes Changes saved.; visible input does not establish
model comprehension. No recovery or reliability conclusion is added.

Newly executed RC checks: Ruff; 46 focused editing/pilot/creation-grading tests;
read-only summarizer on all six retained histories/traces/native responses,
including action alignment with SDK defaults and a mismatched-action rejection
check; command --help checks for controls, edit controls, agent runner and benchmark;
24 tracked documentation links; four historical offline HTML reports and their
local links loaded in Chromium, zero external requests/errors. All 1497 historical
file hashes remain unchanged. No install/download or dependency change was needed.
The recorded earlier full suite (197 tests), frontend build, six original controls
and two editing controls were NOT rerun for this documentation/analysis-only RC.
Their previous results remain valid historical verification, not new RC execution.

A separate manual demo server is running at http://127.0.0.1:8000 (PID 14512 at audit),
with database/logs in runs/portfolio_rc_20261027, never a historical trial DB.
Loopback health and read-only search/details verified in Chromium; actual process
executable and TEMP are on E:. No unrelated process stopped. This is a manual
application demo, not a new agent observation. Runtime availability is session-local.
Receipts: runs/portfolio_rc_20261027/review-checks.json, editing-efficiency.json,
historical-hashes.json, demo-server.json and demo-preview.png (all Git-ignored).

Sharing requirements: the release-candidate commit is local/unpushed; repository
access and a later authorized push are needed for a remote reviewer. Raw runs are
excluded; arrange local review or a separately reviewed/redacted evidence export
for trace-level independent inspection. A clone can review methods/results and
run scripted controls without model calls. Windows/E: policy is verified; other
platforms require storage/tooling adaptation. No live execution is authorized by
the documentation. No paid calls, publication, visibility change or push.


## Private GitHub upload and CI repair - 27 October 2026

GitHub CLI authenticated as Sahiru2007; existing browser-agent-lab repository
confirmed PRIVATE. main was one commit ahead (fc2e3f9), with no remote divergence.
All 66 tracked files were audited: no real credentials, databases, raw runs,
installed dependencies or private machine configuration. Documented .env.example,
synthetic lab:lab example credentials and intentional E: policy paths are retained.

The preceding GitHub Actions run 40535877115 failed with three base-environment
test errors: two mocked CLI tests depended on the developer's frontend/dist;
one evidence-only test imported optional psutil despite mocking its process calls.
Fixed the tests with an isolated build sentinel and a stand-in process module.
No application, grader, recovery configuration or live experiment changed.
Removed Actions upload-artifact over runs/ so raw traces/databases are not uploaded.
No provider secrets or paid/live agent dispatch are configured in CI.

Local targeted verification: 19 tests passed, Ruff and diff checks passed. Actual
Linux base-environment validation is the Checks run attached to the uploaded
commit; inspect GitHub for its conclusion. RC fc2e3f9 remains in preserved history.
No force push, release, visibility change, reviewer invitation or raw evidence upload.


## GitHub presentation refresh - 27 October 2026

README rewritten for technical readers: concrete lost confirmation, implemented
workflows/stack, architecture, setup/commands, separate controls/mocks/real-agent
findings, local Ollama requirements, repository map, caveats and explicitly planned
roadmap. Business grades and all frozen evidence/configurations remain unchanged.
Four real Playwright page captures were visually reviewed and added to docs/assets:
customer directory, details/editing panel, cropped recovery comparison and cropped
guard report showing confirmed versus unresolved workflows. Sources/crop scope are
recorded in docs/assets/README.md. No credentials, personal data, machine paths or
desktop content are in the images. No raw DBs/traces/runs are included.

Capture used a separate fresh synthetic DB/server on an unused loopback port;
that temporary server was stopped. All local captures/temp/receipts remained on E:.
No install, dependency upgrade, app behavior change or model call. Current measured
findings and company-verification versus explicit email-failure interpretation are
preserved. The README explicitly distinguishes recorded local 197-pass opt-in SDK
verification from GitHub 174 passed/23 skipped at 09fc442: optional SDK dependencies,
opt-in Chromium/SDK tests and Windows-only cleanup explain the skipped coverage.

Metadata updated to the reliability-laboratory description and six relevant topics;
repository reconfirmed PRIVATE, homepage blank. No release, invitations, license or
access changes. New verification: local Markdown/image links and fragment, PNG
metadata/dimensions, visual review, historical SHA256 preservation and diff hygiene.
Detailed capture/check receipts are local under runs/github_presentation_20261027.
The previous full suites/control outcomes are recorded findings, not newly run
agent experiments for this presentation. Normal Git push and authenticated GitHub
README/image verification follow; the corresponding Actions run records current CI.


Post-push presentation review: authenticated GitHub-rendered README HTML was
inspected in Chromium with all four byte-verified GitHub PNGs cached locally;
25 repository-relative rendered link/image targets exist. Full signed-in GitHub
site UI was not used. Image readability and synthetic-only content were visually
checked. A punctuation-encoding defect discovered in the first rendered preview
was corrected with plain ASCII punctuation; no image, result or app behavior changed.
Historical file hashes remain identical. All downloaded HTML/images/previews and
verification receipts are under E: runs/github_presentation_20261027, Git-ignored.
