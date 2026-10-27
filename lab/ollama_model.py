"""Local-only SDK model wrapper; native accounting never implies electricity cost."""

import asyncio
import json
import time
from dataclasses import asdict
from importlib.metadata import version

import httpx

from lab.agent_worker import BudgetExceeded


def local_preflight(config):
    """Check the actual owned loopback listener and installed model, without inference."""
    import psutil

    listeners = [c for c in psutil.net_connections(kind="tcp")
                 if c.status == "LISTEN" and c.laddr.port == 11434]
    if len(listeners) != 1 or listeners[0].laddr.ip != "127.0.0.1":
        raise RuntimeError("Ollama must listen only on IPv4 loopback")
    process = psutil.Process(listeners[0].pid)
    env = process.environ()
    expected = {"OLLAMA_NO_CLOUD": "1", "OLLAMA_NUM_PARALLEL": "1",
                "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_MODELS": r"E:\AI\OllamaModels"}
    if any(env.get(k) != v for k, v in expected.items()):
        raise RuntimeError("Actual Ollama server storage/cloud/concurrency settings differ")
    with httpx.Client(base_url=config.endpoint, trust_env=False,
                      follow_redirects=False, timeout=5) as client:
        tags = client.get("/api/tags")
        tags.raise_for_status()
        model = next((m for m in tags.json()["models"] if m["name"] == config.model), None)
        if not model or model.get("digest") != (
                "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41"):
            raise RuntimeError("Approved local model/digest is not installed")
        response = client.get("/api/version")
        response.raise_for_status()
    return {"version": response.json()["version"], "ollama_sdk_version": version("ollama"),
            "model_digest": model["digest"],
            "server_pid": process.pid, "executable": process.exe(), "environment": expected}


class LocalModel:
    def __init__(self, config, progress=None, evidence=None, transport=None):
        from browser_use import ChatOllama

        self.config = config
        self.model = self.name = self.model_name = config.model
        self.provider = "ollama"
        self.progress = progress
        self.evidence = evidence
        self.calls = 0
        self.entries = []
        self.stop_reason = None
        self.started = time.monotonic()
        self.lock = asyncio.Lock()
        self.current = None
        self.inner = ChatOllama(
            model=config.model, host=config.endpoint, timeout=config.timeout_seconds,
            client_params={"trust_env": False, "follow_redirects": False,
                           "event_hooks": {"request": [self.guard], "response": [self.capture]},
                           **({"transport": transport} if transport is not None else {})},
            ollama_options={"num_ctx": config.context_tokens,
                            "num_predict": config.max_output_tokens, "think": False,
                            "temperature": 0, "seed": 42, "keep_alive": "5m"},
        )

    async def guard(self, request):
        if str(request.url) != self.config.endpoint + "/api/chat" or request.method != "POST":
            raise RuntimeError("Nonlocal or unexpected model dispatch blocked")
        body = json.loads(request.content)
        if (body.get("model") != self.model or body.get("think") is not False
                or body.get("options", {}).get("num_ctx") != self.config.context_tokens
                or body.get("options", {}).get("num_predict") != self.config.max_output_tokens):
            raise RuntimeError("Local model dispatch settings differ")

    async def capture(self, response):
        await response.aread()
        if not response.is_success:
            self.current["response_status"] = response.status_code
            return
        body = response.json()
        # Native counts, including responses that fail subsequent SDK schema validation.
        self.current.update({
            "prompt_tokens": body.get("prompt_eval_count"),
            "completion_tokens": body.get("eval_count"),
            "prompt_cached_tokens": body.get("prompt_eval_cached_count"),
            "done_reason": body.get("done_reason"),
            "total_duration_ns": body.get("total_duration"),
            "load_duration_ns": body.get("load_duration"),
        })
        if self.evidence:
            (self.evidence / f"model-response-{self.calls:02d}.json").write_text(
                json.dumps({"message": body.get("message"), **self.current}, indent=2),
                encoding="utf-8")

    def checkpoint(self):
        if self.progress:
            tmp = self.progress.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.summary()), encoding="utf-8")
            tmp.replace(self.progress)

    async def ainvoke(self, messages, output_format=None, **kwargs):
        async with self.lock:
            remaining = self.config.timeout_seconds - (time.monotonic() - self.started)
            if self.calls >= self.config.max_model_calls or remaining <= 0 or self.stop_reason:
                self.stop_reason = self.stop_reason or "local_execution_limit"
                self.checkpoint()
                raise BudgetExceeded(self.stop_reason)
            self.calls += 1
            self.current = {"call": self.calls, "usage_status": "unavailable"}
            self.entries.append(self.current)
            self.checkpoint()
            try:
                result = await asyncio.wait_for(
                    self.inner.ainvoke(messages, output_format=output_format, **kwargs), remaining)
                return result
            except BaseException:
                if "done_reason" in self.current:
                    self.current["model_error"] = "structured_response_invalid"
                else:
                    self.current["infrastructure_error"] = "local_provider_error"
                    self.stop_reason = "local_provider_error"
                raise
            finally:
                if all(isinstance(self.current.get(k), int)
                       and not isinstance(self.current[k], bool)
                       and self.current[k] >= 0 for k in ("prompt_tokens", "completion_tokens")):
                    self.current["usage_status"] = "measured"
                    self.current["total_tokens"] = (self.current["prompt_tokens"]
                                                     + self.current["completion_tokens"])
                self.checkpoint()

    def summary(self):
        return {"model_calls": self.calls, "provider_usage": self.entries,
                "usage_status": "measured" if len(self.entries) == self.calls and all(
                    e["usage_status"] == "measured" for e in self.entries) else "unavailable",
                "provider_api_charges_usd": 0, "electricity_cost": "unmeasured",
                "hardware_cost": "unmeasured", "stop_reason": self.stop_reason,
                "effective_settings": asdict(self.config)}
