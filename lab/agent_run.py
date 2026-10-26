"""Run one real-agent trial; the operator retains all database/evaluation access."""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

from lab.adapters import AgentConfig, AgentRequest, redact_credentials, select_adapter
from lab.app import ROOT
from lab.database import make_engine, snapshot, sqlite_url
from lab.evaluate import evaluate
from lab.run import available_port, wait_ready
from lab.tasks import customer_task


def framework_version():
    try:
        return version("browser-use")
    except PackageNotFoundError:
        return None


def run_trial(task, adapter, config, output):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    url = f"http://127.0.0.1:{available_port()}"
    engine = make_engine(sqlite_url(output / "trial.db"))
    report = {
        "kind": adapter.kind, "adapter": type(adapter).__name__, "task": asdict(task),
        "provider": config.provider, "model": config.model,
        "framework_version": framework_version(), "limits": asdict(config),
        "agent": None, "evaluation": None, "execution_error": None,
        "before": None, "after": None,
    }
    process = None
    try:
        with (output / "server.log").open("w", encoding="utf-8") as logfile:
            # Provider credentials are not needed by the CRM server.
            env = {k: v for k, v in os.environ.items()
                   if not any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD"))}
            env.update(DATABASE_URL=sqlite_url(output / "trial.db"), LAB_FAULT=task.fault)
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "lab.app:create_app", "--factory",
                 "--host", "127.0.0.1", "--port", str(url.rsplit(":", 1)[1]),
                 "--no-access-log"], cwd=ROOT, env=env, stdout=logfile,
                stderr=subprocess.STDOUT,
            )
            try:
                wait_ready(url, process)
                report["before"] = snapshot(engine)
                if report["before"]["customers"] != list(task.starting_data):
                    raise RuntimeError("Starting data differs from versioned task")
                try:
                    report["agent"] = adapter.execute(
                        AgentRequest(url, task.instruction), config, output)
                    report["execution_error"] = report["agent"].get("execution_error")
                except subprocess.TimeoutExpired:
                    report["execution_error"] = "limit:ExecutionTimeout"
                except Exception as exc:
                    report["execution_error"] = f"adapter:{type(exc).__name__}"
            except Exception as exc:
                report["execution_error"] = f"infrastructure:{type(exc).__name__}"
            finally:
                # Stop the server BEFORE grading, even when the adapter failed, to
                # avoid a late request committing after the evaluator snapshot.
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                if report["before"] is not None:
                    try:
                        report["after"] = snapshot(engine)
                        report["evaluation"] = evaluate(
                            report["before"], report["after"], task.expected_customer)
                    except Exception as exc:
                        report["execution_error"] = f"evaluator:{type(exc).__name__}"
    except Exception as exc:
        report["execution_error"] = f"infrastructure:{type(exc).__name__}"
    finally:
        engine.dispose()
    report["duration_seconds"] = round(time.monotonic() - started, 3)
    report["trial_status"] = (
        "execution_error" if report["execution_error"] else
        "business_pass" if report["evaluation"] and report["evaluation"]["passed"]
        else "business_fail"
    )
    # Never persist provider credentials, including accidental agent echoes.
    text = json.dumps(redact_credentials(report), indent=2)
    (output / "result.json").write_text(text, encoding="utf-8")
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", required=True, choices=["browser-use"])
    parser.add_argument("--scenario", choices=["normal", "lost-confirmation"], default="normal")
    parser.add_argument("--allow-paid", action="store_true",
                        help="Explicitly authorize one configured trial's model calls")
    args = parser.parse_args()
    if not args.allow_paid:
        parser.error("Real trials require --allow-paid; no model calls were made")
    try:
        config = AgentConfig.from_env()
        adapter = select_adapter(args.adapter)
    except ValueError as exc:
        parser.error(str(exc))
    if framework_version() != "0.13.11":
        parser.error("Install the pinned integration: uv sync --locked --extra agent")
    if not (ROOT / "frontend" / "dist" / "index.html").exists():
        parser.error("Build the frontend first")
    trial_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = ROOT / "runs" / ("agent_" + trial_id)
    report = run_trial(customer_task(args.scenario), adapter, config, output)
    print(report["trial_status"])
    print(f"Report: {output / 'result.json'}")
    return 2 if report["execution_error"] else 0 if report["evaluation"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
