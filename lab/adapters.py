"""Small execution boundary; this module has no database/grader access."""

import json
import math
import os
import signal
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit


@dataclass(frozen=True)
class AgentRequest:
    url: str
    instruction: str

    def __post_init__(self):
        parsed = urlsplit(self.url)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
                or parsed.username or parsed.password or parsed.path not in {"", "/"}
                or parsed.query or parsed.fragment or not parsed.port):
            raise ValueError("Agent target must be the runner's loopback CRM origin")


@dataclass(frozen=True)
class AgentConfig:
    provider: str
    model: str
    max_steps: int
    timeout_seconds: float
    max_model_calls: int
    max_total_tokens: int
    max_input_tokens: int
    max_output_tokens: int
    max_cost_usd: float
    input_usd_per_million: float
    output_usd_per_million: float

    def __post_init__(self):
        if self.provider != "anthropic" or not self.model.strip():
            raise ValueError("Explicit provider=anthropic and model are required")
        for name, value in asdict(self).items():
            if name in {"provider", "model"}:
                continue
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
            if name.startswith("max_") and name != "max_cost_usd" and not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if self.max_total_tokens < self.max_input_tokens + self.max_output_tokens:
            raise ValueError("Token budget must cover at least one complete call reservation")
        if self.call_cost > self.max_cost_usd:
            raise ValueError("USD budget must cover at least one complete call reservation")

    @property
    def call_cost(self):
        return (self.max_input_tokens * self.input_usd_per_million
                + self.max_output_tokens * self.output_usd_per_million) / 1_000_000

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        types = {
            "provider": str, "model": str, "max_steps": int, "timeout_seconds": float,
            "max_model_calls": int, "max_total_tokens": int, "max_input_tokens": int,
            "max_output_tokens": int, "max_cost_usd": float,
            "input_usd_per_million": float, "output_usd_per_million": float,
        }
        values = {}
        for name, convert in types.items():
            key = "LAB_AGENT_" + name.upper()
            if not env.get(key, "").strip():
                raise ValueError(f"Missing {key}")
            try:
                values[name] = convert(env[key])
            except ValueError:
                raise ValueError(f"Invalid {key}") from None
        config = cls(**values)
        if not env.get("ANTHROPIC_API_KEY", "").strip():
            raise ValueError("Missing ANTHROPIC_API_KEY")
        return config


@dataclass(frozen=True)
class OllamaConfig:
    provider: str = "ollama"
    model: str = "qwen3:8b-q4_K_M"
    endpoint: str = "http://127.0.0.1:11434"
    context_tokens: int = 16384
    concurrency: int = 1
    max_steps: int = 12
    timeout_seconds: float = 300
    max_model_calls: int = 12
    max_output_tokens: int = 2048

    def __post_init__(self):
        if (self.provider != "ollama" or self.model != "qwen3:8b-q4_K_M"
                or self.endpoint != "http://127.0.0.1:11434"):
            raise ValueError("Local adapter requires the approved loopback endpoint and model")
        for key, ceiling in {"context_tokens": 16384, "concurrency": 1,
                             "max_steps": 12, "max_model_calls": 12,
                             "max_output_tokens": 2048}.items():
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= ceiling:
                raise ValueError(f"Invalid local {key}")
        if self.context_tokens != 16384 or self.concurrency != 1:
            raise ValueError("Local context/concurrency must be 16384/1")
        if (isinstance(self.timeout_seconds, bool) or not math.isfinite(self.timeout_seconds)
                or not 0 < self.timeout_seconds <= 300):
            raise ValueError("Local duration must be positive and at most 300 seconds")


@dataclass(frozen=True)
class GuardConfig(OllamaConfig):
    recovery_guard: str = "visible-write-v1"

    def __post_init__(self):
        super().__post_init__()
        if self.recovery_guard != "visible-write-v1":
            raise ValueError("Unsupported recovery guard")


@dataclass(frozen=True)
class GuardFeedbackConfig(GuardConfig):
    feedback_variant: str = "A"

    def __post_init__(self):
        super().__post_init__()
        if self.feedback_variant not in {"A", "B"}:
            raise ValueError("Feedback variant must be A or B")


class Adapter(Protocol):
    kind: str

    def execute(self, request: AgentRequest, config: AgentConfig | OllamaConfig,
                output: Path) -> dict: ...


def redact_credentials(value):
    """Redact decoded values before JSON encoding, including escaped characters."""
    secret = os.environ.get("ANTHROPIC_API_KEY", "")
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, dict):
        return {redact_credentials(k): redact_credentials(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_credentials(item) for item in value]
    return value


def stop_process(process):
    """Bounded cleanup; POSIX workers have their own process group."""
    if os.name == "nt":
        if process.poll() is None:
            try:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                pass  # Still kill/reap the worker below if tree cleanup fails.
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=10)


def worker_environment(folder: Path, local=False):
    # No inherited DB URLs, fault settings, provider overrides, proxies or other secrets.
    names = ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "TMPDIR", "LOCALAPPDATA",
             "USERPROFILE", "HOME", "PLAYWRIGHT_BROWSERS_PATH", "XDG_CACHE_HOME",
             "HF_HOME", "TORCH_HOME", "CUDA_CACHE_PATH", "PIP_CACHE_DIR", "UV_CACHE_DIR")
    env = {key: os.environ[key] for key in names if key in os.environ}
    env.update({
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        "PYTHON_DOTENV_DISABLED": "1", "ANONYMIZED_TELEMETRY": "false",
        "BROWSER_USE_CLOUD_SYNC": "false", "BROWSER_USE_VERSION_CHECK": "false",
        "BROWSER_USE_CONFIG_DIR": str(folder / "sdk-config"),
        "BROWSER_USE_LOGGING_LEVEL": "critical",
    })
    if not local:
        env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
    else:
        env["OLLAMA_NO_CLOUD"] = "1"
    return env


def supervised_worker(payload, config, folder, command=None):
    """Only safe request/config cross the worker boundary; stdout is never recorded."""
    command = command or [sys.executable, "-m", "lab.agent_worker"]
    process = subprocess.Popen(
        command, cwd=folder, env=worker_environment(folder, isinstance(config, OllamaConfig)),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=os.name != "nt",
    )
    try:
        try:
            process.communicate(json.dumps(payload).encode(), timeout=config.timeout_seconds)
        except subprocess.TimeoutExpired:
            progress = folder / "worker-progress.json"
            return {"execution_error": "limit:ExecutionTimeout",
                    "final_agent_message": None, "agent_claimed_success": None,
                    "usage": json.loads(progress.read_text()) if progress.exists() else None}
        result_path = folder / "worker-result.json"
        if not result_path.exists():
            raise RuntimeError("Agent worker exited without a result")
        return json.loads(result_path.read_text(encoding="utf-8"))
    finally:
        stop_process(process)


class BrowserUseAdapter:
    kind = "real_ai_agent_trial"

    def execute(self, request, config, output):
        if not isinstance(config, AgentConfig):
            raise ValueError("Paid adapter requires explicit paid configuration")
        if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
            raise ValueError("Missing ANTHROPIC_API_KEY")
        payload = {"request": asdict(request), "config": asdict(config)}
        # Profile, SDK scratch files and raw worker results never become report artifacts.
        with tempfile.TemporaryDirectory(prefix="browser-agent-lab-") as directory:
            result = supervised_worker(payload, config, Path(directory))
        return redact_credentials(result)


def select_adapter(name: str) -> Adapter:
    if name == "browser-use":
        return BrowserUseAdapter()
    if name == "ollama":
        return OllamaAdapter()
    if name == "ollama-guard":
        return OllamaGuardAdapter()
    raise ValueError("Unknown adapter; supported: browser-use, ollama, ollama-guard")


class OllamaAdapter:
    kind = "real_local_ai_agent_trial"

    def execute(self, request, config, output):
        if not isinstance(config, OllamaConfig):
            raise ValueError("Ollama adapter requires local configuration")
        from lab.ollama_model import local_preflight

        metadata = local_preflight(config)
        payload = {"request": asdict(request), "config": asdict(config)}
        with tempfile.TemporaryDirectory(prefix="browser-agent-lab-local-") as directory:
            folder = Path(directory)
            result = supervised_worker(payload, config, folder)
            # Copy only explicit synthetic browser/model evidence, never profiles/logs.
            import shutil
            evidence = folder / "evidence"
            if evidence.exists():
                shutil.copytree(evidence, output / "browser-evidence")
        result["local_runtime"] = metadata
        return redact_credentials(result)


class OllamaGuardAdapter(OllamaAdapter):
    def execute(self, request, config, output):
        if not isinstance(config, GuardConfig):
            raise ValueError("Guard adapter requires separate GuardConfig")
        return super().execute(request, config, output)
