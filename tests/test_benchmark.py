"""Engine tests use explicitly mocked outcomes, plus actual isolated HTTP controls."""

import json
from dataclasses import asdict

import pytest

from lab.adapters import AgentConfig
from lab.benchmark import (
    analyze,
    atomic_json,
    evidence_link,
    main,
    make_manifest,
    render_html,
    run_benchmark,
)
from lab.benchmark_metrics import aggregate, trial_metrics, wilson
from lab.database import make_engine, snapshot, sqlite_url
from lab.tasks import benchmark_task, customer_task


@pytest.fixture
def agent_config():
    return AgentConfig("anthropic", "mocked-model", 2, 10, 2, 100000,
                       40000, 1024, 1, 3, 15)


class MockExecutor:
    kind = "mocked_adapter_test"

    def __init__(self, outcomes=None):
        self.outcomes = outcomes or []
        self.folders = []

    def __call__(self, spec, folder, manifest):
        index = len(self.folders)
        self.folders.append(folder)
        outcome = self.outcomes[index] if index < len(self.outcomes) else "pass"
        if outcome == "interrupt":
            raise KeyboardInterrupt()
        if outcome == "error":
            raise RuntimeError("Do not persist raw provider error or credential")
        evaluation = {"passed": outcome == "pass", "issues": [] if outcome == "pass"
                      else ["duplicate_customer"]}
        raw = {"kind": self.kind, "evaluation": evaluation, "execution_error": None,
               "agent": {"final_agent_message": "<script>alert('mock')</script>", "usage": {
                   "model_calls": 1, "provider_usage": [
                       {"prompt_tokens": 100, "completion_tokens": 20,
                        "prompt_cached_tokens": 0}], "reserved_cost_usd": 0.2}}}
        (folder / "evidence").mkdir()
        atomic_json(folder / "evidence/result.json", raw)
        return raw, "evidence/result.json"


def test_schedule_is_seeded_and_paired():
    a = make_manifest(trials=4, seed=17)
    b = make_manifest(tuple(reversed(("normal", "lost-confirmation"))),
                      ("verify", "blind-retry"), trials=4, seed=17)
    assert a["schedule"] == b["schedule"]
    assert a["schedule"] != make_manifest(trials=4, seed=18)["schedule"]
    assert len(a["schedule"]) == 16
    for block in {row["block_id"] for row in a["schedule"]}:
        assert {row["strategy"] for row in a["schedule"] if row["block_id"] == block} == {
            "verify", "blind-retry"}


@pytest.mark.parametrize("kwargs", [
    {"trials": 0}, {"strategies": ["checkpoint"]}, {"scenarios": []},
    {"strategies": ["verify", "verify"]}, {"transport": "remote"},
])
def test_invalid_manifest(kwargs):
    with pytest.raises(ValueError):
        make_manifest(**kwargs)


def test_neutral_task_is_versioned_without_changing_old_task():
    neutral = benchmark_task("normal", "basic-browser-use")
    recovery = benchmark_task("normal", "verification-browser-use")
    assert neutral.version == recovery.version == "1.1.0"
    assert "search" not in neutral.instruction
    assert "search" in recovery.instruction
    assert neutral.expected_customer == recovery.expected_customer
    assert customer_task("normal").version == "1.0.0"


def test_mocked_results_errors_denominators_and_offline_rebuild(tmp_path):
    manifest = make_manifest(trials=2)
    executor = MockExecutor(["pass", "duplicate", "error"])
    root = tmp_path / "benchmark"
    summary = run_benchmark(manifest, root, executor=executor)
    assert all(t["kind"] == "mocked_adapter_test" for t in summary["trials"])
    assert len(set(executor.folders)) == 8
    assert sum(g["started"] for g in summary["groups"]) == 8
    assert sum(g["evaluated"] for g in summary["groups"]) == 7
    assert sum(g["operational_success"]["numerator"] for g in summary["groups"]) == 6
    assert sum(g["duplicate_action_rate"]["numerator"] for g in summary["groups"]) == 1
    assert summary["trials"][2]["execution_error"] == "infrastructure:RuntimeError"
    assert "Do not persist" not in (root / "summary.json").read_text()
    assert analyze(root) == summary
    with pytest.raises(FileExistsError):
        run_benchmark(make_manifest(), root, executor=MockExecutor())


def test_interrupted_run_persists_current_and_unstarted_trials(tmp_path):
    root = tmp_path / "run"
    summary = run_benchmark(make_manifest(trials=2), root,
                            executor=MockExecutor(["pass", "interrupt"]))
    assert summary["state"] == "interrupted"
    assert [t["state"] for t in summary["trials"]][:3] == [
        "completed", "interrupted", "scheduled"]
    assert len(list(root.glob("trials/*/result.json"))) == 8
    assert sum(g["started"] for g in summary["groups"]) == 2
    assert sum(g["missing_evaluations"] for g in summary["groups"]) == 1
    assert (root / "report.html").exists()


def test_abrupt_interruption_and_missing_record_are_not_silently_dropped(tmp_path):
    root = tmp_path / "run"
    run_benchmark(make_manifest(), root, executor=MockExecutor())
    path = root / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["state"] = "running"
    atomic_json(path, manifest)
    trial = root / "trials/trial-000001/result.json"
    trial.unlink()
    summary = analyze(root)
    assert summary["state"] == "incomplete_or_interrupted"
    assert summary["trials"][0]["state"] == "missing"
    assert sum(g["started"] for g in summary["groups"]) == 4
    assert "Trial JSON unavailable" in (root / "report.html").read_text()


def test_budget_admission_and_no_implicit_paid_execution(tmp_path, agent_config):
    manifest = make_manifest(strategies=["basic-browser-use"], trials=2,
                             config=agent_config, max_cost_usd=1)
    with pytest.raises(ValueError, match="allow-paid"):
        run_benchmark(manifest, tmp_path / "forbidden")
    executor = MockExecutor(["error"])
    summary = run_benchmark(manifest, tmp_path / "mocked", executor=executor)
    assert len(executor.folders) == 1
    assert summary["reserved_run_cost_usd"] == 1
    assert sum(t["state"] == "not_run_budget" for t in summary["trials"]) == 3
    assert summary["trials"][0]["metrics"]["model_calls"]["status"] == "unknown"


def test_unknown_usage_partial_coverage_and_estimated_cost(agent_config):
    limits = asdict(agent_config)
    partial = {"agent": {"usage": {"model_calls": 2, "provider_usage": [
        {"prompt_tokens": 100, "completion_tokens": 20, "prompt_cached_tokens": None}],
        "reserved_cost_usd": 0.5}}}
    measured = trial_metrics(partial, 1, "mocked_adapter_test", limits)
    assert measured["model_calls"]["value"] == 2
    assert measured["input_tokens"]["status"] == "unknown"
    assert measured["input_tokens"]["known_subtotal"] == 100
    assert measured["estimated_cost_usd"]["value"] is None
    assert measured["estimated_cost_usd"]["known_subtotal"] == pytest.approx(0.0006)
    partial["agent"]["usage"]["model_calls"] = 1
    full = trial_metrics(partial, 2, "mocked_adapter_test", limits)
    assert full["total_tokens"]["value"] == 120
    assert full["estimated_cost_usd"]["status"] == "estimated"
    assert full["estimated_cost_usd"]["value"] == pytest.approx(0.0006)
    assert full["cached_input_tokens"]["status"] == "unknown"
    controls = trial_metrics({}, 1, "scripted_http_control", None)
    assert controls["model_calls"]["status"] == "unavailable"
    assert controls["model_calls"]["value"] is None


def test_wilson_known_values_and_empty_samples():
    assert wilson(0, 0) is None
    assert wilson(5, 10) == pytest.approx([0.236593, 0.763407], abs=1e-6)
    assert wilson(0, 10)[1] == pytest.approx(0.277533, abs=1e-6)
    assert wilson(10, 10)[0] == pytest.approx(0.722467, abs=1e-6)
    assert aggregate([]) == []


def test_report_escapes_messages_links_evidence_and_labels(tmp_path):
    root = tmp_path / "run"
    summary = run_benchmark(make_manifest(), root, executor=MockExecutor())
    page = render_html(summary)
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert "Wilson 95%" in page
    assert "mocked_adapter_test" in page
    assert "unknown" in page and "unavailable" in page
    assert "Checkpoint recovery is not implemented" in page
    for trial in summary["trials"]:
        assert (root / evidence_link(trial, trial["evidence"])).is_file()
    for unsafe in ("../../outside", "https://example.com", "evidence/../outside", "evidence/x:y"):
        with pytest.raises(ValueError):
            evidence_link(summary["trials"][0], unsafe)


def test_cli_refuses_paid_execution_before_config(monkeypatch):
    monkeypatch.setattr("sys.argv", ["benchmark", "--strategy", "basic-browser-use"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_actual_http_trials_have_independent_database_state_and_servers(tmp_path):
    root = tmp_path / "http"
    summary = run_benchmark(make_manifest(transport="http", trials=2), root)
    databases = list(root.glob("trials/*/evidence/*/trial.db"))
    assert len(databases) == 8
    pids = set()
    for trial in summary["trials"]:
        raw_path = root / evidence_link(trial, trial["evidence"])
        raw = json.loads(raw_path.read_text())
        assert raw["control_behaved_as_expected"]
        assert raw["before"]["events"] == []
        engine = make_engine(sqlite_url(raw_path.parent / "trial.db"))
        try:
            assert snapshot(engine) == raw["after"]
        finally:
            engine.dispose()
        log = (raw_path.parent / "server.log").read_text()
        pids.add(log.split("Started server process [")[1].split("]")[0])
    assert len(pids) == 8
    duplicate_groups = [g for g in summary["groups"] if g["strategy"] == "blind-retry"
                        and g["scenario"] == "lost-confirmation"]
    assert duplicate_groups[0]["duplicate_action_rate"]["value"] == 1


def test_control_driver_error_still_gets_independent_evaluation(tmp_path, monkeypatch):
    import lab.run as controls

    original = controls.drive_http

    def fail_after_commit(url, case):
        original(url, case)
        raise RuntimeError("mock driver failure")

    monkeypatch.setattr(controls, "drive_http", fail_after_commit)
    result = controls.run_case(None, controls.CASES[0], tmp_path, "http")
    assert result["execution_error"] == "driver:RuntimeError"
    assert result["evaluation"]["passed"] is True
    assert not result["control_behaved_as_expected"]


def test_execution_error_and_business_outcome_remain_independent(tmp_path):
    class FailedAfterEffects(MockExecutor):
        def __call__(self, *args):
            raw, evidence = super().__call__(*args)
            raw["execution_error"] = "adapter:MockedErrorAfterEffects"
            return raw, evidence

    summary = run_benchmark(make_manifest(), tmp_path / "run", executor=FailedAfterEffects())
    for group in summary["groups"]:
        assert group["operational_success"]["value"] == 0
        assert group["business_success"]["value"] == 1
        assert group["execution_errors"] == group["started"]


def test_manifest_matches_checked_in_schema():
    from lab.app import ROOT

    manifest = make_manifest()
    schema = json.loads((ROOT / "docs/benchmark-manifest-v1.schema.json").read_text())
    assert set(schema["required"]) <= manifest.keys()
    assert manifest["schema_version"] == schema["properties"]["schema_version"]["const"]
    item = schema["properties"]["schedule"]["items"]
    for spec in manifest["schedule"]:
        assert set(item["required"]) <= spec.keys()
        for field, rule in item["properties"].items():
            if "enum" in rule:
                assert spec[field] in rule["enum"]


def test_offline_cli_does_not_execute_or_load_credentials(tmp_path, monkeypatch):
    root = tmp_path / "run"
    run_benchmark(make_manifest(), root, executor=MockExecutor())

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline analysis must not load provider credentials")

    monkeypatch.setattr(AgentConfig, "from_env", forbidden)
    monkeypatch.setattr("sys.argv", ["benchmark", "--analyze", str(root)])
    assert main() == 0


def test_interruption_closes_actual_trial_server(tmp_path, monkeypatch):
    import lab.run as controls

    manifest = make_manifest(scenarios=["normal"], strategies=["verify"], transport="http")
    original = controls.subprocess.Popen
    processes = []

    def capture(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        return process

    def interrupt(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(controls.subprocess, "Popen", capture)
    monkeypatch.setattr(controls, "drive_http", interrupt)
    summary = run_benchmark(manifest, tmp_path / "interrupted-http")
    assert summary["state"] == "interrupted"
    assert summary["trials"][0]["evaluation"] is None
    assert len(processes) == 1 and processes[0].poll() is not None


@pytest.mark.parametrize("calls", [False, 0.0, -1, "0"])
def test_invalid_call_counts_do_not_manufacture_measured_zero_usage(calls):
    raw = {"agent": {"usage": {"model_calls": calls, "provider_usage": []}}}
    values = trial_metrics(raw, 1, "mocked_adapter_test")
    for name in ("model_calls", "input_tokens", "output_tokens", "total_tokens"):
        assert values[name]["status"] == "unknown"
        assert values[name]["value"] is None


@pytest.mark.parametrize("evaluation", [
    {"passed": "true", "issues": []},
    {"passed": True, "issues": ["duplicate_customer"]},
    {"passed": False, "issues": []},
    {"passed": False, "issues": [123]},
])
def test_malformed_evaluation_never_becomes_a_success(tmp_path, evaluation):
    class MalformedExecutor(MockExecutor):
        def __call__(self, *args):
            raw, evidence = super().__call__(*args)
            raw["evaluation"] = evaluation
            return raw, evidence

    summary = run_benchmark(make_manifest(scenarios=["normal"], strategies=["verify"]),
                            tmp_path / "run", executor=MalformedExecutor())
    record = summary["trials"][0]
    assert record["execution_error"] == "evaluator:InvalidEvaluation"
    assert record["evaluation"] is None
    assert summary["groups"][0]["operational_success"]["numerator"] == 0
    assert summary["groups"][0]["business_success"]["denominator"] == 0
