"""Benchmark Engine v1: sequential isolated trials and offline, evidence-based analysis."""

import argparse
import hashlib
import html
import json
import math
import random
import subprocess
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from lab.adapters import AgentConfig, redact_credentials, select_adapter
from lab.agent_run import framework_version, run_trial
from lab.app import ROOT
from lab.benchmark_metrics import aggregate, trial_metrics, valid_evaluation
from lab.run import run_case
from lab.tasks import benchmark_task

VERSION = "1.0.0"
SCENARIOS = ("normal", "lost-confirmation")
CONTROLS = ("blind-retry", "verify")
AGENTS = ("basic-browser-use", "verification-browser-use")
STRATEGIES = CONTROLS + AGENTS


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(redact_credentials(value), indent=2, allow_nan=False),
                         encoding="utf-8")
    temporary.replace(path)


def provenance():
    def git(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            return None

    commit = git("rev-parse", "HEAD")
    patch = git("diff", "HEAD", "--binary")
    paths = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    source = hashlib.sha256()
    if paths is not None:
        for path in sorted(set(paths.split(b"\0")) - {b""}):
            target = ROOT / path.decode("utf-8")
            if target.is_file():
                source.update(path + b"\0" + target.read_bytes() + b"\0")
    packages = {}
    for package in ("browser-use", "playwright", "sqlalchemy", "fastapi"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = None
    return {
        "source_commit": commit.decode().strip() if commit else None,
        "tracked_patch_sha256": hashlib.sha256(patch).hexdigest() if patch is not None else None,
        "working_tree_sha256": source.hexdigest() if paths is not None else None,
        "locks": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                  for name in ("uv.lock", "frontend/package-lock.json")},
        "packages": packages,
    }


def make_manifest(scenarios=SCENARIOS, strategies=CONTROLS, trials=1, seed=0,
                  transport="browser", config=None, max_cost_usd=None):
    if (not scenarios or len(set(scenarios)) != len(scenarios)
            or any(s not in SCENARIOS for s in scenarios)):
        raise ValueError("Select distinct supported scenarios")
    if (not strategies or len(set(strategies)) != len(strategies)
            or any(s not in STRATEGIES for s in strategies)):
        raise ValueError(
            "Select distinct supported strategies; checkpoint recovery is not implemented")
    if isinstance(trials, bool) or not isinstance(trials, int) or trials < 1:
        raise ValueError("trials must be a positive repetition count per scenario/strategy")
    if transport not in {"http", "browser"}:
        raise ValueError("Unsupported transport")
    if any(s in AGENTS for s in strategies):
        if transport != "browser" or config is None:
            raise ValueError("Agent strategies require browser transport and configuration")
        if (isinstance(max_cost_usd, bool) or not isinstance(max_cost_usd, (int, float))
                or not math.isfinite(max_cost_usd)
                or max_cost_usd <= 0):
            raise ValueError("Agent benchmarks require a finite positive run-wide USD budget")
    rng = random.Random(seed)
    schedule = []
    # Canonical scenario/arm sets keep ordering independent of CLI argument order.
    for repetition in range(trials):
        for scenario in sorted(scenarios):
            arms = sorted(strategies)
            rng.shuffle(arms)
            for strategy in arms:
                agent = strategy in AGENTS
                schedule.append({
                    "trial_id": f"trial-{len(schedule) + 1:06d}",
                    "block_id": f"{scenario}-{repetition + 1:06d}",
                    "repetition": repetition + 1, "scenario": scenario, "strategy": strategy,
                    "transport": transport, "task_id": "customer.create_once",
                    "task_version": "1.1.0" if agent else "1.0.0", "policy_version": "1.0.0",
                    "kind": "real_ai_agent_trial" if agent else f"scripted_{transport}_control",
                    "provider": config.provider if agent else None,
                    "model": config.model if agent else None,
                })
    return {"benchmark_version": VERSION, "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seed": seed, "repetitions": trials, "schedule": schedule,
            "planned_trials": len(schedule), "agent_config": asdict(config) if config else None,
            "max_cost_usd": max_cost_usd, "reserved_run_cost_usd": 0,
            "started_trial_ids": [], "state": "planned", "provenance": provenance()}


def execute_trial(spec, folder, manifest):
    """Production dispatch; all business outcomes come from existing independent graders."""
    if spec["strategy"] in AGENTS:
        config = AgentConfig(**manifest["agent_config"])
        raw = run_trial(benchmark_task(spec["scenario"], spec["strategy"]),
                        select_adapter("browser-use"), config, folder / "evidence")
        return raw, "evidence/result.json"
    fault = "none" if spec["scenario"] == "normal" else "lost_confirmation"
    blind = spec["strategy"] == "blind-retry"
    case = {"name": spec["strategy"].replace("-", "_"), "fault": fault,
            "driver": "blind_retry" if blind else "verify_before_retry",
            "expected_pass": not (blind and fault != "none")}
    if spec["transport"] == "http":
        raw = run_case(None, case, folder / "evidence", "http")
    else:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                raw = run_case(browser, case, folder / "evidence", "browser")
                raw["browser_version"] = browser.version
            finally:
                browser.close()
    return raw, f"evidence/{raw['trial_id']}/result.json"


def run_benchmark(manifest, output, allow_paid=False, executor=None):
    mocked = executor is not None
    if mocked and getattr(executor, "kind", None) != "mocked_adapter_test":
        raise ValueError("Injected executors must be explicitly labeled mocked_adapter_test")
    agents = any(row["strategy"] in AGENTS for row in manifest["schedule"])
    if agents and not mocked and not allow_paid:
        raise ValueError("Real-agent scheduling requires explicit --allow-paid authorization")
    executor = executor or execute_trial
    output.mkdir(parents=True, exist_ok=False)
    manifest["mocked"] = mocked
    atomic_json(output / "manifest.json", manifest)
    for spec in manifest["schedule"]:
        folder = output / "trials" / spec["trial_id"]
        folder.mkdir(parents=True)
        record = {**spec, "state": "scheduled", "evaluation": None, "execution_error": None,
                  "metrics": {}, "evidence": None}
        if mocked:
            record["kind"] = "mocked_adapter_test"
        atomic_json(folder / "result.json", record)
    manifest["state"] = "running"
    atomic_json(output / "manifest.json", manifest)
    try:
        for spec in manifest["schedule"]:
            folder = output / "trials" / spec["trial_id"]
            record = json.loads((folder / "result.json").read_text())
            if spec["strategy"] in AGENTS:
                reservation = manifest["agent_config"]["max_cost_usd"]
                if (manifest["reserved_run_cost_usd"] + reservation
                        > manifest["max_cost_usd"] + 1e-12):
                    record["state"] = "not_run_budget"
                    atomic_json(folder / "result.json", record)
                    continue
                # Durable reservation before dispatch; no refund for failures/unknown usage.
                manifest["reserved_run_cost_usd"] += reservation
                atomic_json(output / "manifest.json", manifest)
            record["state"] = "running"
            atomic_json(folder / "result.json", record)
            manifest["started_trial_ids"].append(spec["trial_id"])
            atomic_json(output / "manifest.json", manifest)
            started = time.monotonic()
            interrupted = False
            try:
                raw, evidence = executor(spec, folder, manifest)
                expected_kind = "mocked_adapter_test" if mocked else spec["kind"]
                if raw.get("kind") != expected_kind:
                    raise ValueError("Executor result kind does not match the scheduled trial")
                if raw.get("evaluation") is None and not raw.get("execution_error"):
                    raw["execution_error"] = "evaluator:MissingEvaluation"
                elif raw.get("evaluation") is not None and not valid_evaluation(raw):
                    raw["execution_error"] = "evaluator:InvalidEvaluation"
                    raw["evaluation"] = None
                record.update(evaluation=raw.get("evaluation"),
                              execution_error=raw.get("execution_error"), evidence=evidence,
                              control_behaved_as_expected=raw.get("control_behaved_as_expected"),
                              browser_version=raw.get("browser_version"),
                              final_agent_message=(raw.get("agent") or {}).get(
                                  "final_agent_message"))
                record["metrics"] = trial_metrics(
                    raw, time.monotonic() - started, record["kind"], manifest["agent_config"])
                record["state"] = "failed" if record["execution_error"] else "completed"
            except KeyboardInterrupt:
                interrupted = True
                record.update(state="interrupted", execution_error="infrastructure:Interrupted")
            except Exception as exc:
                record.update(state="failed",
                              execution_error=f"infrastructure:{type(exc).__name__}")
            finally:
                if not record["metrics"]:
                    record["metrics"] = trial_metrics(
                        {}, time.monotonic() - started, record["kind"], manifest["agent_config"])
                atomic_json(folder / "result.json", record)
            if interrupted:
                manifest["state"] = "interrupted"
                break
        else:
            manifest["state"] = "finished"
    finally:
        atomic_json(output / "manifest.json", manifest)
        summary = analyze(output)
    return summary


def evidence_link(trial, relative):
    if not relative:
        return None
    path = PurePosixPath(relative)
    if (path.is_absolute() or ".." in path.parts or "\\" in relative
            or ":" in relative or not relative.startswith("evidence/")):
        raise ValueError("Evidence links must stay in the trial evidence directory")
    return "trials/" + trial["trial_id"] + "/" + quote(str(path), safe="/")


def render_html(summary):
    def escape(value):
        return html.escape(str(value), quote=True)

    def binary(value):
        if value["value"] is None:
            return "unavailable (n=0)"
        lo, hi = value["wilson95"]
        return (f"{value['numerator']}/{value['denominator']} ({value['value']:.1%}); "
                f"Wilson 95% [{lo:.1%}, {hi:.1%}]")

    groups = []
    for group in summary["groups"]:
        metrics = group["metrics"]
        cells = [group["kind"], group["strategy"], group["scenario"], group["transport"],
                 f"{group['task_version']} / {group['policy_version']}",
                 f"{group['provider']} / {group['model']}",
                 f"{group['started']}/{group['planned']}", binary(group["operational_success"]),
                 binary(group["business_success"]), binary(group["duplicate_action_rate"])]
        for name in ("wall_seconds", "model_calls", "total_tokens", "estimated_cost_usd"):
            m = metrics[name]
            cells.append(f"{m['status']}; known {m['known_count']}; total {m['total']}; "
                         f"observed subtotal {m['observed_subtotal']}; "
                         f"median {m['median']}; p95 {m['p95']}; "
                         f"unknown {m['unknown_count']}; unavailable {m['unavailable_count']}")
        groups.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>")
    trials = []
    for trial in summary["trials"]:
        link = evidence_link(trial, trial.get("evidence"))
        evidence = (f'<a href="{escape(link)}">Raw runner JSON</a>'
                    if link and trial.get("evidence_available") else "Raw result unavailable")
        record_link = (f'<a href="trials/{escape(trial["trial_id"])}/result.json">Trial JSON</a>'
                       if trial.get("record_available") else "Trial JSON unavailable")
        details = json.dumps({"metrics": trial.get("metrics"),
                              "message": trial.get("final_agent_message")}, indent=2)
        trials.append(
            f"<tr><td>{escape(trial['trial_id'])}</td><td>{escape(trial['kind'])}</td>"
            f"<td>{escape(trial['strategy'])}</td><td>{escape(trial['scenario'])}</td>"
            f"<td>{escape(trial['state'])}</td><td>{escape(trial.get('evaluation'))}</td>"
            f"<td>{escape(trial.get('execution_error'))}</td><td>{evidence} "
            f"{record_link}"
            f"<details><summary>Metrics / message</summary><pre>"
            f"{escape(details)}"
            "</pre></details></td></tr>")
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        'style-src \'unsafe-inline\'">'
        '<title>Browser Agent Lab benchmark</title><style>'
        'body{font:14px system-ui;margin:2rem;color:#183c34}table{border-collapse:collapse;'
        'margin:1rem 0}td,th{border:1px solid #ccc;padding:.5rem;text-align:left}'
        'pre{white-space:pre-wrap;max-width:45rem}</style><h1>Benchmark Engine v1</h1>'
        f"<p>Run state: {escape(summary['state'])}. No real-agent success is inferred "
        "from scripted controls or mocked tests. Checkpoint recovery is not implemented.</p>"
        "<p>Rows are separated by kind, strategy, scenario, task/policy version and model. "
        "Operational success uses all started trials; business/duplicate rates use valid "
        "evaluations. Missing evaluations are not silently discarded from operational success. "
        "Wilson intervals describe binary samples, not demonstrated AI capability for controls.</p>"
        "<p>Metrics explicitly distinguish measured, estimated, unknown and unavailable. "
        "Known subtotals with incomplete coverage are partial, never full-run totals. "
        "Costs use operator price ceilings, not billing reconciliation. Timeout/interruption "
        "wall times include cleanup and do not imply completed task times.</p>"
        '<p><a href="manifest.json">Manifest</a> | <a href="summary.json">Summary JSON</a></p>'
        "<h2>Comparisons</h2><table><tr>" + "".join(f"<th>{title}</th>" for title in (
            "Kind", "Strategy", "Scenario", "Transport", "Task / policy", "Provider / model",
            "Started/planned", "Operational success",
            "Business success", "Duplicate actions", "Wall seconds", "Model calls", "Tokens",
            "Estimated USD")) + "</tr>" + "".join(groups) + "</table>"
        "<h2>Individual trial evidence</h2><table><tr><th>ID</th><th>Kind</th><th>Strategy</th>"
        "<th>Scenario</th><th>State</th><th>Independent evaluation</th><th>Execution error</th>"
        "<th>Evidence</th></tr>" + "".join(trials) + "</table></html>"
    )


def analyze(output):
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported benchmark manifest schema")
    trials = []
    for index, spec in enumerate(manifest["schedule"], 1):
        if spec["trial_id"] != f"trial-{index:06d}":
            raise ValueError("Invalid trial ID or schedule ordering")
        path = output / "trials" / spec["trial_id"] / "result.json"
        started = spec["trial_id"] in manifest.get("started_trial_ids", [])
        record = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            **spec, "state": "scheduled", "metrics": {}, "evaluation": None,
            "execution_error": None, "evidence": None}
        if not path.exists() and started:
            record.update(state="missing", execution_error="infrastructure:MissingTrialRecord")
        if manifest.get("mocked"):
            record["kind"] = "mocked_adapter_test"
        if record["trial_id"] != spec["trial_id"]:
            raise ValueError("Trial identity mismatch")
        evidence_link(record, record.get("evidence"))
        record["record_available"] = path.is_file()
        record["evidence_available"] = bool(record.get("evidence")) and (
            path.parent / record["evidence"]).is_file()
        trials.append(record)
    state = manifest["state"]
    if state == "running" or any(row["state"] == "running" for row in trials):
        state = "incomplete_or_interrupted"
    summary = {"benchmark_version": VERSION, "state": state,
               "manifest": "manifest.json", "trials": trials, "groups": aggregate(trials),
               "reserved_run_cost_usd": manifest["reserved_run_cost_usd"],
               "timing_note": "Wall measurements include cleanup; timeouts/interrupted "
               "tasks have censored completion times and are not completed-task timings"}
    atomic_json(output / "summary.json", summary)
    (output / "report.html").write_text(render_html(redact_credentials(summary)), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", nargs="+", choices=SCENARIOS, default=list(SCENARIOS))
    parser.add_argument("--strategy", nargs="+", choices=STRATEGIES, default=list(CONTROLS))
    parser.add_argument("--trials", type=int, default=1, help="Repetitions per scenario/strategy")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--transport", choices=["http", "browser"], default="browser")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--analyze", type=Path, help="Offline rebuild only; never executes trials")
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument("--max-cost-usd", type=float,
                        help="Run-wide estimated budget for agent trials")
    args = parser.parse_args()
    if args.analyze:
        analyze(args.analyze)
        print(f"Report: {args.analyze / 'report.html'}")
        return 0
    try:
        agents = any(s in AGENTS for s in args.strategy)
        if agents and not args.allow_paid:
            raise ValueError("Agent strategies require --allow-paid; no model calls were made")
        config = AgentConfig.from_env() if agents else None
        if agents and framework_version() != "0.13.11":
            raise ValueError("Install the pinned SDK: uv sync --locked --extra agent")
        if args.transport == "browser" and not (ROOT / "frontend/dist/index.html").is_file():
            raise ValueError("Build the frontend first")
        manifest = make_manifest(args.scenario, args.strategy, args.trials, args.seed,
                                 args.transport, config, args.max_cost_usd)
    except ValueError as exc:
        parser.error(str(exc))
    output = args.output or ROOT / "runs" / (
        "benchmark_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "_" + uuid.uuid4().hex[:8])
    summary = run_benchmark(manifest, output, args.allow_paid)
    print(f"Report: {output / 'report.html'}")
    if summary["state"] in {"interrupted", "incomplete_or_interrupted"}:
        return 130
    if any(t["execution_error"] or t["state"] == "not_run_budget" for t in summary["trials"]):
        return 2
    if any(t["kind"].startswith("scripted_") and not t.get("control_behaved_as_expected")
           for t in summary["trials"]):
        return 2
    if any(t["kind"] == "real_ai_agent_trial" and not t["evaluation"]["passed"]
           for t in summary["trials"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
