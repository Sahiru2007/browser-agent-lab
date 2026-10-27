# Ollama standalone installation - 27 October 2026

Current status: approved qwen3:8b-q4_K_M downloaded and validated; local Browser Use
adapter implemented. One normal trial passed independent grading; one lost-confirmation
trial failed with duplicate_customer. No paid calls or retries. Earlier installation
observations below are historical; current adapter/results are at the end.

## Installation and storage

- Release: v0.40.11, published 24 October 2026.
- Source: https://github.com/ollama/ollama/releases/tag/v0.40.11
- Archive: E:\AI\Downloads\ollama-v0.40.11-windows-amd64.zip
- Archive bytes: 1586356606 (about 1.59 GB / 1.48 GiB).
- SHA-256: bda4a493ba8a7c24d57263cd843cd68cee84f44aed4299eeed532acad7eda12a
- Extraction: E:\AI\Downloads\ollama-v0.40.11-extracted
- Installation: E:\AI\Ollama; 75 files, 2231045135 bytes.
- Model storage: E:\AI\OllamaModels.
- Server-only profile/config: E:\AI\Caches\ollama-profile.
- Logs/startup record: E:\AI\Caches\ollama-server.
- Temporary data: E:\AI\Downloads\Temp; CUDA cache: E:\AI\Caches\cuda.

The official Windows instructions offer this zip with CLI and NVIDIA dependencies.
No GUI installer, updater, new GPU driver, service registration or automatic startup
was used. Archive, extraction and installed copies are retained, all on E:.
Explained before installation that existing Windows DLLs and NVIDIA driver remain
on C:. No new system-drive component was required or installed. Authenticode on
ollama.exe verified as Valid, signed by Ollama Inc.; the archive hash also matched
the official GitHub release asset digest.

Before installation: no executable was found in PATH, standard install locations
or uninstall registry; no Ollama process/service or port-11434 listener existed.
The existing E: model directories contained no files and were preserved. Existing
C: .ollama identity/config/cache was not moved, deleted or opened for key contents.

## Observed running server

- PID at verification: 30844; image: E:\AI\Ollama\ollama.exe.
- CLI: ollama version is 0.40.11; GET /api/version: version 0.40.11.
- Endpoint: http://127.0.0.1:11434; process socket inspection found exactly one
  listener, 127.0.0.1:11434, with no wildcard/LAN listener.
- Read the actual server process environment, not just user configuration:
  OLLAMA_MODELS=E:\AI\OllamaModels, OLLAMA_HOST=127.0.0.1:11434,
  OLLAMA_NO_CLOUD=1, OLLAMA_NOPRUNE=1. Cloud access and automatic pruning are off.
- USERPROFILE/HOME/APPDATA/LOCALAPPDATA in this server are under the dedicated
  E: profile. Its TEMP/TMP/TMPDIR and CUDA cache are also on E:. The operator's
  Windows profile and existing keys were not reassigned globally.
- One model/parallel request maximum; default context ceiling configured to 16384.
- GET /api/tags and GET /api/ps succeeded: zero installed and zero loaded models.
- Model-file inventory before/after is identical. No pull/run/generate/chat API
  request was issued. Metadata GETs do not establish inference or GPU performance.

The hidden background server remains running for the current Windows session;
it is not an installed autostart service. The storage helper exposes its E: CLI
in the project shell. For a later manual restart only after confirming port 11434
is free:

```powershell
. .\scripts\use-e-storage.ps1
python .\scripts\start-local-ollama.py
```

The launcher refuses an occupied port, never replaces its listener, filters
credential-like environment variables, uses a dedicated E: child profile, disables
cloud/pruning, and never pulls models or invokes inference. It writes a startup
receipt and new logs on E:. To stop it, identify and stop only its recorded PID;
do not terminate unrelated Ollama processes or reuse stale PIDs blindly.

## Historical model recommendation (subsequently approved)

Recommend **qwen3:8b-q4_K_M**, 8.19B parameters, **Q4_K_M** quantization.
The official public manifest contains **5225388164 bytes** of config/layers:
about **5.23 GB / 4.87 GiB** before any blob deduplication. The weight layer itself
is 5225374496 bytes, digest
a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f.
Only the small manifest was fetched to inspect sizes; no weight blob was fetched.
No existing model files were available for deduplication at verification time.

Proposed settings after approval: **16384 total context tokens**, a single request
and one loaded model; use non-thinking mode for bounded structured browser-action
responses. These are a recommendation, not a model that has been loaded/tested.

Observed hardware:

| Resource | Observation |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4070 SUPER |
| Dedicated VRAM | 12282 MiB, approximately 12 GiB |
| Free VRAM | 10343 MiB initially; 10103 MiB at final verification; fluctuates |
| NVIDIA driver | 617.14 |
| Physical RAM | 34298929152 bytes, approximately 32 GiB |
| Available RAM | About 12.7-13.0 GiB during verification; fluctuates |

Memory estimate, **not measured allocation**: 4.87 GiB quantized weights plus
approximately 2.25 GiB FP16 KV cache at 16384 tokens, plus graph/runtime/scratch
buffers. Budget **8-10 GiB VRAM** and **8-12 GiB host-memory headroom**. This should
be plausible on this GPU for the small bounded task, but the upper end is close
to currently free VRAM; actual allocation/CPU offload must be checked after an
approved download/load. Do not claim fit or speed before measurement.

KV estimate uses the official model config: 36 layers, 8 KV heads and head size
128: 2 (K/V) * 36 * 8 * 128 * 2 bytes * 16384 = 2415919104 bytes. Host-memory
usage depends on memory mapping/offload and may overlap VRAM residency; this is
a conservative headroom recommendation, not extra measured resident RAM.
Larger contexts/concurrency increase memory. The 16k proposal is for this small
CRM workload, not a general long-context browsing guarantee. Prompt fit must be
checked explicitly rather than silently truncating a task.

## Structured responses and current integration limitation

The model is advertised with tool support. Local Ollama supports JSON-schema
responses using the format parameter and tool calls. Browser Use 0.13.11's
installed ChatOllama serializes its action schema into format and validates
returned JSON, so this is capability-compatible with the DOM-only browser-action
approach. No vision capability is assumed. Successful schema adherence/tool
selection on this computer is still unverified without an approved model load.

**Before the local-adapter milestone below, the adapter was not wired for Ollama:** AgentConfig only accepts
Anthropic and the worker explicitly constructs ChatAnthropic. Also, installed
ChatOllama returns usage=None despite native Ollama response counters, so reusing
the present budget wrapper unchanged would block subsequent calls as unknown.
A separately authorized local-provider integration with trustworthy native usage
accounting is needed before any local agent trial. Do not weaken the usage guard
or claim this installation alone enables the benchmark. No adapter feature was
added here, and the paid pilot remains on hold.

Sources: [official Windows standalone instructions](https://docs.ollama.com/windows),
[exact model tag/quantization](https://ollama.com/library/qwen3:8b-q4_K_M),
[official Qwen architecture](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json),
[Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs),
[Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling).

Evidence: runs/ollama_install_20261027/installation.json,
server-verification.json, models-before.json and proposed-model-manifest.json.
These are local ignored artifacts, not model benchmark results.


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
