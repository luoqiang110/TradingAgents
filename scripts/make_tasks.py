"""Cross-platform task runner behind the project Makefile."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import config_upgrade


ROOT = Path(__file__).resolve().parents[1]
DEV_DIR = ROOT / ".make"
API_PID = DEV_DIR / "api.pid"
FRONT_PID = DEV_DIR / "front.pid"
PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.12")
VENV_DIR = ROOT / os.getenv("VENV_DIR", ".venv")
IS_WINDOWS = os.name == "nt"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")


def exe(name: str) -> str:
    if IS_WINDOWS and shutil.which(f"{name}.cmd"):
        return f"{name}.cmd"
    return name


UV = os.getenv("UV", exe("uv"))
NPM = os.getenv("NPM", exe("npm"))
DOCKER = os.getenv("DOCKER", exe("docker"))


HELP = """Development Commands:
  make setup           - Interactive setup wizard (recommended for new users)
  make doctor          - Check configuration and system requirements
  make config          - Generate local config files (aborts if config already exists)
  make config-upgrade  - Merge new fields from config.example.yaml into config.yaml
  make check           - Check if all required tools are installed
  make install         - Install all dependencies (frontend + backend + pre-commit hooks)
  make setup-sandbox   - Pre-pull sandbox container image (recommended)
  make dev             - Start all services in development mode (with hot-reloading)
  make dev-daemon      - Start dev services in background (daemon mode)
  make start           - Start all services in production mode (optimized, no hot-reloading)
  make start-daemon    - Start prod services in background (daemon mode)
  make stop            - Stop all running services
  make clean           - Clean up processes and temporary files"""


def run(cmd: list[str], **kwargs) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, **kwargs)


def require_tool(command: str, label: str | None = None) -> None:
    if shutil.which(command) is None:
        name = label or command
        raise SystemExit(f"missing: {name}")


def docker_compose(*args: str) -> list[str]:
    return [
        DOCKER,
        "compose",
        "--env-file",
        "server/.env",
        "-f",
        "server/docker-compose.prod.yml",
        *args,
    ]


def ensure_uv() -> None:
    if shutil.which(UV) is None:
        raise SystemExit(
            "missing: uv. Install it first: "
            "https://docs.astral.sh/uv/getting-started/installation/"
        )


def ensure_venv_ready() -> None:
    if not VENV_PYTHON.exists():
        raise SystemExit("missing: .venv. Run: make install")
    result = subprocess.run(
        [str(VENV_PYTHON), "-c", "import uvicorn"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise SystemExit(f"missing: uvicorn in {VENV_PYTHON}. Run: make install")


def task_help() -> None:
    print(HELP)


def task_check() -> None:
    ensure_uv()
    require_tool(NPM, "npm")
    require_tool(DOCKER, "docker")
    subprocess.run([DOCKER, "compose", "version"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    print("ok: required tools are installed")


def task_doctor() -> None:
    print("Checking TradingAgents configuration...")
    task_check()
    print("ok: .env exists" if (ROOT / ".env").exists() else "warn: .env missing; run make config")
    print(
        "ok: server/.env exists"
        if (ROOT / "server/.env").exists()
        else "warn: server/.env missing; run make config"
    )
    print(
        f"ok: virtualenv python found at {VENV_PYTHON}"
        if VENV_PYTHON.exists()
        else "warn: virtualenv missing; run make install"
    )
    for path in ("front/package.json", "server/docker-compose.prod.yml"):
        full = ROOT / path
        if not full.exists():
            raise SystemExit(f"missing: {path}")
        print(f"ok: {path} found")
    aliases_path = ROOT / "server/app/data/a_share_aliases.json"
    data = json.loads(aliases_path.read_text(encoding="utf-8"))
    print(f"ok: ticker alias data loaded ({len(data.get('aliases', {}))} aliases)")
    print("Doctor finished.")


def task_config() -> None:
    if (ROOT / ".env").exists() or (ROOT / "server/.env").exists():
        raise SystemExit("Config already exists (.env or server/.env). Aborting.")
    shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
    shutil.copyfile(ROOT / "server/.env.example", ROOT / "server/.env")
    print("Created .env and server/.env. Fill in API keys and domain settings before production deployment.")


def task_config_upgrade() -> None:
    config_upgrade.append_missing(ROOT / ".env.example", ROOT / ".env")
    config_upgrade.append_missing(ROOT / "server/.env.example", ROOT / "server/.env")


def task_install() -> None:
    ensure_uv()
    run([UV, "venv", str(VENV_DIR), "--python", PYTHON_VERSION, "--allow-existing"])
    run([UV, "pip", "install", "--python", str(VENV_PYTHON), "-e", ".", "-r", "server/requirements.txt"])
    if (ROOT / "front/package-lock.json").exists():
        run([NPM, "--prefix", "front", "ci"])
    else:
        run([NPM, "--prefix", "front", "install"])
    if (ROOT / ".pre-commit-config.yaml").exists() or (ROOT / ".pre-commit-config.yml").exists():
        run([UV, "pip", "install", "--python", str(VENV_PYTHON), "pre-commit"])
        run([str(VENV_PYTHON), "-m", "pre_commit", "install"])
    else:
        print("skip: no pre-commit config found")


def task_setup_sandbox() -> None:
    require_tool(DOCKER, "docker")
    for image in ("python:3.12-slim", "node:22-alpine", "nginx:1.27-alpine", "certbot/certbot:latest"):
        run([DOCKER, "pull", image])


def task_setup() -> None:
    print("TradingAgents setup wizard")
    task_check()
    if not (ROOT / ".env").exists() and not (ROOT / "server/.env").exists():
        task_config()
    else:
        print("Config files already exist; skipping make config.")
    if input("Install frontend/backend dependencies now? [Y/n] ").strip().lower() not in {"n", "no"}:
        task_install()
    if input("Pre-pull Docker images for production deployment? [Y/n] ").strip().lower() not in {"n", "no"}:
        task_setup_sandbox()
    print("Setup complete. Edit .env and server/.env, then run make dev or make start-daemon.")


def start_process(cmd: list[str], log_path: Path | None = None) -> subprocess.Popen:
    print("+", " ".join(cmd))
    popen_kwargs = {}
    if not IS_WINDOWS:
        popen_kwargs["start_new_session"] = True
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handle = log_path.open("a", encoding="utf-8")
        return subprocess.Popen(cmd, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, **popen_kwargs)
    return subprocess.Popen(cmd, cwd=ROOT, **popen_kwargs)


def task_dev() -> None:
    ensure_venv_ready()
    DEV_DIR.mkdir(exist_ok=True)
    print(f"Starting API on http://localhost:{BACKEND_PORT} and frontend on http://localhost:{FRONTEND_PORT}")
    api = start_process(
        [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "server.app.main:app",
            "--host",
            BACKEND_HOST,
            "--port",
            BACKEND_PORT,
            "--reload",
        ]
    )
    front = start_process([NPM, "--prefix", "front", "run", "dev", "--", "--port", FRONTEND_PORT])
    try:
        while True:
            if api.poll() is not None:
                raise SystemExit(api.returncode)
            if front.poll() is not None:
                raise SystemExit(front.returncode)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping dev services...")
    finally:
        terminate_process(api.pid)
        terminate_process(front.pid)


def task_dev_daemon() -> None:
    ensure_venv_ready()
    DEV_DIR.mkdir(exist_ok=True)
    api = start_process(
        [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "server.app.main:app",
            "--host",
            BACKEND_HOST,
            "--port",
            BACKEND_PORT,
            "--reload",
        ],
        DEV_DIR / "api.log",
    )
    front = start_process(
        [NPM, "--prefix", "front", "run", "dev", "--", "--port", FRONTEND_PORT],
        DEV_DIR / "front.log",
    )
    API_PID.write_text(str(api.pid), encoding="utf-8")
    FRONT_PID.write_text(str(front.pid), encoding="utf-8")
    print("Dev services started in background.")
    print(f"API log: {DEV_DIR / 'api.log'}")
    print(f"Frontend log: {DEV_DIR / 'front.log'}")


def terminate_process(pid: int) -> None:
    if pid <= 0:
        return
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def stop_pid_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        terminate_process(int(path.read_text(encoding="utf-8").strip()))
    finally:
        path.unlink(missing_ok=True)


def task_start() -> None:
    run(docker_compose("up", "--build"))


def task_start_daemon() -> None:
    run(docker_compose("up", "-d", "--build"))
    print("Production services started. Frontend/API are behind nginx on ports 80 and 443.")


def task_stop() -> None:
    stop_pid_file(API_PID)
    stop_pid_file(FRONT_PID)
    subprocess.run(docker_compose("down"), cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Stopped running services.")


def task_clean() -> None:
    task_stop()
    shutil.rmtree(DEV_DIR, ignore_errors=True)
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
    for path in ROOT.rglob("*.pyc"):
        path.unlink(missing_ok=True)
    print("Cleaned temporary files.")


TASKS = {
    "help": task_help,
    "setup": task_setup,
    "doctor": task_doctor,
    "config": task_config,
    "config-upgrade": task_config_upgrade,
    "check": task_check,
    "install": task_install,
    "setup-sandbox": task_setup_sandbox,
    "dev": task_dev,
    "dev-daemon": task_dev_daemon,
    "start": task_start,
    "start-daemon": task_start_daemon,
    "stop": task_stop,
    "clean": task_clean,
}


def main() -> int:
    task = sys.argv[1] if len(sys.argv) > 1 else "help"
    if task not in TASKS:
        print(f"Unknown task: {task}", file=sys.stderr)
        print(HELP)
        return 2
    try:
        TASKS[task]()
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
