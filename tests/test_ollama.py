"""Mocked local-provider tests: no Ollama inference or paid calls."""

import asyncio
import json
import sys
from dataclasses import replace

import httpx
import pytest

from lab.adapters import OllamaAdapter, OllamaConfig, select_adapter, supervised_worker
from lab.agent_worker import BudgetExceeded


def test_local_selection_and_no_credentials(monkeypatch, tmp_path):
    from lab.adapters import worker_environment

    monkeypatch.setenv("ANTHROPIC_API_KEY", "never-forward")
    monkeypatch.setenv("OLLAMA_API_KEY", "never-forward")
    monkeypatch.setenv("HTTP_PROXY", "http://untrusted.test")
    assert isinstance(select_adapter("ollama"), OllamaAdapter)
    env = worker_environment(tmp_path, local=True)
    assert not any("KEY" in k or "PROXY" in k for k in env)
    assert env["OLLAMA_NO_CLOUD"] == "1"
    assert OllamaConfig().max_model_calls == 12


@pytest.mark.parametrize("changes", [
    {"endpoint": "http://localhost:11434"}, {"endpoint": "https://ollama.com"},
    {"model": "qwen3:cloud"}, {"provider": "anthropic"}, {"concurrency": 2},
    {"context_tokens": 32768}, {"max_model_calls": 13}, {"timeout_seconds": 301},
    {"max_output_tokens": 4096}, {"max_steps": True},
])
def test_local_settings_fail_closed(changes):
    with pytest.raises(ValueError):
        replace(OllamaConfig(), **changes)


def model_fixture(tmp_path, known=True, invalid=False):
    pytest.importorskip("browser_use")
    from pydantic import BaseModel

    from lab.ollama_model import LocalModel

    class Answer(BaseModel):
        ok: bool

    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert str(request.url) == "http://127.0.0.1:11434/api/chat"
        assert body["options"]["num_ctx"] == 16384
        assert body["options"]["num_predict"] == 2048
        assert body["think"] is False
        response = {"model": "qwen3:8b-q4_K_M", "done": True,
                    "message": {"role": "assistant", "content": (
                        'not JSON' if invalid else '{"ok":true}')}, "done_reason": "stop"}
        if known:
            response.update(prompt_eval_count=30, eval_count=5, prompt_eval_cached_count=2)
        return httpx.Response(200, json=response)

    return LocalModel(OllamaConfig(), tmp_path / "progress.json", tmp_path,
                      httpx.MockTransport(respond)), Answer, requests


@pytest.mark.parametrize("known", [True, False])
def test_native_usage_and_local_call_limit(tmp_path, known):
    model, schema, requests = model_fixture(tmp_path, known=known)

    async def check():
        for _ in range(12):
            result = await model.ainvoke([], output_format=schema)
            assert result.completion.ok is True
        with pytest.raises(BudgetExceeded):
            await model.ainvoke([], output_format=schema)

    asyncio.run(check())
    assert len(requests) == 12
    usage = model.summary()
    assert usage["provider_api_charges_usd"] == 0
    assert usage["electricity_cost"] == "unmeasured"
    assert usage["usage_status"] == ("measured" if known else "unavailable")
    if known:
        assert usage["provider_usage"][0]["total_tokens"] == 35
    else:
        assert usage["provider_usage"][0]["prompt_tokens"] is None


def test_invalid_model_output_retains_native_usage(tmp_path):
    model, schema, requests = model_fixture(tmp_path, invalid=True)
    with pytest.raises(Exception):
        asyncio.run(model.ainvoke([], output_format=schema))
    assert len(requests) == 1
    entry = model.summary()["provider_usage"][0]
    assert entry["model_error"] == "structured_response_invalid"
    assert entry["total_tokens"] == 35


def test_local_dispatch_guard_rejects_redirect_target(tmp_path):
    model, _, _ = model_fixture(tmp_path)
    with pytest.raises(RuntimeError, match="blocked"):
        asyncio.run(model.guard(httpx.Request("POST", "https://ollama.com/api/chat")))


def test_local_timeout_cleans_worker_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = supervised_worker({}, replace(OllamaConfig(), timeout_seconds=0.1), tmp_path,
                               [sys.executable, "-c", "import time; time.sleep(30)"])
    assert result["execution_error"] == "limit:ExecutionTimeout"


def test_local_deadline_blocks_dispatch(tmp_path):
    model, schema, requests = model_fixture(tmp_path)
    model.started -= 301
    with pytest.raises(BudgetExceeded):
        asyncio.run(model.ainvoke([], output_format=schema))
    assert not requests


def test_local_config_cannot_select_paid_adapter(tmp_path):
    from lab.adapters import AgentRequest, BrowserUseAdapter

    with pytest.raises(ValueError, match="Paid adapter"):
        BrowserUseAdapter().execute(AgentRequest("http://127.0.0.1:1234", "Synthetic task"),
                                    OllamaConfig(), tmp_path)


def test_preflight_rejects_remote_listener(monkeypatch):
    from types import SimpleNamespace

    psutil = pytest.importorskip("psutil")
    from lab.ollama_model import local_preflight

    monkeypatch.setattr(psutil, "net_connections", lambda **kwargs: [
        SimpleNamespace(status="LISTEN", laddr=SimpleNamespace(port=11434, ip="0.0.0.0"))])
    with pytest.raises(RuntimeError, match="loopback"):
        local_preflight(OllamaConfig())


def test_local_calls_are_serialized(tmp_path):
    model, schema, _ = model_fixture(tmp_path)
    inner = model.inner.ainvoke
    active = peak = 0

    async def counted(*args, **kwargs):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(.01)
            return await inner(*args, **kwargs)
        finally:
            active -= 1

    model.inner.ainvoke = counted

    async def check():
        await asyncio.gather(*(model.ainvoke([], output_format=schema) for _ in range(3)))

    asyncio.run(check())
    assert peak == 1
    assert model.calls == 3
