# Versioned tasks

Creation tasks and their frozen wording remain unchanged. EditTask is a separate
operator-owned definition; seeds, assertions and faults never enter AgentRequest.

| ID | Version | Business instruction |
| --- | --- | --- |
| customer.change_company | 1.0.0 | Find the existing customer with email asha@example.test and change only their company to Evergreen Cooperative. Preserve all other customer information. |
| customer.change_email | 1.0.0 | Find the existing customer with email asha@example.test and change only their email to asha.perera@example.test. Preserve all other customer information. |

Both start with Asha Perera (asha@example.test, North Farm) and Asha Pereira
(apereira@example.test, South Farm). No database ID appears in the instruction.
Both have fault=none; no edit failure injection was introduced. Expected changes
are kept operator-side and checked against committed snapshots/audit history.

An actual edit has one customer.updated event with full before/after and changed
fields. A no-op save has no event. See ARCHITECTURE.md for the complete contract.

Build the frontend, then run both scripted Chromium controls:

```powershell
. .\scripts\use-e-storage.ps1
uv run --offline --extra agent python -m lab.edit_run
```

An optional --output DIRECTORY must name a new directory. It contains company/
and email/ result.json, trial.db, browser-evidence/trace.zip and screenshots,
plus summary.json and an offline report.html. Reports are scripted controls;
no agent trial or model usage is implied. The AI/benchmark command selectors
remain creation-only in this milestone; do not describe edits as benchmarked.
