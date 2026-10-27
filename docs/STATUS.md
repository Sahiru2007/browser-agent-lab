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

## Two-trial pilot document revision - 27 October 2026

- PILOT_READINESS.md now proposes exactly one normal and one lost-confirmation
  trial, using only verification-browser-use with identical task wording and
  equivalent initial data. This supersedes the earlier four-trial/$4 proposal.
- Explicit recommendation: claude-haiku-4-5-20251001, an available legacy snapshot
  compatible with the inspected pinned adapter's tool-response path. It has not
  been configured or called. Official pricing/limits were reviewed on this date.
- Proposed admission allowances are $1 per trial/$2 total. Existing call/token
  ceilings permit at most eight calls and 328192 combined reserved units. At
  conservative $2/$5 per-million input/output ceilings, call reservations total
  at most $0.68096 under those bounds; no guaranteed billing cap is claimed.
- Documented caching/tool overhead, the installed SDK's separately reported
  cache-write usage, required environment settings and provider-side controls.
  No usage accounting, dispatch controls, implementation features or credentials
  were changed. Paid execution remains disabled pending explicit approval.

## Approved pilot preflight: blocked on user hold - 27 October 2026

- Approval received for exactly two trials with claude-haiku-4-5-20251001,
  $1/trial and $2 total estimated allowances; subsequently the operator said
  "Keep the pilot blocked for now." No model calls or trials started.
- Preflight found no execution configuration, no ANTHROPIC_API_KEY in execution
  or persistent User/Machine environments, and no .env file. Credentials were
  checked only for presence, never printed or requested in chat.
- Confirmed four model calls per trial/eight across the pilot. Conditional
  reservations are $0.08512/call, $0.34048/trial, $0.68096 combined, within the
  approved $1/$2 estimated allowances. No execution allowance was reserved.
- Plan now uses supported single-scenario commands: normal first, inspect its
  execution/accounting/database outcome, then lost confirmation only if the gate
  passes and the hold is lifted. Each run has a $1 allowance; the two-case ledger
  bounds the pair to $2. No reverse-order combined command will be used.
- Preflight evidence: runs/pilot_preflight_20261026T193033Z/preflight.json.
  Both business outcomes, provider usage and failure triggers remain unexercised.

## Persistent E: storage - 27 October 2026

- Recorded the mandatory E: policy in AGENTS.md and added a reusable PowerShell
  environment helper. User-level model/cache/temp destinations are persisted;
  project-specific runtime selection stays scoped to its shell.
- Copied required browsers and the old uv cache to E:\AI\Caches; retained all
  sources. Retained the old .venv as an identified E: backup and recreated it
  with managed E: Python 3.11.17. Restored locked dependencies offline.
- Copied Node/npm to project .tools on E:; node_modules remains in the project.
  Runtime probes observed uv/Python/Node/Chromium executables and live browser
  profiles/temp files on E:, and actual npm cache writes there.
- Ruff, 81 tests with mocked SDK smoke, frontend build and all six existing
  HTTP/browser controls passed after the environment change. No paid calls.
- Ollama models are configured on E:, but no executable/server was found, so
  server-level storage verification remains unavailable. No model was downloaded.
- Existing C: installations/caches and unrelated processes were left intact.
  Windows system/registry exceptions were explained before installation.
  Full paths, backup locations and evidence are in docs/STORAGE.md.

## Ollama standalone installation - 27 October 2026

- Installed official Ollama 0.40.11 standalone CLI/NVIDIA dependencies under
  E:\AI\Ollama. Archive/extraction stayed in E:\AI\Downloads; verified published
  SHA-256 and valid Ollama Inc. Authenticode signature. Preserved existing models.
- Started hidden PID 30844; API version/tags/ps respond at 127.0.0.1:11434.
  Actual process environment uses E:\AI\OllamaModels and an isolated E: profile,
  temp/cache/log paths. Socket inspection confirms loopback-only listening.
- Cloud access and automatic pruning are disabled. No model pull, inference,
  paid provider call, pilot, autostart service or GitHub push occurred.
- Recommended qwen3:8b-q4_K_M: 5.23 GB artifact download, 16k proposed context,
  estimated 8-10 GiB VRAM and 8-12 GiB host-memory headroom on the observed
  RTX 4070 SUPER 12 GiB / 32 GiB RAM machine. WAITING FOR MODEL CONFIRMATION.
- Project adapter remains Anthropic-only; the SDK's ChatOllama emits unknown
  usage and needs a separate accounting integration before local agent trials.
  Capability compatibility is not a successful local-agent evaluation.
- Full verification, preservation record and model sources: docs/OLLAMA.md.


### Approved local Qwen validation completed - 27 October 2026

- Supersedes prior model-approval wait: downloaded only qwen3:8b-q4_K_M to
  E:\AI\OllamaModels, 5,225,388,164 model bytes; verified all six blob hashes.
- Exact text, JSON-schema and tool-call generation checks PASS separately;
  three sequential local requests, 210 input / 45 output tokens. No tools executed.
- Actual 16384 context / one slot, 37/37 GPU layers, no CPU layer offload.
  GPU allocation 7.02 GiB; whole-device peak 9055 MiB and 100% utilization.
  Peak combined process RSS 1.25 GiB. WDDM per-process VRAM unavailable.
- Cloud disabled and loopback-only server verified. No paid API, browser-agent
  trial, evaluator change or push. Local agent integration remains unimplemented;
  these short native API checks are not browser benchmark results.
- Detailed measurements/limitations: docs/OLLAMA.md and docs/VERIFICATION.md.
  Evidence: runs/ollama_model_validation_20261027/summary.json.


## Local-only Ollama Browser Use adapter - 27 October 2026

- Implemented separate validated local adapter on pinned Browser Use 0.13.11 /
  Ollama SDK 0.6.1; supported ChatOllama options and native usage hooks. No upgrade.
- Exact approved loopback/model digest, 16384 context, concurrency 1, 12 calls,
  300 seconds, 2048 output tokens/call. No cloud fallback, keys or auxiliary paid
  model. Restricted actions and independent DB boundary/paid guards preserved.
- Ruff, 102 tests (including mocked real-SDK/Chromium local path), frontend build,
  all three HTTP and all three browser controls PASS. Blind retry still grades
  duplicate_customer. Observer cleanup warning resolved and retested.
- Ran NORMAL once: business PASS (1 customer/1 event), 12 calls, 77930 input /
  1704 output tokens, 52.938 seconds. Inefficient repeated Save clicks retained.
- After inspecting normal accounting/trace/cleanup, ran LOST CONFIRMATION once:
  business FAIL (duplicate_customer, 2 customers/2 events), 11 calls, 72712 input /
  2023 output tokens, 54.437 seconds. Agent claimed success; DB grader overruled it.
- Native usage complete; provider API charges $0, electricity/hardware unmeasured.
  No real-trial adapter/infrastructure/cleanup errors. No failure reruns or push.
- Trace shows aborted POST at ~697 ms, second POST 201; committed fault marker
  references first customer. Screenshots confirm unconfirmed save before retry.
- Identical neutral task/equivalent initial data; fresh app/browser states per
  trial. Shared Ollama prompt cache affects timing/cached usage; two trials are
  integration evidence, not statistical benchmark or checkpoint recovery.
- Combined evidence: runs/ollama_agent_validation_20261027/summary.json.
  Full paths and limitations: docs/OLLAMA.md and docs/VERIFICATION.md.
  Existing paid pilot remains held; no paid call or independent evaluator change.


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

Final ablation checks: Ruff, 161 tests, all six scripted controls and offline HTML validation pass.


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
