"""Opt-in real SDK/browser smoke test with a completely mocked model (no provider calls)."""

import asyncio
import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LAB_TEST_BROWSER_USE") != "1",
    reason="Optional SDK smoke: set LAB_TEST_BROWSER_USE=1 after installing the agent extra",
)


def test_mocked_sdk_browser_and_independent_grade(tmp_path, monkeypatch):
    from lab.adapters import AgentConfig
    from lab.agent_run import run_trial
    from lab.agent_worker import BROWSER_ACTIONS, browser_tools, run
    from lab.tasks import customer_task

    for name in ("ANONYMIZED_TELEMETRY", "BROWSER_USE_CLOUD_SYNC", "BROWSER_USE_VERSION_CHECK"):
        monkeypatch.setenv(name, "false")
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("BROWSER_USE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "mock-key-not-a-credential")

    import anthropic
    import browser_use
    import browser_use.llm.anthropic.chat as chat_module
    from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

    def no_provider(*args, **kwargs):
        raise AssertionError("Provider network calls are forbidden in this mocked test")

    monkeypatch.setattr(anthropic, "AsyncAnthropic", no_provider)
    monkeypatch.setattr(chat_module, "AsyncAnthropic", no_provider)

    class MockModel:
        model = "mock-model"
        provider = "anthropic"
        name = model
        calls = 0

        async def ainvoke(self, messages, output_format=None, **kwargs):
            self.calls += 1
            # No creation occurs: the agent's claim must not pass the DB grader.
            return ChatInvokeCompletion(
                completion=output_format.model_validate({
                    "evaluation_previous_goal": "Mocked", "memory": "Mocked",
                    "next_goal": "Done", "action": [
                        {"done": {"text": "Mocked success claim", "success": True}}],
                }),
                usage=ChatInvokeUsage(
                    prompt_tokens=100, completion_tokens=20, total_tokens=120,
                    prompt_cached_tokens=None, prompt_cache_creation_tokens=None,
                    prompt_image_tokens=None,
                ),
            )

    mock_model = MockModel()
    monkeypatch.setattr(browser_use, "ChatAnthropic", lambda **kwargs: mock_model)
    assert set(browser_tools().registry.registry.actions) == BROWSER_ACTIONS
    real_agent = browser_use.Agent

    def checked_agent(**kwargs):
        agent = real_agent(**kwargs)
        assert set(agent.tools.registry.registry.actions) <= BROWSER_ACTIONS
        assert agent.settings.use_judge is False
        return agent

    monkeypatch.setattr(browser_use, "Agent", checked_agent)
    monkeypatch.chdir(tmp_path)

    class SDKMockAdapter:
        kind = "mocked_adapter_test"

        def execute(self, request, config, output):
            return asyncio.run(run(request, config))

    config = AgentConfig("anthropic", "mock-model", 2, 45, 2, 200000,
                         80000, 1024, 1, 3, 15)
    result = run_trial(customer_task("normal"), SDKMockAdapter(), config, tmp_path / "trial")
    assert result["execution_error"] is None, result
    assert result["agent"]["agent_claimed_success"] is True
    assert result["evaluation"]["passed"] is False
    assert result["trial_status"] == "business_fail"
    assert mock_model.calls == 1
    assert result["agent"]["usage"]["provider_usage"][0]["total_tokens"] == 120


def test_mocked_ollama_sdk_trace_and_independent_grade(tmp_path, monkeypatch):
    """Real pinned SDK and Chromium, mocked Ollama HTTP; never local AI evidence."""
    import json
    import zipfile

    import httpx

    from lab.adapters import OllamaConfig
    from lab.agent_run import run_trial
    from lab.agent_worker import run
    from lab.tasks import benchmark_task

    for name in ("ANONYMIZED_TELEMETRY", "BROWSER_USE_CLOUD_SYNC", "BROWSER_USE_VERSION_CHECK"):
        monkeypatch.setenv(name, "false")
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("BROWSER_USE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    import lab.ollama_model as local

    real_model = local.LocalModel

    def respond(request):
        assert request.url.host == "127.0.0.1"
        return httpx.Response(200, json={
            "model": "qwen3:8b-q4_K_M", "done": True, "done_reason": "stop",
            "prompt_eval_count": 30, "eval_count": 20,
            "message": {"role": "assistant", "content": json.dumps({
                "evaluation_previous_goal": "Mocked", "memory": "Mocked",
                "next_goal": "Done", "action": [
                    {"done": {"text": "Mocked claim only", "success": True}}],
            })},
        })

    monkeypatch.setattr(local, "LocalModel", lambda cfg, progress, evidence: real_model(
        cfg, progress, evidence, httpx.MockTransport(respond)))

    class MockLocalAdapter:
        kind = "mocked_adapter_test"

        def execute(self, request, config, output):
            return asyncio.run(run(request, config))

    report = run_trial(benchmark_task("normal", "basic-browser-use"), MockLocalAdapter(),
                       OllamaConfig(), tmp_path / "trial")
    assert report["execution_error"] is None, report
    assert report["agent"]["agent_claimed_success"] is True
    assert report["evaluation"]["passed"] is False
    assert report["agent"]["usage"]["provider_usage"][0]["total_tokens"] == 50
    assert zipfile.is_zipfile(tmp_path / "evidence" / "trace.zip")
    assert (tmp_path / "evidence" / "browser-history.json").is_file()


@pytest.mark.parametrize("scenario", ["normal", "lost-confirmation"])
@pytest.mark.parametrize("feedback_variant", [None, "A", "B"])
def test_guarded_sdk_writes_with_mocked_model(tmp_path, monkeypatch, scenario, feedback_variant):
    """Real SDK/CDP browser; mocked Ollama responses, not real-agent results."""
    import json
    import re

    import httpx

    from lab.adapters import GuardConfig, GuardFeedbackConfig
    from lab.agent_run import run_trial
    from lab.agent_worker import run
    from lab.tasks import benchmark_task

    for name in ("ANONYMIZED_TELEMETRY", "BROWSER_USE_CLOUD_SYNC", "BROWSER_USE_VERSION_CHECK"):
        monkeypatch.setenv(name, "false")
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("BROWSER_USE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    import lab.ollama_model as local

    real_model = local.LocalModel
    calls = []

    def respond(request):
        body = json.loads(request.content)
        text = "\n".join(str(m.get('content', '')) for m in body['messages'])
        calls.append(body)
        if len(calls) == 1:
            actions = []
            for key, value in [('name', 'Nimal Silva'), ('email', 'nimal@example.test'),
                               ('company', 'Evergreen Farms')]:
                matches = re.findall(r'\[(\d+)\][^\n]*\bid=["\x27]?' + key + r'\b', text)
                assert matches, text[-8000:]
                actions.append({'input': {'index': int(matches[-1]), 'text': value}})
        elif len(calls) == 2:
            matches = re.findall(r'\[(\d+)\][^\n]*<button[^\n]*', text)
            assert matches, text[-8000:]
            actions = [{'click': {'index': int(matches[-1])}}]
        else:
            actions = [{'done': {'text': 'Mock success claim', 'success': True}}]
        return httpx.Response(200, json={
            'model': 'qwen3:8b-q4_K_M', 'done': True, 'done_reason': 'stop',
            'prompt_eval_count': 30, 'eval_count': 20,
            'message': {'role': 'assistant', 'content': json.dumps({
                'evaluation_previous_goal': 'Mocked', 'memory': 'Mocked',
                'next_goal': 'Mocked', 'action': actions})}})

    monkeypatch.setattr(local, 'LocalModel', lambda cfg, progress, evidence: real_model(
        cfg, progress, evidence, httpx.MockTransport(respond)))

    class MockAdapter:
        kind = 'mocked_adapter_test'

        def execute(self, request, config, output):
            return asyncio.run(run(request, config))

    config = (GuardFeedbackConfig(feedback_variant=feedback_variant) if feedback_variant
              else GuardConfig())
    result = run_trial(benchmark_task(scenario, 'basic-browser-use'), MockAdapter(),
                       config, tmp_path / 'trial')
    assert result['execution_error'] is None, result
    assert result['evaluation']['passed'] is True, result
    assert result['agent']['recovery_guard']['unresolved'] == (scenario == 'lost-confirmation')
    assert result['agent']['agent_claimed_success'] == (scenario == 'normal')
    assert len(calls) == 3
    assert 'Recovery guard' in str(calls[-1]['messages'])
    from lab.guard_feedback import CLARIFICATION
    delivered = '\n'.join(str(message['content']) for message in calls[-1]['messages'])
    assert (CLARIFICATION in delivered) == (
        scenario == 'lost-confirmation' and feedback_variant == 'B')
