from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO
from urllib.error import URLError
from urllib.request import urlopen

from dotenv import dotenv_values, load_dotenv

from app.config.settings import get_settings
from app.db.database import init_db


ROOT_DIR = Path(__file__).resolve().parent
RUN_DIR = ROOT_DIR / ".run"
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE_FILE = ROOT_DIR / ".env.example"


@dataclass
class ManagedProcess:
    name: str
    process: subprocess.Popen[str]
    reader: threading.Thread
    log_path: Path


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def safe_print(message: str) -> None:
    print(message, flush=True)


def ensure_env_file() -> None:
    if ENV_FILE.exists() or not ENV_EXAMPLE_FILE.exists():
        return
    if os.getenv("PORT") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("BOT_TOKEN"):
        return
    shutil.copyfile(ENV_EXAMPLE_FILE, ENV_FILE)
    safe_print("Created .env from .env.example. Update BOT_TOKEN before starting the bot.")


def resolve_python() -> str:
    candidate = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    return str(candidate if candidate.exists() else Path(sys.executable))


def looks_like_bot_token(value: str) -> bool:
    if ":" not in value:
        return False
    left, right = value.split(":", 1)
    return left.isdigit() and len(right) > 10


def stream_output(name: str, stream: TextIO, log_path: Path) -> None:
    with log_path.open("a", encoding="utf-8") as file:
        for line in iter(stream.readline, ""):
            text = line.rstrip()
            if not text:
                continue
            file.write(text + "\n")
            file.flush()
            safe_print(f"[{name}] {text}")


def start_process(name: str, args: list[str], env: dict[str, str]) -> ManagedProcess:
    RUN_DIR.mkdir(exist_ok=True)
    log_path = RUN_DIR / f"{name}.log"
    log_path.write_text("", encoding="utf-8")

    process = subprocess.Popen(
        args,
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdout is not None

    reader = threading.Thread(
        target=stream_output,
        args=(name, process.stdout, log_path),
        daemon=True,
    )
    reader.start()
    return ManagedProcess(name=name, process=process, reader=reader, log_path=log_path)


def stop_process(managed: ManagedProcess) -> None:
    if managed.process.poll() is not None:
        return

    managed.process.terminate()
    try:
        managed.process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        managed.process.kill()
        managed.process.wait(timeout=5)


def wait_for_health(health_url: str, process: ManagedProcess, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.process.poll() is not None:
            return False
        try:
            with urlopen(health_url, timeout=2) as response:
                return response.status == 200
        except (URLError, OSError):
            time.sleep(0.5)
    return False


def build_runtime_env() -> tuple[dict[str, str], str, int, str]:
    ensure_env_file()
    load_dotenv(ENV_FILE, override=False)
    get_settings.cache_clear()
    settings = get_settings()

    values = {key: value for key, value in dotenv_values(ENV_FILE).items() if value is not None}
    env = values.copy()
    env.update(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["BASE_URL"] = settings.base_url

    port = int(os.getenv("PORT", str(settings.app_port)))
    host = "0.0.0.0" if os.getenv("PORT") else settings.app_host
    health_url = f"http://127.0.0.1:{port}/health"

    safe_print(f"Base URL: {settings.base_url}")
    safe_print(f"Bind: http://{host}:{port}")
    database_label = "PostgreSQL via DATABASE_URL" if settings.database_url else str(settings.database_path)
    safe_print(f"Database: {database_label}")

    return env, host, port, health_url


def main() -> int:
    configure_stdio()

    env, host, port, health_url = build_runtime_env()
    init_db()
    settings = get_settings()
    python = resolve_python()

    api_args = [
        python,
        "-m",
        "uvicorn",
        "app.api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if settings.enable_reload and not os.getenv("PORT"):
        api_args.append("--reload")

    managed_processes: list[ManagedProcess] = []
    try:
        api = start_process("api", api_args, env)
        managed_processes.append(api)

        if not wait_for_health(health_url, api):
            safe_print(f"API did not start. Check log: {api.log_path}")
            return 1
        safe_print("API ready.")

        if looks_like_bot_token(settings.bot_token):
            bot = start_process("bot", [python, "-m", "app.bot.main"], env)
            managed_processes.append(bot)
            time.sleep(3)
            if bot.process.poll() is not None:
                safe_print(f"Bot exited too early. Check log: {bot.log_path}")
                return 1
            safe_print("Bot started.")
        else:
            safe_print("BOT_TOKEN is missing. API is running, bot was skipped.")

        safe_print("Press Ctrl+C to stop.")
        while True:
            for managed in managed_processes:
                code = managed.process.poll()
                if code is not None:
                    safe_print(f"Process {managed.name} exited with code {code}")
                    return code or 1
            time.sleep(1)
    except KeyboardInterrupt:
        safe_print("Stopping processes...")
        return 0
    finally:
        for managed in reversed(managed_processes):
            stop_process(managed)


if __name__ == "__main__":
    raise SystemExit(main())
