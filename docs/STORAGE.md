# E: storage policy and verification - 27 October 2026

All local project downloads, installations, environments, caches and generated
files must use E:. This is recorded in AGENTS.md for future sessions.

## Use the project storage environment

From E:\projects\browser-agent-lab in PowerShell:

```powershell
. .\scripts\use-e-storage.ps1
```

If local scripts are blocked, start a shell with
`powershell.exe -NoProfile -ExecutionPolicy RemoteSigned` first. Only that shell's
policy is changed; do not weaken permanent user/machine policy. The script does
not download, delete or migrate anything. It creates E: directories, sets the
current process environment and prefers E: project tool copies. `-Persist` also
sets user-level storage variables; it was applied during this setup. It does not
persist project-specific PATH, UV_PYTHON or UV_PROJECT_ENVIRONMENT selections to
other projects. Run it before project commands in each new/stale shell.

| Purpose | Effective location |
| --- | --- |
| Project, generated reports, frontend build | E:\projects\browser-agent-lab |
| Python venv | E:\projects\browser-agent-lab\.venv |
| Frontend dependencies | E:\projects\browser-agent-lab\frontend\node_modules |
| Project uv / Node / npm binaries | .tools\bin / .tools\nodejs inside the project |
| Ollama model storage | E:\AI\OllamaModels |
| Installer/archive downloads | E:\AI\Downloads |
| Temporary files / download intermediates | E:\AI\Downloads\Temp |
| uv dependency cache | E:\AI\Caches\uv |
| Managed Python runtimes | E:\AI\Python |
| Managed Python archive cache | E:\AI\Downloads\uv-python |
| uv tool installations / executable links | E:\AI\Caches\uv-tools / E:\AI\Caches\bin |
| npm cache / global prefix | E:\AI\Caches\npm / E:\AI\Caches\npm-global |
| pip cache | E:\AI\Caches\pip |
| Playwright browsers | E:\AI\Caches\ms-playwright |
| Standalone Browser Use config | E:\AI\Caches\browser-use |
| Generic XDG cache | E:\AI\Caches |
| Optional Hugging Face / Torch / CUDA caches | E:\AI\Caches\huggingface / torch / cuda |

The script sets the corresponding OLLAMA_MODELS, UV_*, NPM_CONFIG_*,
PLAYWRIGHT_BROWSERS_PATH, PIP_CACHE_DIR, BROWSER_USE_CONFIG_DIR, XDG_CACHE_HOME,
HF_HOME, TORCH_HOME, CUDA_CACHE_PATH, TEMP, TMP and TMPDIR variables. Browser
garbage collection is disabled with PLAYWRIGHT_SKIP_BROWSER_GC=1 so installing a
revision does not silently remove previously identified browser assets.
The isolated agent worker inherits only explicitly allowed nonsecret storage
variables; database/fault settings and unrelated provider keys remain excluded.
Its per-trial SDK config/profile/scratch files remain in fresh E: temporary folders.

Always inspect effective install/download targets before installing more software.
Save installer executables/archives explicitly beneath E:\AI\Downloads and select
an E: install target/portable distribution where supported. Do not assume the
personal browser's default Downloads directory has changed. npm local installs
stay in frontend/node_modules; global installs, if specifically requested, use
the E: prefix. No global packages were installed for this task.

## Existing data identified and preserved

Before any new download, the audit identified:

- C:\Users\Sahiru Bodahewa\AppData\Local\ms-playwright: about 718 MiB.
- C:\Users\Sahiru Bodahewa\AppData\Local\npm-cache: about 1059.4 MiB.
- E:\AI\Cache\uv: about 398.5 MiB (the previous singular Cache directory).
- The project's venv was on E: but based on the installed Python 3.11.9 on C:.
- Existing global Node, Python, uv, GitHub CLI and personal Chrome were on C:.
  An unrelated Hermes Python process was already on E:.

Explained the changes before performing them. Copied the exact required Chromium,
headless-shell, FFmpeg and winldd revisions from C: into the E: browser store.
Copied the old E: uv cache into E:\AI\Caches\uv. Both cache sources are retained.
Copied the existing Node/npm distribution into .tools\nodejs, retaining its C:
original. No personal Chrome process or unrelated application was stopped.

After configuring and dry-running E: targets, downloaded a 23.9 MiB managed
CPython 3.11.17 archive to E:\AI\Downloads\uv-python and installed it on E:.
The old project venv was retained at:

```text
E:\AI\Caches\backups\browser-agent-lab-venv-before-e-storage-20261027
```

Then created a fresh .venv against E: Python and restored all 118 locked packages,
including the optional SDK, **offline** from the copied cache. The backup is for
recovery, not a portable environment to run in its moved location. No C: Python,
Node, npm cache, browser store, uv installation or Ollama identity/config was
deleted or moved. Previous E:\AI\Temp and E:\AI\Cache directories are also retained.

Project runtime versions now observed: Python 3.11.17, uv 0.13.5, Node 24.22.1,
bundled npm 11.19.1, Chromium 156.0.8078.4. The old npm command selected a global
11.1.0 CLI; the E: Node distribution uses its bundled npm. The build passed.

An initial `npm cache add <directory>` probe failed with a DirFetcher packing
error. Packing the local frontend into E:\AI\Downloads\npm and adding that tarball
offline succeeded; npm verified actual content in E:\AI\Caches\npm\_cacache.
No package registry download was needed for that probe.

## Actual process/file verification

Evidence: runs/storage_verification_20261027/runtime-paths.json and browser.png.
This records live observations, not just registry/environment strings:

- Running uv PID 32560 loaded .tools\bin\uv.exe on E:.
- A uv-launched Python child PID 11616 used the E: managed interpreter; its
  sys.prefix was the project .venv and its sys.base_prefix was E:\AI\Python\... .
- Running Node PID 30936 loaded .tools\nodejs\node.exe on E:; the Playwright Node
  driver was also observed inside .venv on E:.
- Running Chromium PID 32128 and its children loaded the copied E: browser binary.
  Its real --user-data-dir pointed into E:\AI\Downloads\Temp and existed while live.
- Python and Node created actual temporary probe files on E:; their existence
  was checked while the children waited. Only those newly created probe files
  were cleaned up by their own processes.
- npm queried the E: cache from its E: runtime and wrote/verified cache content
  and logs there. The managed Python download archive was found on E:.

All checks passed in the migrated environment: Ruff, 81 tests (mocked SDK smoke
enabled), frontend build, three HTTP controls and three Chromium controls. These
remain scripted/mocked checks; the paid pilot remains on hold.

## Windows exceptions and Ollama status

Explained these exceptions before downloading/installing the managed runtime:
Windows, system DLLs and registry-backed user environment configuration remain
on the Windows system drive. Existing global binaries and personal Chrome remain
where installed. System services may retain machine TEMP=C:\Windows\Temp;
the project changes user/child-process temp, not machine-wide service settings.
Windows MSI caches, GPU drivers and some application updaters can also require
system-drive components. No MSI/system installer, driver or updater was run here.
Before any future installer with unavoidable C: writes, explain its exact scope;
never silently send a large installer/model/cache to C:.

At the initial storage audit, no Ollama executable/server was found; only model
directory inheritance was verified. This is now superseded by the completed
standalone installation in E:\AI\Ollama and observed loopback server environment.
See [OLLAMA.md](OLLAMA.md) for actual executable/version/socket verification and
the E: profile/log paths. The subsequently approved qwen3:8b-q4_K_M weights are now stored on E: and
validated locally; see OLLAMA.md for digest, size and runtime GPU measurements. Existing C: .ollama identity/config/cache
remains untouched and private key contents were never read.

Do not rely on the removed legacy OLLAMA_TMPDIR variable. OS TEMP/TMP/TMPDIR are
set to E: instead. If Ollama is installed later, its documented installer target
is `/DIR="E:\AI\Ollama"`; inspect update/log destinations too, and verify the new
server's actual paths after restart. Already running programs do not acquire
new environment values retroactively. Do not restart unrelated programs.

Official references: [uv storage](https://docs.astral.sh/uv/reference/storage/),
[uv environment](https://docs.astral.sh/uv/configuration/environment/),
[npm configuration](https://docs.npmjs.com/cli/v11/using-npm/config/),
[Playwright browser storage](https://playwright.dev/python/docs/browsers#managing-browser-binaries),
[Ollama Windows paths](https://docs.ollama.com/windows), and
[Ollama legacy temp-variable removal](https://github.com/ollama/ollama/issues/8545).


The subsequent local Browser Use adapter uses fresh E: temporary worker/browser
profiles via the loaded storage environment. Persistent synthetic action traces,
screenshots, native response usage and per-trial databases are under project runs/.
The Ollama server/model store stays on E: and is shared across trials; cloud remains
disabled. Two actual local trial results and limits are recorded in OLLAMA.md.
