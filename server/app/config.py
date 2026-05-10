import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / "server" / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env.enterprise", override=False)


def _csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    def __init__(self) -> None:
        runtime_dir = Path(os.getenv("SERVER_RUNTIME_DIR", "server/runtime"))
        self.app_name = os.getenv("SERVER_APP_NAME", "TradingAgents Cloud API")
        self.api_prefix = os.getenv("SERVER_API_PREFIX", "/api")
        self.runtime_dir = runtime_dir
        self.results_dir = Path(
            os.getenv("TRADINGAGENTS_RESULTS_DIR", str(runtime_dir / "logs"))
        )
        self.cache_dir = Path(
            os.getenv("TRADINGAGENTS_CACHE_DIR", str(runtime_dir / "cache"))
        )
        self.memory_log_path = Path(
            os.getenv(
                "TRADINGAGENTS_MEMORY_LOG_PATH",
                str(runtime_dir / "memory" / "trading_memory.md"),
            )
        )
        self.max_workers = int(os.getenv("SERVER_MAX_WORKERS", "1"))
        self.cors_origins = _csv(os.getenv("SERVER_CORS_ORIGINS"), ["*"])
        self.api_key = os.getenv("TRADINGAGENTS_API_KEY") or None

        self.default_llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.default_quick_model = os.getenv("QUICK_THINK_LLM", "gpt-5.4-mini")
        self.default_deep_model = os.getenv("DEEP_THINK_LLM", "gpt-5.4")
        self.default_backend_url = os.getenv("LLM_BACKEND_URL") or None
        self.default_output_language = os.getenv(
            "TRADINGAGENTS_OUTPUT_LANGUAGE", "Chinese"
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.memory_log_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
