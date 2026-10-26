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


class Adapter(Protocol):
    kind: str

    def execute(self, request: AgentRequest, config: AgentConfig, output: Path) -> dict: ...


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


def worker_environment(folder: Path):
    # No inherited DB URLs, fault settings, provider overrides, proxies or other secrets.
    names = ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "LOCALAPPDATA",
             "USERPROFILE", "HOME", "PLAYWRIGHT_BROWSERS_PATH")
    env = {key: os.environ[key] for key in names if key in os.environ}
    env.update({
        "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        "PYTHON_DOTENV_DISABLED": "1", "ANONYMIZED_TELEMETRY": "false",
        "BROWSER_USE_CLOUD_SYNC": "false", "BROWSER_USE_VERSION_CHECK": "false",
        "BROWSER_USE_CONFIG_DIR": str(folder / "sdk-config"),
        "BROWSER_USE_LOGGING_LEVEL": "critical",
    })
    return env


def supervised_worker(payload, config, folder, command=None):
    """Only safe request/config cross the worker boundary; stdout is never recorded."""
    command = command or [sys.executable, "-m", "lab.agent_worker"]
    process = subprocess.Popen(
        command, cwd=folder, env=worker_environment(folder), stdin=subprocess.PIPE,
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
        if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
            raise ValueError("Missing ANTHROPIC_API_KEY")
        payload = {"request": asdict(request), "config": asdict(config)}
        # Profile, SDK scratch files and raw worker results never become report artifacts.
        with tempfile.TemporaryDirectory(prefix="browser-agent-lab-") as directory:
            result = supervised_worker(payload, config, Path(directory))
        return redact_credentials(result)


def select_adapter(name: str) -> Adapter:
    if name != "browser-use":
        raise ValueError("Unknown adapter; supported: browser-use")
    return BrowserUseAdapter()
