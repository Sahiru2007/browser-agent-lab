"""Scripted browser editing controls; never AI-agent benchmark results."""

import argparse
import html
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from lab.agent_run import run_trial
from lab.app import ROOT
from lab.database import make_engine, snapshot, sqlite_url
from lab.evaluate import evaluate_task
from lab.tasks import edit_task


@dataclass(frozen=True)
class ScriptedConfig:
    provider: None = None
    model: None = None


class EditBrowserControl:
    kind = "scripted_browser_edit_control"

    def __init__(self, identifier_email, field, value):
        self.email, self.field, self.value = identifier_email, field, value

    def execute(self, request, config, output):
        evidence = output / "browser-evidence"
        evidence.mkdir()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            context.tracing.start(screenshots=True, snapshots=True, sources=False)
            try:
                page = context.new_page()
                page.set_default_timeout(8000)
                page.goto(request.url, wait_until="networkidle")
                # Broad search first: both similar-name records are visible.
                page.get_by_label("Search by name or email").fill("Asha")
                expect(page.get_by_role("button", name="Open details for")).to_have_count(2)
                page.get_by_label("Search by name or email").fill(self.email)
                record = page.get_by_role("button", name="Open details for", exact=False).filter(
                    has_text="Asha Perera")
                expect(record).to_have_count(1)
                record.click()
                details = page.get_by_role("region", name="Customer details", exact=True)
                expect(details.get_by_label("Edit email address")).to_have_value(self.email)
                original = {"email": details.get_by_label("Edit email address").input_value(),
                            "company": details.get_by_label("Edit company").input_value()}
                label = "Edit company" if self.field == "company" else "Edit email address"
                details.get_by_label(label, exact=True).fill(self.value)
                with page.expect_response(lambda r: r.request.method == "PATCH") as response:
                    details.get_by_role("button", name="Save changes", exact=True).click()
                assert response.value.status == 200
                expect(details.get_by_role("status")).to_have_text("Changes saved.")
                page.screenshot(path=str(evidence / "saved.png"), full_page=True)
                # A real follow-up no-op must not add a second business edit/audit.
                details.get_by_role("button", name="Save changes", exact=True).click()
                expect(details.get_by_role("status")).to_have_text("No changes to save.")
                details.get_by_role("button", name="Close details").click()
                lookup = self.value if self.field == "email" else self.email
                page.get_by_label("Search by name or email").fill(lookup)
                reopened = page.get_by_role("button", name="Open details for").filter(
                    has_text="Asha Perera")
                expect(reopened).to_have_count(1)
                reopened.click()
                details = page.get_by_role("region", name="Customer details", exact=True)
                expect(details.get_by_label(label, exact=True)).to_have_value(self.value)
                other = "email" if self.field == "company" else "company"
                other_label = "Edit email address" if other == "email" else "Edit company"
                expect(details.get_by_label(other_label)).to_have_value(original[other])
                page.screenshot(path=str(evidence / "reopened.png"), full_page=True)
                return {"execution_error": None, "observation": {
                    "selected_by_email": self.email, "changed_field": self.field,
                    "visible_value_after_reopen": details.get_by_label(label).input_value(),
                    "unrequested_field_preserved_in_UI": other,
                    "followup_noop_feedback": "No changes to save.",
                }}
            finally:
                try:
                    context.tracing.stop(path=str(evidence / "trace.zip"))
                finally:
                    context.close()
                    browser.close()


def run_controls(output):
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for field in ("company", "email"):
        task = edit_task(field)
        folder = output / field
        adapter = EditBrowserControl(task.identifier_email, field, task.changes[field])
        report = run_trial(task, adapter, ScriptedConfig(), folder)
        engine = make_engine(sqlite_url(folder / "trial.db"))
        try:
            current = snapshot(engine)
        finally:
            engine.dispose()
        regrade = evaluate_task(report["before"], current, task) if report["before"] else None
        verified = current == report["after"] and regrade == report["evaluation"]
        result = {"task_id": task.task_id, "version": task.version,
                  "report": field + "/result.json", "evaluation": report["evaluation"],
                  "execution_error": report["execution_error"],
                  "saved_database_regrade_matches": verified}
        results.append(result)
        print(field, "CONTROL OK" if verified and not report["execution_error"]
              and report["evaluation"]["passed"] else "CONTROL ERROR")
    summary = {"kind": "scripted_browser_edit_controls_not_ai_agent_results", "results": results}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    rows = ''.join('<tr><td>' + html.escape(r['task_id']) + '</td><td>'
                   + html.escape(str(r['evaluation'])) + '</td><td>'
                   + str(r['saved_database_regrade_matches']) + '</td><td><a href="'
                   + r['report'] + '">JSON/database evidence</a></td><td><a href="'
                   + r['report'].replace('result.json', 'browser-evidence/trace.zip')
                   + '">Browser trace</a></td></tr>' for r in results)
    (output / "report.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Edit controls</title>'
        '<h1>Scripted customer editing controls</h1><p>Not AI-agent results. Each saved database '
        'was independently regraded after browser/server shutdown.</p><table><tr><th>Task</th>'
        '<th>Grade</th><th>Regrade matches</th><th>Evidence</th><th>Trace</th></tr>'
        + rows + '</table></html>', encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not (ROOT / 'frontend/dist/index.html').exists():
        parser.error('Build the frontend first')
    output = args.output or ROOT / 'runs' / ('edit_controls_' + datetime.now(timezone.utc).strftime(
        '%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8])
    summary = run_controls(output)
    print('Report:', output / 'report.html')
    return 0 if all(r['saved_database_regrade_matches'] and not r['execution_error']
                    and r['evaluation'] and r['evaluation']['passed']
                    for r in summary['results']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
