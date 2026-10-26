"""Mocked adapter/provider tests; never real-agent benchmark results."""

import asyncio
import json
import subprocess
import sys
from dataclasses import asdict, replace
from types import SimpleNamespace

import httpx
import pytest

from lab.adapters import (
    AgentConfig,
    AgentRequest,
    BrowserUseAdapter,
    redact_credentials,
    select_adapter,
    supervised_worker,
    worker_environment,
)
from lab.agent_run import run_trial
from lab.agent_worker import BudgetedModel, BudgetExceeded, validate_browser_tools
from lab.tasks import customer_task


@pytest.fixture
def config():
    return AgentConfig("anthropic", "explicit-test-model", 4, 15, 3, 150000,
                       40000, 1024, 1.0, 3.0, 15.0)


def config_env(config):
    return {"LAB_AGENT_" + k.upper(): str(v) for k, v in asdict(config).items()}


def test_selection_and_missing_credentials(config):
    assert isinstance(select_adapter("browser-use"), BrowserUseAdapter)
    with pytest.raises(ValueError, match="Unknown adapter"):
        select_adapter("mock")
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AgentConfig.from_env(config_env(config))


@pytest.mark.parametrize("field", list(AgentConfig.__dataclass_fields__))
def test_every_configuration_field_is_required(config, field):
    env = {**config_env(config), "ANTHROPIC_API_KEY": "mock-secret"}
    del env["LAB_AGENT_" + field.upper()]
    with pytest.raises(ValueError, match="Missing LAB_AGENT"):
        AgentConfig.from_env(env)


@pytest.mark.parametrize("changes", [
    {"provider": "unknown"}, {"model": ""}, {"max_steps": 0},
    {"timeout_seconds": float("nan")}, {"max_cost_usd": float("inf")},
    {"max_total_tokens": 1}, {"max_cost_usd": 0.001}, {"max_model_calls": 1.5},
])
def test_invalid_limits(config, changes):
    with pytest.raises(ValueError):
        replace(config, **changes)


def test_agent_boundary_and_environment(config, monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "mock-secret")
    monkeypatch.setenv("DATABASE_URL", "private-db")
    monkeypatch.setenv("LAB_FAULT", "lost_confirmation")
    monkeypatch.setenv("OPENAI_API_KEY", "other-secret")
    env = worker_environment(tmp_path)
    assert not {"DATABASE_URL", "LAB_FAULT", "OPENAI_API_KEY"} & env.keys()
    task = customer_task("lost-confirmation")
    request = asdict(AgentRequest("http://127.0.0.1:1234", task.instruction))
    assert set(request) == {"url", "instruction"}
    assert "lost_confirmation" not in json.dumps(request)
    for url in ("https://example.com", "http://127.0.0.1:1234/api/reset"):
        with pytest.raises(ValueError):
            AgentRequest(url, task.instruction)


class MockAdapter:
    kind = "mocked_adapter_test"

    def __init__(self, action):
        self.action = action
        self.url = None

    def execute(self, request, config, output):
        self.url = request.url
        if self.action == "timeout":
            raise subprocess.TimeoutExpired("mock-adapter", 1)
        if self.action == "error":
            raise RuntimeError("mock-secret")
        if self.action == "duplicate":
            with httpx.Client(base_url=request.url, trust_env=False) as client:
                for _ in range(2):
                    response = client.post(
                        "/api/customers", json=customer_task("normal").expected_customer)
                    assert response.status_code == 201
        return {"agent_claimed_success": True, "final_agent_message": "Success mock-secret"}


@pytest.mark.parametrize("action", ["error", "timeout", "claim", "duplicate"])
def test_runner_independently_grades_and_cleans_up(config, tmp_path, monkeypatch, action):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "mock-secret")
    adapter = MockAdapter(action)
    report = run_trial(customer_task("normal"), adapter, config, tmp_path / action)
    assert report["kind"] == "mocked_adapter_test"
    assert report["evaluation"]["passed"] is False
    issue = "duplicate_customer" if action == "duplicate" else "missing_or_incorrect_customer"
    assert issue in report["evaluation"]["issues"]
    assert report["execution_error"] == {
        "error": "adapter:RuntimeError", "timeout": "limit:ExecutionTimeout",
        "claim": None, "duplicate": None,
    }[action]
    assert "mock-secret" not in (tmp_path / action / "result.json").read_text()
    with httpx.Client(trust_env=False, timeout=0.5) as client:
        with pytest.raises((httpx.ConnectError, httpx.ConnectTimeout)):
            client.get(adapter.url + "/api/health")


def test_actual_worker_timeout_cleanup(config, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "mock-secret")
    import lab.adapters as module

    real_popen = subprocess.Popen
    processes = []

    def capture(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(module.subprocess, "Popen", capture)
    result = supervised_worker({}, replace(config, timeout_seconds=0.2), tmp_path,
                               [sys.executable, "-c", "import time; time.sleep(60)"])
    assert result["execution_error"] == "limit:ExecutionTimeout"
    assert processes[0].poll() is not None


def test_worker_error_cleanup(config, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "mock-secret")
    with pytest.raises(RuntimeError, match="without a result"):
        supervised_worker({}, config, tmp_path, [sys.executable, "-c", "raise RuntimeError()"])


class FakeModel:
    model = "explicit-test-model"
    name = model
    provider = "anthropic"

    def __init__(self, usage=None):
        self.usage = usage
        self.calls = 0

    async def ainvoke(self, *args, **kwargs):
        self.calls += 1
        return SimpleNamespace(usage=self.usage)


def test_budget_reserves_before_dispatch_and_blocks_calls(config):
    fake = FakeModel(SimpleNamespace(model_dump=lambda **kwargs: {
        "prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}))
    model = BudgetedModel(fake, replace(config, max_model_calls=1))
    asyncio.run(model.ainvoke([]))
    with pytest.raises(BudgetExceeded):
        asyncio.run(model.ainvoke([]))
    assert fake.calls == 1
    assert model.summary()["reserved_tokens"] == 41024


@pytest.mark.parametrize("limit", ["tokens", "usd", "unknown_usage"])
def test_each_model_budget_stops_further_dispatch(config, limit):
    usage = SimpleNamespace(model_dump=lambda **kwargs: {
        "prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120})
    if limit == "tokens":
        config = replace(config, max_total_tokens=41024)
    elif limit == "usd":
        config = replace(config, max_cost_usd=config.call_cost)
    fake = FakeModel(None if limit == "unknown_usage" else usage)
    model = BudgetedModel(fake, config)
    asyncio.run(model.ainvoke([]))
    with pytest.raises(BudgetExceeded):
        asyncio.run(model.ainvoke([]))
    assert fake.calls == 1


def test_oversized_prompt_never_reaches_provider(config):
    fake = FakeModel()
    model = BudgetedModel(fake, config)
    message = SimpleNamespace(model_dump_json=lambda: "x" * 50000)
    with pytest.raises(BudgetExceeded):
        asyncio.run(model.ainvoke([message]))
    assert fake.calls == 0


def test_live_command_requires_opt_in_before_credentials(monkeypatch):
    from lab.agent_run import main

    monkeypatch.setattr(sys, "argv", ["agent_run", "--adapter", "browser-use"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


@pytest.mark.parametrize("failure", [RuntimeError, asyncio.CancelledError])
def test_failed_provider_call_blocks_further_dispatch(config, tmp_path, failure):
    class FailingModel(FakeModel):
        async def ainvoke(self, *args, **kwargs):
            self.calls += 1
            raise failure()

    fake = FailingModel()
    progress = tmp_path / "progress.json"
    model = BudgetedModel(fake, config, progress)
    with pytest.raises(failure):
        asyncio.run(model.ainvoke([]))
    with pytest.raises(BudgetExceeded, match="provider_error_usage_unknown"):
        asyncio.run(model.ainvoke([]))
    assert fake.calls == 1
    assert model.reserved_tokens == 41024
    assert json.loads(progress.read_text())["stop_reason"] == "provider_error_usage_unknown"


def test_redaction_handles_json_escaped_secrets(monkeypatch):
    secret = 'mock-"secret\\with\nnewlines'
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    result = redact_credentials({"message": "echo " + secret, "nested": [secret]})
    assert result == {"message": "echo [REDACTED]", "nested": ["[REDACTED]"]}
    assert secret not in json.loads(json.dumps(result))["message"]


def test_runtime_tool_validation_rejects_sdk_added_actions():
    tools = SimpleNamespace(registry=SimpleNamespace(
        registry=SimpleNamespace(actions={"done": object(), "evaluate": object()})))
    with pytest.raises(RuntimeError, match="browser-only"):
        validate_browser_tools(tools)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows tree-cleanup fallback")
def test_worker_is_reaped_when_taskkill_fails(monkeypatch):
    from lab.adapters import stop_process

    class Process:
        pid = 12345
        killed = False
        waited = False

        def poll(self):
            return 1 if self.killed else None

        def kill(self):
            self.killed = True

        def wait(self, timeout):
            self.waited = True

    def unavailable(*args, **kwargs):
        raise OSError("mocked taskkill failure")

    monkeypatch.setattr(subprocess, "run", unavailable)
    process = Process()
    stop_process(process)
    assert process.killed and process.waited
