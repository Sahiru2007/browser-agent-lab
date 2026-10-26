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
requested description. No GitHub Actions result is claimed yet.
No Docker/PostgreSQL run, AI-agent run, or paid model
call was performed. The TestClient deprecation warning is nonfatal; review it
when upgrading dependencies.

example-control-results.json preserves the original synthetic HTTP examples.
The local reports above are the evidence for this setup verification.
