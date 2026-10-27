"""Private subprocess entrypoint; no task assertions, faults or DB modules imported."""

import asyncio
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from lab.adapters import AgentConfig, AgentRequest, GuardConfig, OllamaConfig, redact_credentials

# Positive list: no evaluate/JS, extract (another LLM), search engine, files or uploads.
BROWSER_ACTIONS = frozenset({
    "done", "navigate", "go_back", "wait", "click", "input", "scroll", "send_keys",
    "switch", "close", "dropdown_options", "select_dropdown", "find_text",
})


class BudgetExceeded(RuntimeError):
    pass


class BudgetedModel:
    def __init__(self, model, config, progress=None):
        self.inner = model
        self.config = config
        self.model = model.model
        self.provider = model.provider
        self.name = model.name
        self.model_name = model.model
        self.calls = 0
        self.reserved_tokens = 0
        self.reserved_usd = 0.0
        self.usage = []
        self.stop_reason = None
        self.progress = progress

    def checkpoint(self):
        if self.progress:
            temporary = self.progress.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.summary()), encoding="utf-8")
            temporary.replace(self.progress)

    async def ainvoke(self, messages, output_format=None, **kwargs):
        cfg = self.config
        if self.stop_reason:
            raise BudgetExceeded(self.stop_reason)
        # Conservative text-size heuristic, NOT a provider tokenizer/billing guarantee.
        size = sum(len(m.model_dump_json().encode()) for m in messages) + 8192
        if output_format is not None:
            size += len(json.dumps(output_format.model_json_schema()).encode())
        tokens = cfg.max_input_tokens + cfg.max_output_tokens
        if (size > cfg.max_input_tokens or self.calls >= cfg.max_model_calls
                or self.reserved_tokens + tokens > cfg.max_total_tokens
                or self.reserved_usd + cfg.call_cost > cfg.max_cost_usd + 1e-12):
            self.stop_reason = "model_budget_exhausted"
            self.checkpoint()
            raise BudgetExceeded(self.stop_reason)
        # Reserve before dispatch, including calls that fail or return unknown usage.
        self.calls += 1
        self.reserved_tokens += tokens
        self.reserved_usd += cfg.call_cost
        self.checkpoint()
        try:
            result = await self.inner.ainvoke(messages, output_format=output_format, **kwargs)
        except (Exception, asyncio.CancelledError):
            # Failed/canceled requests can still be billed. Keep the reservation
            # and forbid another dispatch when actual usage is unavailable.
            self.stop_reason = "provider_error_usage_unknown"
            self.checkpoint()
            raise
        if result.usage is None:
            self.stop_reason = "usage_unavailable"
        else:
            usage = result.usage.model_dump(mode="json")
            self.usage.append(usage)
            if (usage["prompt_tokens"] > cfg.max_input_tokens
                    or usage["completion_tokens"] > cfg.max_output_tokens):
                self.stop_reason = "provider_usage_exceeded_estimate"
        self.checkpoint()
        return result

    def summary(self):
        return {"model_calls": self.calls, "reserved_tokens": self.reserved_tokens,
                "reserved_cost_usd": self.reserved_usd, "provider_usage": self.usage,
                "stop_reason": self.stop_reason}


def browser_tools(guard=None):
    from browser_use import Tools

    if guard is None:
        tools = Tools()
    else:
        from lab.recovery_guard import guarded_tools
        tools = guarded_tools(guard)
    actions = tools.registry.registry.actions
    if not BROWSER_ACTIONS <= actions.keys():
        raise RuntimeError("Pinned Browser Use tool API changed")
    for name in list(actions):
        if name not in BROWSER_ACTIONS:
            del actions[name]
    return tools


def validate_browser_tools(tools):
    if set(tools.registry.registry.actions) - BROWSER_ACTIONS:
        raise RuntimeError("SDK registered tools outside the browser-only policy")


def save_local_history(history, evidence):
    import shutil

    data = history.model_dump()
    for i, step in enumerate(data.get("history", [])):
        state = step.get("state", {})
        path = state.get("screenshot_path")
        if path and Path(path).is_file():
            target = f"step-{i:02d}.png"
            shutil.copyfile(path, evidence / target)
            state["screenshot_path"] = target
        for action in step.get("result", []):
            if action.get("error"):
                action["error"] = "SDK action/model error (raw details suppressed)"
    (evidence / "browser-history.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


async def run(request, config):
    from browser_use import Agent, Browser, ChatAnthropic
    from playwright.async_api import async_playwright

    # Resolve installed Playwright browser; never attach to a user's existing profile.
    async with async_playwright() as playwright:
        executable = playwright.chromium.executable_path
    local = isinstance(config, OllamaConfig)
    browser = Browser(
        headless=True, executable_path=executable, user_data_dir=str(Path.cwd() / "profile"),
        use_cloud=False, keep_alive=local, allowed_domains=[request.url],
        enable_default_extensions=False, accept_downloads=False, permissions=[],
    )
    local = isinstance(config, OllamaConfig)
    evidence = Path("evidence")
    if local:
        evidence.mkdir(exist_ok=True)
        from lab.ollama_model import LocalModel

        model = LocalModel(config, Path("worker-progress.json"), evidence)
    else:
        model = BudgetedModel(ChatAnthropic(
            model=config.model, api_key=os.environ["ANTHROPIC_API_KEY"],
            max_tokens=config.max_output_tokens, max_retries=0,
            timeout=min(config.timeout_seconds, 60),
            base_url="https://api.anthropic.com",
        ), config, Path("worker-progress.json"))
    result = {"framework_version": version("browser-use"), "final_agent_message": None,
              "agent_claimed_success": None, "execution_error": None, "usage": None}
    agent = None
    guard = None
    trace_driver = trace_context = observed = None
    try:
        if local:
            await browser.start()
            trace_driver = await async_playwright().start()
            observed = await trace_driver.chromium.connect_over_cdp(browser.cdp_url)
            trace_context = observed.contexts[0]
            await trace_context.tracing.start(screenshots=True, snapshots=True, sources=False)
            if isinstance(config, GuardConfig):
                from lab.recovery_guard import RecoveryGuard
                guard = RecoveryGuard(request.url, trace_context, evidence / "guard-events.jsonl")
                await guard.install()
        agent = Agent(
            task=f"CRM URL: {request.url}\n{request.instruction}", llm=model,
            browser=browser, tools=browser_tools(guard), use_vision=False,
            fallback_llm=None, page_extraction_llm=model,
            use_judge=False, calculate_cost=False, message_compaction=False,
            enable_planning=False, enable_signal_handler=False,
            available_file_paths=[], file_system_path=str(Path.cwd() / "scratch"),
            display_files_in_done_text=False, final_response_after_failure=False,
            max_failures=1, max_actions_per_step=3,
            llm_timeout=max(1, int(config.timeout_seconds if local
                                       else min(config.timeout_seconds, 60))),
            step_timeout=max(1, int(config.timeout_seconds)),
        )
        validate_browser_tools(agent.tools)
        history = await asyncio.wait_for(agent.run(max_steps=config.max_steps),
                                         timeout=config.timeout_seconds)
        result["final_agent_message"] = history.final_result()
        result["agent_claimed_success"] = history.is_successful()
        result["steps_recorded"] = len(history.history)
        result["termination_reason"] = "done" if history.is_done() else "steps_exhausted_or_stopped"
        # Browser Use can catch model errors internally. Preserve their existence,
        # without leaking raw SDK/provider error strings into reports.
        if history.errors() and any(history.errors()):
            if local and not any("infrastructure_error" in e for e in model.entries):
                result["task_failure"] = "model:AgentActionOrResponseFailure"
            else:
                result["execution_error"] = "adapter:BrowserUseHistoryError"
    except Exception as exc:
        result["execution_error"] = f"adapter:{type(exc).__name__}"
    finally:
        if guard is not None:
            result["recovery_guard"] = guard.finish()
            if guard.error:
                result["execution_error"] = "guard:" + guard.error
        if local:
            try:
                if agent is not None:
                    save_local_history(agent.history, evidence)
                if trace_context:
                    await asyncio.wait_for(trace_context.tracing.stop(
                        path=str(evidence / "trace.zip")), timeout=10)
            except Exception:
                result["execution_error"] = "evidence:TraceSaveError"
            finally:
                try:
                    if observed:
                        await asyncio.wait_for(observed.close(), timeout=5)
                except Exception:
                    result["execution_error"] = "cleanup:TraceObserverCleanupError"
                finally:
                    if trace_driver:
                        try:
                            await asyncio.wait_for(trace_driver.stop(), timeout=5)
                        except Exception:
                            result["execution_error"] = "cleanup:TraceDriverCleanupError"
        try:
            await asyncio.wait_for(browser.kill(), timeout=10)
            if local:
                await asyncio.sleep(0.1)
        except Exception:
            result["execution_error"] = "cleanup:BrowserCleanupError"
        result["usage"] = model.summary()
        if model.stop_reason and not result["execution_error"]:
            if local and model.stop_reason == "local_execution_limit":
                result["task_failure"] = "limit:" + model.stop_reason
            else:
                result["execution_error"] = "limit:" + model.stop_reason
    return result


def main():
    payload = json.loads(sys.stdin.buffer.read())
    result = {}
    try:
        result = asyncio.run(run(AgentRequest(**payload["request"]),
                                 (GuardConfig if payload["config"].get("recovery_guard") else
                                  OllamaConfig if payload["config"].get("provider") == "ollama"
                                  else AgentConfig)(**payload["config"])))
    except Exception as exc:
        result = {"execution_error": f"adapter:{type(exc).__name__}"}
    text = json.dumps(redact_credentials(result))
    Path("worker-result.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
