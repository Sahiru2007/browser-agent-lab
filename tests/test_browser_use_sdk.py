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
