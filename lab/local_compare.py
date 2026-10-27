"""Frozen, exploratory local recovery comparison; never dispatches paid providers."""

import argparse
import hashlib
import html
import itertools
import json
import math
import random
import statistics
import zipfile
from dataclasses import asdict, replace
from importlib.metadata import distribution, version
from pathlib import Path
from urllib.parse import urlsplit

from lab.adapters import OllamaConfig, select_adapter
from lab.agent_run import run_trial
from lab.agent_worker import BROWSER_ACTIONS
from lab.app import ROOT
from lab.benchmark import atomic_json, make_manifest, provenance
from lab.benchmark_metrics import rate, valid_evaluation
from lab.tasks import benchmark_task

SEEDS = (101, 202, 303)
POLICY = (
    "After any write whose outcome is uncertain, inspect the application's visible state "
    "to determine whether the intended change has already occurred before deciding to retry. "
    "Do not repeat an uncertain write unless those observations establish that it did not "
    "take effect."
)
ORIGINALS = ("agent_20261027T104036Z_f677e01c", "agent_20261027T104235Z_60a31f72")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()


def seed_data(seed):
    rng = random.Random(seed)
    names = rng.sample(["Amara Fernando", "Devi Senanayake", "Kamal Jayasinghe",
                        "Maya Dias", "Ravi De Silva", "Tara Samarasinghe"], 2)
    return [{"id": i, "name": name, "email": f"contact-{seed}-{i}@example.test",
             "company": rng.choice(["Orchid Grove", "Cedar Fields", "Maple Gardens"])}
            for i, name in enumerate(names, 1)]


def original_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for name in ORIGINALS for p in sorted((ROOT / "runs" / name).rglob("*"))
            if p.is_file()}


def harness_hashes():
    files = [ROOT / "lab" / name for name in (
        "adapters.py", "agent_worker.py", "ollama_model.py", "agent_run.py",
        "tasks.py", "local_compare.py", "evaluate.py", "database.py")]
    sdk = Path(distribution("browser-use").locate_file("browser_use/agent"))
    files += [sdk / "service.py", sdk / "views.py", *sdk.rglob("*.md")]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}


def prepare_manifest():
    if version("browser-use") != "0.13.11":
        raise ValueError("The pinned SDK is required; do not upgrade for this comparison")
    base = benchmark_task("normal", "basic-browser-use")
    originals = [json.loads((ROOT / "runs" / n / "result.json").read_text()) for n in ORIGINALS]
    if any(r["task"]["instruction"] != base.instruction
           or r["limits"] != asdict(OllamaConfig()) for r in originals):
        raise ValueError("Baseline differs from retained original settings/instruction")
    common = {"limits": asdict(OllamaConfig()), "tools": sorted(BROWSER_ACTIONS),
              "model_digest": originals[0]["agent"]["local_runtime"]["model_digest"],
              "versions": {p: version(p) for p in ("browser-use", "ollama", "playwright")},
              "model_options": {"think": False, "temperature": 0, "seed": 42,
                                "keep_alive": "5m", "num_ctx": 16384, "num_predict": 2048},
              "harness_hashes": harness_hashes()}
    configs = {}
    for name, policy in (("baseline", ""), ("verification", POLICY)):
        value = {"name": name, "task_instruction": base.instruction,
                 "general_operating_instructions": policy, "common": common,
                 "instruction": base.instruction + (
                     "\n\nGeneral operating instructions:\n" + policy if policy else "")}
        configs[name] = {**value, "sha256": digest(value)}
    # Reuse the existing seeded block scheduler. Control labels are ordering slots
    # only, replaced before dispatch; no scripted trial or result enters this run.
    scheduled = make_manifest(trials=3, seed=1)["schedule"]
    schedule = []
    for spec in scheduled:
        arm = "baseline" if spec["strategy"] == "blind-retry" else "verification"
        seed = SEEDS[spec["repetition"] - 1]
        schedule.append({"trial_id": spec["trial_id"], "scenario": spec["scenario"],
                         "configuration": arm, "data_seed": seed,
                         "block_id": spec["block_id"], "config_hash": configs[arm]["sha256"],
                         "starting_data_hash": digest(seed_data(seed))})
    first = [s["configuration"] for s in schedule[::2]]
    assert first.count("baseline") == first.count("verification") == 3
    return {"kind": "exploratory_real_local_agent_comparison", "version": "1.0.0",
            "scheduler_seed": 1, "data_seeds": list(SEEDS), "configurations": configs,
            "schedule": schedule, "planned_trials": 12,
            "original_hashes": original_hashes(), "provenance": provenance(),
            "cache_conditions": "Long-lived Ollama and prefix cache shared across sequential "
            "trials; no cache flush or timing isolation. Fresh app DB/server/browser/context.",
            "original_diagnosis": {
                "normal": {"business_pass": True, "explicit_done": True,
                           "calls": 12, "done_at_step_ceiling": True,
                           "blocked_model_dispatch": False, "execution_error": None,
                           "note": "SDK final step is done-only; not early completion."},
                "lost_confirmation": "Model labeled submission successful and stated verify "
                "goals but selected Save again; trace has aborted POST then 201 duplicate. "
                "This is observed behavior, not a claim to know internal causation."}}


def termination(raw, config):
    agent = raw.get("agent") or {}
    calls = (agent.get("usage") or {}).get("model_calls")
    done = agent.get("termination_reason") == "done"
    limit = (agent.get("usage") or {}).get("stop_reason")
    error = raw.get("execution_error") or ""
    boundary = isinstance(calls, int) and calls >= config.max_model_calls
    return {"explicit_done": done, "done_at_call_ceiling": done and boundary,
            "call_ceiling_reached": boundary,
            "limit_termination": not done and (boundary or limit == "local_execution_limit"
                or "Timeout" in error),
            "reported_reason": agent.get("termination_reason"), "stop_reason": limit}


def accounting(raw, config):
    usage = (raw.get("agent") or {}).get("usage") or {}
    entries = usage.get("provider_usage") or []
    calls = usage.get("model_calls")
    valid = (isinstance(calls, int) and not isinstance(calls, bool)
             and 0 < calls <= config.max_model_calls and len(entries) == calls
             and usage.get("usage_status") == "measured"
             and usage.get("provider_api_charges_usd") == 0)
    for entry in entries:
        valid = valid and all(isinstance(entry.get(k), int) and not isinstance(entry[k], bool)
                              and entry[k] >= 0 for k in ("prompt_tokens", "completion_tokens"))
        if not valid:
            break
        valid = entry["completion_tokens"] <= config.max_output_tokens
    if not valid:
        return {"status": "unavailable_or_invalid", "model_calls": calls}
    return {"status": "measured", "model_calls": calls,
            **{name: sum(e[field] for e in entries) for name, field in (
                ("input_tokens", "prompt_tokens"), ("output_tokens", "completion_tokens"))},
            "cached_input_tokens": (sum(e["prompt_cached_tokens"] for e in entries)
                if all(isinstance(e.get("prompt_cached_tokens"), int) for e in entries) else None),
            "provider_api_charges_usd": 0, "electricity_hardware_cost": "unmeasured"}


def execute(spec, folder, manifest):
    cfg = manifest["configurations"][spec["configuration"]]
    task = replace(benchmark_task(spec["scenario"], "basic-browser-use"),
                   instruction=cfg["instruction"],
                   starting_data=tuple(seed_data(spec["data_seed"])))
    raw = run_trial(task, select_adapter("ollama"), OllamaConfig(), folder / "evidence")
    if not raw.get("execution_error"):
        import psutil

        evidence = folder / "evidence/browser-evidence"
        if not zipfile.is_zipfile(evidence / "trace.zip"):
            raw["execution_error"] = "evidence:MissingBrowserTrace"
            return raw
        history = json.loads((evidence / "browser-history.json").read_text())
        port = urlsplit(history["history"][0]["state"]["url"]).port
        listeners = [c for c in psutil.net_connections(kind="tcp")
                     if c.status == "LISTEN" and c.laddr.port == port]
        workers = [p.pid for p in psutil.process_iter(["name", "cmdline"])
                   if p.info["name"].lower() in {"python.exe", "python"}
                   and "lab.agent_worker" in (p.info["cmdline"] or [])]
        browsers = [p.pid for p in psutil.process_iter(["name", "cmdline"])
                    if p.info["name"].lower() in {"chrome.exe", "headless_shell.exe"}
                    and any(v.startswith("--user-data-dir=") and
                            "browser-agent-lab-local-" in v for v in p.info["cmdline"] or [])]
        if listeners or workers or browsers:
            raw["execution_error"] = "cleanup:RemainingTrialResources"
        if (raw["limits"] != cfg["common"]["limits"] or raw["framework_version"] != "0.13.11"
                or raw["agent"]["local_runtime"]["model_digest"] != cfg["common"]["model_digest"]):
            raw["execution_error"] = "adapter:FrozenConfigurationMismatch"
    return raw


def run_comparison(output, executor=None):
    manifest = prepare_manifest()
    mocked = executor is not None
    if mocked and getattr(executor, "kind", None) != "mocked_adapter_test":
        raise ValueError("Injected executors must be labeled mocked_adapter_test")
    if mocked:
        manifest["kind"] = "mocked_adapter_test"
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / "manifest.json", manifest)
    state = {"state": "running", "started": [], "stop_reason": None,
             "manifest_sha256": digest(manifest)}
    for spec in manifest["schedule"]:
        folder = output / "trials" / spec["trial_id"]
        folder.mkdir(parents=True)
        atomic_json(folder / "comparison.json", {**spec, "state": "not_started"})
    atomic_json(output / "state.json", state)
    try:
        for spec in manifest["schedule"]:
            if (harness_hashes() != manifest["configurations"]["baseline"]["common"][
                    "harness_hashes"]
                    or original_hashes() != manifest["original_hashes"]
                    or digest(json.loads((output / "manifest.json").read_text()))
                    != state["manifest_sha256"]):
                state.update(state="stopped", stop_reason="FrozenSourceOrOriginalEvidenceChanged")
                break
            folder = output / "trials" / spec["trial_id"]
            record = {**spec, "state": "running"}
            atomic_json(folder / "comparison.json", record)
            state["started"].append(spec["trial_id"])
            atomic_json(output / "state.json", state)
            print(f"START {spec['trial_id']} {spec['scenario']} "
                  f"{spec['configuration']} data_seed={spec['data_seed']}", flush=True)
            try:
                raw = (executor or execute)(spec, folder, manifest)
                if raw.get("kind") != ("mocked_adapter_test" if mocked else
                                        "real_local_ai_agent_trial"):
                    raise ValueError("Trial kind mismatch")
                metrics = accounting(raw, OllamaConfig())
                record.update(state="completed", evaluation=raw.get("evaluation"),
                              execution_error=raw.get("execution_error"),
                              termination=termination(raw, OllamaConfig()), metrics=metrics,
                              duration_seconds=raw.get("duration_seconds"),
                              driver_duration_seconds=raw.get("driver_duration_seconds"),
                              final_agent_message=(raw.get("agent") or {}).get(
                                  "final_agent_message"),
                              evidence="evidence/result.json")
                if raw.get("execution_error") or metrics["status"] != "measured":
                    state.update(state="stopped", stop_reason="InfrastructureOrAccountingProblem")
                if not valid_evaluation(raw):
                    record.update(evaluation=None, execution_error="evaluator:InvalidEvaluation")
                    state.update(state="stopped", stop_reason="MissingOrInvalidEvaluation")
            except KeyboardInterrupt:
                record.update(state="interrupted", execution_error="infrastructure:Interrupted")
                state.update(state="stopped", stop_reason="Interrupted")
            except Exception as exc:
                record.update(state="failed",
                              execution_error=f"infrastructure:{type(exc).__name__}")
                state.update(state="stopped", stop_reason="InfrastructureProblem")
            atomic_json(folder / "comparison.json", record)
            atomic_json(output / "state.json", state)
            print(f"END {spec['trial_id']} {record.get('evaluation')} "
                  f"{record.get('termination')}", flush=True)
            analyze(output)
            if state["state"] == "stopped":
                break
        else:
            state["state"] = "finished"
    finally:
        state["original_evidence_unchanged"] = original_hashes() == manifest["original_hashes"]
        atomic_json(output / "state.json", state)
        summary = analyze(output)
    return summary


def describe(values):
    values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    bootstrap = (sorted(statistics.mean(sample) for sample in
                        itertools.product(values, repeat=len(values))) if 0 < len(values) <= 3
                 else [])
    interval = ([bootstrap[max(0, math.ceil(.025 * len(bootstrap)) - 1)],
                 bootstrap[math.ceil(.975 * len(bootstrap)) - 1]] if bootstrap else None)
    return {"n": len(values), "total": sum(values) if values else None,
            "mean": statistics.mean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "min": min(values) if values else None, "max": max(values) if values else None,
            "bootstrap95_mean": interval,
            "uncertainty_note": "Exact percentile bootstrap of sample means (n<=3). "
            "Tiny/constant samples can give degenerate intervals; not proof of stability. "
            "Observed range is descriptive, not a confidence interval."}


def analyze(output):
    manifest = json.loads((output / "manifest.json").read_text())
    state = json.loads((output / "state.json").read_text())
    if state["state"] == "running":
        state = {**state, "state": "incomplete_or_interrupted"}
    trials = [json.loads((output / "trials" / s["trial_id"] / "comparison.json").read_text())
              for s in manifest["schedule"]]
    groups = []
    for condition in ("normal", "lost-confirmation"):
        for arm in ("baseline", "verification"):
            planned = [t for t in trials if t["scenario"] == condition
                       and t["configuration"] == arm]
            started = [t for t in planned if t["state"] != "not_started"]
            evaluated = [t for t in started if valid_evaluation(t)]
            term = [t for t in started if t.get("termination")]
            group = {"condition": condition, "configuration": arm, "planned": len(planned),
                     "started": len(started), "evaluated": len(evaluated),
                     "business_completion": rate(sum(t["evaluation"]["passed"] for t in evaluated),
                                                 len(evaluated)),
                     "duplicates": rate(sum("duplicate_customer" in t["evaluation"]["issues"]
                                            for t in evaluated), len(evaluated)),
                     "explicit_done": rate(sum(t["termination"]["explicit_done"] for t in term),
                                           len(term)),
                     "limit_termination": rate(sum(t["termination"]["limit_termination"]
                                               for t in term), len(term)),
                     "done_at_call_ceiling": sum(t["termination"]["done_at_call_ceiling"]
                                                 for t in term),
                     "missing_termination": len(started) - len(term),
                     "infrastructure_errors": sum(bool(t.get("execution_error")) for t in started)}
            group["measurements"] = {k: describe([(t.get("metrics") or {}).get(k)
                                                 for t in started]) for k in (
                "model_calls", "input_tokens", "output_tokens", "cached_input_tokens")}
            group["measurements"]["duration_seconds"] = describe(
                [t.get("duration_seconds") for t in started])
            groups.append(group)
    pairs = []
    for condition in ("normal", "lost-confirmation"):
        for seed in SEEDS:
            rows = {t["configuration"]: t for t in trials if t["scenario"] == condition
                    and t["data_seed"] == seed and t.get("evaluation")}
            if len(rows) == 2:
                pairs.append({"condition": condition, "data_seed": seed,
                              "verification_minus_baseline": int(rows["verification"][
                                  "evaluation"]["passed"]) - int(rows["baseline"][
                                      "evaluation"]["passed"])})
    summary = {"kind": manifest["kind"], "state": state, "groups": groups,
               "trials": trials, "paired_business_differences": pairs,
               "cache_conditions": manifest["cache_conditions"],
               "uncertainty": "Wilson 95% per-arm binary intervals; only three matched seeds. "
               "Exploratory, not proof of reliability or timing isolation. No scripted controls.",
               "provider_api_charges_usd": 0, "electricity_hardware_cost": "unmeasured"}
    atomic_json(output / "summary.json", summary)
    (output / "report.html").write_text(render_html(summary, manifest), encoding="utf-8")
    return summary


def render_html(summary, manifest):
    def esc(value):
        return html.escape(str(value), quote=True)

    def binary(value):
        interval = value["wilson95"]
        return (f"{value['numerator']}/{value['denominator']}; Wilson 95% "
                + (f"[{interval[0]:.1%}, {interval[1]:.1%}]" if interval else "unavailable"))

    rows = []
    for g in summary["groups"]:
        cells = [g["condition"], g["configuration"], f"{g['started']}/{g['planned']}",
                 *(binary(g[k]) for k in ("business_completion", "duplicates", "explicit_done",
                                         "limit_termination")), g["done_at_call_ceiling"],
                 json.dumps(g["measurements"])]
        rows.append("<tr>" + "".join("<td>" + esc(c) + "</td>" for c in cells) + "</tr>")
    evidence = []
    for t in summary["trials"]:
        path = "trials/" + t["trial_id"] + "/"
        evidence.append(f"<li>{esc(t['trial_id'])} {esc(t['scenario'])} "
                        f"{esc(t['configuration'])}, seed {t['data_seed']}: {esc(t['state'])}; "
                        f"{esc(t.get('evaluation'))}; {esc(t.get('termination'))} "
                        f"<a href='{path}comparison.json'>record</a> "
                        f"<a href='{path}evidence/result.json'>DB grade/final response/usage</a> "
                        f"<a href='{path}evidence/browser-evidence/browser-history.json'>"
                        "actions</a> "
                        f"<a href='{path}evidence/browser-evidence/trace.zip'>trace</a></li>")
    return ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
            "style-src 'unsafe-inline'\"><title>Local recovery comparison</title>"
            "<style>body{font:14px system-ui;margin:2rem}td,th{border:1px solid #aaa;"
            "padding:.5rem;vertical-align:top}table{border-collapse:collapse}pre{white-space:pre-wrap}"
            "</style><h1>Exploratory local recovery comparison</h1>"
            f"<p>Report kind: {esc(summary['kind'])}</p>"
            f"<p>{esc(summary['state'])}</p><p>{esc(summary['uncertainty'])}</p>"
            f"<p>{esc(summary['cache_conditions'])}</p><p>Provider API charges $0; "
            "electricity/hardware unmeasured. Calls are attempts; token counters are native. "
            "Durations include cleanup. Done and done-at-ceiling are separate "
            "from blocked limits.</p>"
            "<p><a href='manifest.json'>Frozen instructions, hashes, seeds and ordering</a> | "
            "<a href='summary.json'>Structured summary</a></p>"
            "<h2>Original trial diagnosis (unchanged originals)</h2>"
            f"<pre>{esc(json.dumps(manifest['original_diagnosis'], indent=2))}</pre>"
            "<h2>Frozen configurations</h2>"
            f"<pre>{esc(json.dumps(manifest['configurations'], indent=2))}</pre>"
            "<h2>Per-condition comparison</h2><table><tr>"
            "<th>Condition</th><th>Configuration</th><th>Started/planned</th>"
            "<th>Business completion</th><th>Duplicates</th><th>Explicit done</th>"
            "<th>Limit termination</th><th>Done at call ceiling</th><th>Calls/tokens/duration</th>"
            "</tr>" + "".join(rows) + "</table><h2>Matched business differences</h2>"
            f"<pre>{esc(json.dumps(summary['paired_business_differences'], indent=2))}</pre>"
            "<h2>Individual evidence in execution order</h2><ol>" + "".join(evidence)
            + "</ol></html>")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--analyze", type=Path)
    args = parser.parse_args()
    if args.analyze:
        analyze(args.analyze)
        return 0
    if not args.output:
        parser.error("Provide a new --output directory; exactly 12 local trials are scheduled")
    summary = run_comparison(args.output)
    print(f"Report: {args.output / 'report.html'}")
    return 0 if summary["state"]["state"] == "finished" else 2


if __name__ == "__main__":
    raise SystemExit(main())
