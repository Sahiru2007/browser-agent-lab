# Five-minute technical demonstration (no model calls)

This walkthrough uses the existing CRM plus retained evidence. It never invokes
agent_run, comparison/pilot --execute or a model endpoint. All paths below are
project-relative; raw runs are author-local and intentionally absent in Git.
A reviewer with only a clone can inspect CASE_STUDY.md and run scripted controls,
but needs separately arranged evidence access to audit historical traces.

1. Load `. .\scripts\use-e-storage.ps1`, ensure frontend/dist/index.html exists
   (otherwise `npm --prefix frontend run build`). Check port ownership with
   `Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue`.
   If another service owns it, inspect its process and choose an unused port;
   never kill it merely to run the demo.
2. Start `uv run uvicorn lab.app:create_app --factory --host 127.0.0.1 --port 8000`
   with a fresh/manual database, never a retained trial.db. Visit
   http://127.0.0.1:8000. Search Asha, show the two similar names, select by email
   and open labeled company/email details. You may demonstrate a manual edit in
   this disposable demo DB; it is not an agent trial or new benchmark observation.
3. Open `runs/agent_20261027T104235Z_60a31f72/result.json`: the agent success claim
   coexists with duplicate_customer, two customers and two creation events.
   Explain post-commit confirmation loss using its retained trace; the DB is
   operator audit evidence, never runtime recovery input.
4. Open `runs/local_recovery_comparison_20261027/report.html`, then
   `runs/recovery_guard_20261027/report.html`: instruction-only lost trials
   duplicate, whereas guarded trials have correct DB state but two unresolved
   workflows. Zero live retry blocks; separate technical tests verify blocking.
5. Open `runs/feedback_ablation_20261027/report.html`: A and B each confirm 1/2;
   fresh GET alone is insufficient. Open `runs/editing_pilot_20261027/report.html`
   and independent-audit.json: six correct edits, three positive success flags,
   37 no-op saves. Contrast company/101's qualified verification failure with
   email/202's explicit incorrect failed-write claim.
6. Show the efficiency table/method in CASE_STUDY.md and optionally run the
   read-only command `uv run --offline --extra agent python
   scripts/summarize-editing-evidence.py runs/editing_pilot_20261027` as one line.
   Explain why 60 calls after acknowledgment are operator hindsight, not an
   agent-visible DB check or a claim of 60 unnecessary calls. No model is called.

Use `uv run playwright show-trace PATH` on an existing browser-evidence/trace.zip
for deeper browser inspection; installed Playwright is required, no new inference.
The RC audit's separate manual server uses an E:-resident disposable database and
logs under runs/portfolio_rc_20261027, when available. See STATUS.md for its URL.

Reviewer handoff: this RC is local and unpushed. Arrange repository access and an
explicitly reviewed/redacted evidence handoff if independent raw-evidence review is
needed; do not attach DBs/traces/credentials automatically. No reliability claim,
public release, visibility change or extra execution is implied by this demo.
