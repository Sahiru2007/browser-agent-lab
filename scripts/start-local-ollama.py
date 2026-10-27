"""Start only the E: local Ollama server. Never pull models or run inference."""

import json
import os
import socket
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def main():
    if os.name != "nt":
        raise SystemExit("This launcher is for the approved Windows E: installation")
    executable = Path("E:/AI/Ollama/ollama.exe")
    models = Path("E:/AI/OllamaModels")
    profile = Path("E:/AI/Caches/ollama-profile")
    logs = Path("E:/AI/Caches/ollama-server")
    temp = Path("E:/AI/Downloads/Temp")
    if not executable.is_file():
        raise SystemExit("Install the official standalone distribution on E: first")
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            raise SystemExit("Port 11434 is occupied; inspect it without replacing its server")
    except (ConnectionRefusedError, TimeoutError):
        pass
    for path in (models, profile, logs, temp, profile / "AppData/Local",
                 profile / "AppData/Roaming"):
        path.mkdir(parents=True, exist_ok=True)
    # Only this server gets the isolated profile; existing Windows identity/config
    # and the parent's HOME/USERPROFILE remain unchanged.
    env = {k: v for k, v in os.environ.items()
           if not any(marker in k.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD"))}
    env.update({
        "OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_MODELS": str(models),
        "OLLAMA_NO_CLOUD": "1", "OLLAMA_NOPRUNE": "1",
        "OLLAMA_CONTEXT_LENGTH": "16384", "OLLAMA_NUM_PARALLEL": "1",
        "OLLAMA_MAX_LOADED_MODELS": "1", "USERPROFILE": str(profile), "HOME": str(profile),
        "LOCALAPPDATA": str(profile / "AppData/Local"),
        "APPDATA": str(profile / "AppData/Roaming"),
        "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp),
        "XDG_CACHE_HOME": "E:\\AI\\Caches", "CUDA_CACHE_PATH": "E:\\AI\\Caches\\cuda",
    })
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stdout_path, stderr_path = logs / f"{stamp}-stdout.log", logs / f"{stamp}-stderr.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            [str(executable), "serve"], cwd=executable.parent, env=env,
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Ollama exited; inspect {stderr_path}")
            try:
                with opener.open("http://127.0.0.1:11434/api/version", timeout=1) as response:
                    version = json.load(response)
                break
            except (OSError, urllib.error.URLError):
                time.sleep(0.25)
        else:
            raise TimeoutError("Ollama did not become ready")
    except BaseException:
        # This is only the process just created here, never an existing listener.
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        raise
    record = {
        "pid": process.pid, "executable": str(executable), "endpoint": "http://127.0.0.1:11434",
        "version": version, "models": str(models), "profile": str(profile),
        "stdout": str(stdout_path), "stderr": str(stderr_path),
        "cloud_enabled": False, "automatic_pruning": False,
        "model_pull_or_inference_performed": False,
    }
    (logs / "server-startup.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
