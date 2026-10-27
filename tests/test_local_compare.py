"""Comparison tests: mocked outcomes are explicitly labeled and never live AI results."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import httpx
import pytest

import lab.local_compare as module
from lab.adapters import OllamaConfig
from lab.agent_run import run_trial
from lab.tasks import benchmark_task


@pytest.fixture
def frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "version", lambda name: "0.13.11")
    monkeypatch.setattr(module, "harness_hashes", lambda: {"mocked-source": "frozen"})
    monkeypatch.setattr(module, "provenance", lambda: {"kind": "mocked_adapter_test"})
    for name in module.ORIGINALS:
        p = tmp_path / "runs" / name
        p.mkdir(parents=True)
        (p / "result.json").write_text(json.dumps({
            "task": {"instruction": benchmark_task("normal", "basic-browser-use").instruction},
            "limits": asdict(OllamaConfig()),
            "agent": {"local_runtime": {"model_digest": "mocked-digest"}}}))
    return tmp_path / "comparison"


def test_frozen_matched_balanced_schedule(frozen):
    a = module.prepare_manifest()
    b = module.prepare_manifest()
    assert a["schedule"] == b["schedule"]
    assert len(a["schedule"]) == 12
    configs = a["configurations"]
    assert configs["baseline"]["common"] == configs["verification"]["common"]
    assert configs["baseline"]["general_operating_instructions"] == ""
    assert configs["baseline"]["instruction"] == configs["verification"]["task_instruction"]
    assert configs["baseline"]["sha256"] != configs["verification"]["sha256"]
    assert not any(s in module.POLICY for s in ("Nimal", "email", "customer", "selector", "fault"))
    first = [r["configuration"] for r in a["schedule"][::2]]
    assert first.count("baseline") == first.count("verification") == 3
    for i in range(0, 12, 2):
        left, right = a["schedule"][i:i + 2]
        assert left["starting_data_hash"] == right["starting_data_hash"]
        assert left["scenario"] == right["scenario"]
        assert left["configuration"] != right["configuration"]
    assert len({module.digest(module.seed_data(s)) for s in module.SEEDS}) == 3


class MockExecutor:
    kind = "mocked_adapter_test"

    def __init__(self, problem=None):
        self.calls = 0
        self.problem = problem

    def __call__(self, spec, folder, manifest):
        self.calls += 1
        if self.problem == "interrupt":
            raise KeyboardInterrupt()
        if self.problem == "raise":
            raise RuntimeError("raw error must not enter report")
        usage = {"model_calls": 1, "usage_status": "measured", "provider_api_charges_usd": 0,
                 "provider_usage": [{"prompt_tokens": 30, "completion_tokens": 5,
                                     "prompt_cached_tokens": 0}]}
        if self.problem == "accounting":
            usage["provider_usage"] = []
        return {"kind": self.kind, "execution_error": (
            "cleanup:MockProblem" if self.problem == "infrastructure" else None),
            "evaluation": {"passed": False, "issues": ["duplicate_customer"]},
            "duration_seconds": 2.0, "driver_duration_seconds": 1.0,
            "agent": {"termination_reason": "done", "final_agent_message": "<script>mock</script>",
                      "usage": usage}}


def test_failures_retained_not_replaced_and_report(frozen):
    executor = MockExecutor()
    summary = module.run_comparison(frozen, executor=executor)
    assert executor.calls == 12
    assert summary["kind"] == "mocked_adapter_test"
    assert summary["state"]["original_evidence_unchanged"]
    assert all(g["duplicates"]["numerator"] == 3 for g in summary["groups"])
    assert all(g["business_completion"]["denominator"] == 3 for g in summary["groups"])
    assert all(g["explicit_done"]["numerator"] == 3 for g in summary["groups"])
    assert all(g["business_completion"]["wilson95"] for g in summary["groups"])
    assert module.analyze(frozen) == summary
    text = (frozen / "report.html").read_text()
    assert "&lt;script&gt;" not in text  # Agent text stays in linked structured evidence.
    assert "<script>" not in text
    assert "Wilson 95%" in text
    assert "scripted controls" in text
    assert len({str(p) for p in (frozen / "trials").iterdir()}) == 12


@pytest.mark.parametrize("problem", ["accounting", "infrastructure", "interrupt", "raise"])
def test_stops_without_replacement_on_problem(frozen, problem):
    executor = MockExecutor(problem)
    summary = module.run_comparison(frozen, executor=executor)
    assert executor.calls == 1
    assert summary["state"]["state"] == "stopped"
    assert sum(t["state"] == "not_started" for t in summary["trials"]) == 11
    assert "raw error must not" not in (frozen / "summary.json").read_text()


def test_done_at_boundary_is_not_aborted_limit():
    raw = {"agent": {"termination_reason": "done", "usage": {"model_calls": 12}}}
    result = module.termination(raw, OllamaConfig())
    assert result["explicit_done"] and result["done_at_call_ceiling"]
    assert not result["limit_termination"]
    raw["agent"]["termination_reason"] = "steps_exhausted_or_stopped"
    assert module.termination(raw, OllamaConfig())["limit_termination"]


@pytest.mark.parametrize("bad", [None, -1, True, 2049])
def test_invalid_accounting_is_not_fabricated(bad):
    raw = MockExecutor()(None, None, None)
    raw["agent"]["usage"]["provider_usage"][0]["completion_tokens"] = bad
    assert module.accounting(raw, OllamaConfig())["status"] == "unavailable_or_invalid"


def test_operator_seed_is_fresh_and_not_forwarded(tmp_path):
    class NoWrite:
        kind = "mocked_adapter_test"

        def execute(self, request, config, output):
            assert set(asdict(request)) == {"url", "instruction"}
            with httpx.Client(base_url=request.url, trust_env=False) as client:
                assert len(client.get("/api/customers").json()) == 2
            return {"agent_claimed_success": True}

    for seed in module.SEEDS:
        task = replace(benchmark_task("normal", "basic-browser-use"),
                       starting_data=tuple(module.seed_data(seed)))
        report = run_trial(task, NoWrite(), OllamaConfig(), tmp_path / str(seed))
        assert report["execution_error"] is None
        assert report["before"]["customers"] == module.seed_data(seed)
        assert report["evaluation"]["passed"] is False
        assert Path(tmp_path / str(seed) / "trial.db").is_file()


def test_continuous_uncertainty_is_explicit():
    result = module.describe([1, 2, 3])
    assert result["bootstrap95_mean"] == [1, 3]
    assert result["n"] == 3
    assert "not proof" in result["uncertainty_note"]


def test_changed_original_evidence_stops_before_dispatch(frozen, monkeypatch):
    original = module.prepare_manifest

    def changed_after_freeze():
        manifest = original()
        monkeypatch.setattr(module, "original_hashes", lambda: {"changed": "evidence"})
        return manifest

    monkeypatch.setattr(module, "prepare_manifest", changed_after_freeze)
    executor = MockExecutor()
    result = module.run_comparison(frozen, executor=executor)
    assert executor.calls == 0
    assert result["state"]["stop_reason"] == "FrozenSourceOrOriginalEvidenceChanged"



def test_malformed_evaluation_stops_and_retains_offline_report(frozen):
    class InvalidGrade(MockExecutor):
        def __call__(self, *args):
            raw = super().__call__(*args)
            raw["evaluation"] = {"passed": True, "issues": ["duplicate_customer"]}
            return raw

    executor = InvalidGrade()
    result = module.run_comparison(frozen, executor=executor)
    assert executor.calls == 1
    assert result["state"]["stop_reason"] == "MissingOrInvalidEvaluation"
    assert result["trials"][0]["evaluation"] is None
    assert result["trials"][0]["execution_error"] == "evaluator:InvalidEvaluation"
    assert sum(g["evaluated"] for g in result["groups"]) == 0
    assert "mocked_adapter_test" in (frozen / "report.html").read_text()
    assert module.analyze(frozen) == result
