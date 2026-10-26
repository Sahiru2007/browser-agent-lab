"""Run scripted browser controls. These are NOT AI-agent benchmark results."""

import argparse
import html
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from lab.app import ROOT
from lab.database import make_engine, snapshot, sqlite_url
from lab.evaluate import evaluate
from lab.tasks import CUSTOMER, customer_task

EXPECTED = CUSTOMER
CASES = [
    {
        "name": "normal_reference",
        "fault": "none",
        "driver": "verify_before_retry",
        "expected_pass": True,
    },
    {
        "name": "recover_after_lost_confirmation",
        "fault": "lost_confirmation",
        "driver": "verify_before_retry",
        "expected_pass": True,
    },
    {
        "name": "detect_unsafe_retry",
        "fault": "lost_confirmation",
        "driver": "blind_retry",
        "expected_pass": False,
    },
]


def available_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_ready(base_url: str, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 20
    with httpx.Client(timeout=0.5, trust_env=False) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Application exited; inspect server.log")
            try:
                if client.get(base_url + "/api/health").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
    raise TimeoutError("Application did not become ready")


def drive(page, case: dict) -> dict:
    page.get_by_label("Full name", exact=True).fill(EXPECTED["name"])
    page.get_by_label("Email address", exact=True).fill(EXPECTED["email"])
    page.get_by_label("Company", exact=True).fill(EXPECTED["company"])
    page.get_by_role("button", name="Save customer", exact=True).click()
    status = page.get_by_role("status")
    expect(status).to_have_text(
        "Customer saved."
        if case["fault"] == "none"
        else "Could not confirm whether the customer was saved."
    )
    retried = False
    if case["fault"] != "none":
        if case["driver"] == "blind_retry":
            retried = True
            page.get_by_role("button", name="Save customer", exact=True).click()
            expect(status).to_have_text("Customer saved.")
        else:
            page.get_by_label("Search by name or email").fill(EXPECTED["email"])
            expect(page.get_by_role("cell", name=EXPECTED["email"], exact=False)).to_have_count(1)
    return {"confirmation_message": status.inner_text(), "retried": retried}


def drive_http(base_url: str, case: dict) -> dict:
    """Exercise the real server without a browser; label this transport separately."""
    retried = False
    with httpx.Client(base_url=base_url, timeout=0.7, trust_env=False) as client:
        try:
            response = client.post("/api/customers", json=EXPECTED)
            response.raise_for_status()
            if case["fault"] != "none":
                raise AssertionError("Expected a post-commit confirmation timeout")
            message = "Customer saved."
        except httpx.ReadTimeout:
            if case["fault"] == "none":
                raise
            message = "Could not confirm whether the customer was saved."
            if case["driver"] == "blind_retry":
                retried = True
                client.post("/api/customers", json=EXPECTED).raise_for_status()
                message = "Customer saved."
            else:
                response = client.get("/api/customers", params={"q": EXPECTED["email"]})
                response.raise_for_status()
                records = response.json()
                assert len(records) == 1
                assert all(records[0][key] == value for key, value in EXPECTED.items())
    return {"confirmation_message": message, "retried": retried}


def run_case(browser, case: dict, output: Path, transport: str) -> dict:
    trial_id = case["name"] + "_" + uuid.uuid4().hex[:8]
    folder = output / trial_id
    folder.mkdir(parents=True)
    database_url = sqlite_url(folder / "trial.db")
    port = available_port()
    base_url = f"http://127.0.0.1:{port}"
    env = {**os.environ, "DATABASE_URL": database_url, "LAB_FAULT": case["fault"]}
    started = time.monotonic()
    report = {
        "trial_id": trial_id,
        **case,
        "kind": f"scripted_{transport}_control",
        "evaluation": None,
        "execution_error": None,
        "task": {"task_id": "customer.create_once", "version": "1.0.0",
                 "instruction": customer_task("normal").instruction, "customer": EXPECTED},
    }
    engine = make_engine(database_url)
    context = None
    before = None
    stage = "infrastructure"
    with (folder / "server.log").open("w", encoding="utf-8") as logfile:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "lab.app:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-access-log",
            ],
            cwd=ROOT,
            env=env,
            stdout=logfile,
            stderr=subprocess.STDOUT,
        )
        try:
            wait_ready(base_url, process)
            before = snapshot(engine)
            stage = "driver"
            driver_started = time.monotonic()
            if transport == "browser":
                context = browser.new_context()
                context.tracing.start(screenshots=True, snapshots=True, sources=False)
                page = context.new_page()
                page.set_default_timeout(8000)
                page.goto(base_url, wait_until="networkidle")
                report["observation"] = drive(page, case)
                page.screenshot(path=str(folder / "final.png"), full_page=True)
            else:
                report["observation"] = drive_http(base_url, case)
            report["driver_duration_seconds"] = round(time.monotonic() - driver_started, 6)
        except Exception as exc:
            report["execution_error"] = f"{stage}:{type(exc).__name__}"
        finally:
            if context is not None:
                try:
                    context.tracing.stop(path=str(folder / "trace.zip"))
                except Exception as exc:
                    report["execution_error"] = f"Trace capture failed: {exc}"
                try:
                    context.close()
                except Exception as exc:
                    report["execution_error"] = f"Browser cleanup failed: {exc}"
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            if before is not None:
                try:
                    after = snapshot(engine)
                    report["before"] = before
                    report["after"] = after
                    report["evaluation"] = evaluate(before, after, EXPECTED)
                    triggered = after["faults"]
                    report["fault_was_triggered"] = (
                        len(triggered) == 0 if case["fault"] == "none" else len(triggered) == 1
                    )
                except Exception as exc:
                    report["execution_error"] = f"evaluator:{type(exc).__name__}"
            engine.dispose()
    report["duration_seconds"] = round(time.monotonic() - started, 3)
    report["control_behaved_as_expected"] = (
        report["execution_error"] is None
        and report["evaluation"] is not None
        and report["evaluation"]["passed"] == case["expected_pass"]
        and report.get("fault_was_triggered", False)
    )
    (folder / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "runs")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--transport", choices=["browser", "http"], default="browser")
    args = parser.parse_args()
    if args.transport == "browser" and not (ROOT / "frontend" / "dist" / "index.html").exists():
        parser.error("Build the frontend first: npm --prefix frontend run build")
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    output = args.output.resolve() / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    )
    output.mkdir(parents=True)
    if args.transport == "http":
        results = [
            run_case(None, case, output, "http") for _ in range(args.repeats) for case in CASES
        ]
    else:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception as exc:
                print(f"Browser startup failed: {exc}", file=sys.stderr)
                print("Install Chromium: uv run playwright install chromium", file=sys.stderr)
                print("For API-only controls: add --transport http", file=sys.stderr)
                return 2
            try:
                results = [
                    run_case(browser, case, output, "browser")
                    for _ in range(args.repeats)
                    for case in CASES
                ]
            finally:
                browser.close()
    summary = {
        "kind": f"scripted_{args.transport}_controls_not_ai_agent_results",
        "results": results,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    rows = []
    for result in results:
        evaluation = result["evaluation"]
        outcome = "ERROR" if evaluation is None else "PASS" if evaluation["passed"] else "FAIL"
        issues = ", ".join(evaluation["issues"]) if evaluation else result["execution_error"]
        rows.append(
            f"<tr><td>{html.escape(result['name'])}</td><td>{html.escape(result['driver'])}</td>"
            f"<td>{outcome}</td><td>{html.escape(issues)}</td>"
            f"<td><a href='{result['trial_id']}/result.json'>JSON</a></td></tr>"
        )
    (output / "report.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Browser Agent Lab</title>'
        "<style>body{font:15px system-ui;margin:50px;color:#183c34}table{border-collapse:collapse}"
        "th,td{padding:15px;border:1px solid #ddd;text-align:left}</style>"
        "<h1>Control run report</h1>"
        f"<p>Transport: {args.transport}. Scripted controls, not AI-agent benchmark results.</p>"
        "<p>The unsafe-retry control should fail business evaluation: it creates two customers.</p>"
        "<table><tr><th>Scenario</th><th>Driver</th><th>Business result</th>"
        "<th>Issues</th><th>Evidence</th></tr>" + "".join(rows) + "</table></html>",
        encoding="utf-8",
    )
    for result in results:
        print(
            result["name"],
            "CONTROL OK" if result["control_behaved_as_expected"] else "CONTROL ERROR",
        )
    print(f"Report: {output / 'report.html'}")
    return 0 if all(r["control_behaved_as_expected"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
