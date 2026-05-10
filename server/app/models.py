from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .tickers import normalize_ticker as normalize_ticker_symbol


ANALYST_OPTIONS = ("market", "social", "news", "fundamentals")
PROVIDER_OPTIONS = (
    "openai",
    "google",
    "anthropic",
    "xai",
    "deepseek",
    "qwen",
    "glm",
    "openrouter",
    "azure",
    "ollama",
)
LANGUAGE_OPTIONS = (
    "Chinese",
    "English",
    "Japanese",
    "Korean",
    "Spanish",
    "Portuguese",
    "French",
    "German",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=32)
    trade_date: date
    analysts: list[str] = Field(default_factory=lambda: list(ANALYST_OPTIONS))
    research_depth: int = Field(1, ge=1, le=5)
    llm_provider: str | None = None
    quick_think_llm: str | None = None
    deep_think_llm: str | None = None
    backend_url: str | None = None
    output_language: str | None = None
    checkpoint_enabled: bool = False
    data_vendors: dict[str, str] | None = None
    tool_vendors: dict[str, str] | None = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return normalize_ticker_symbol(value)

    @field_validator("analysts")
    @classmethod
    def validate_analysts(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            key = item.strip().lower()
            if key not in ANALYST_OPTIONS:
                raise ValueError(f"Unsupported analyst: {item}")
            if key not in cleaned:
                cleaned.append(key)
        if not cleaned:
            raise ValueError("At least one analyst must be selected")
        return cleaned

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, value: str | None) -> str | None:
        if value is None:
            return value
        provider = value.strip().lower()
        if provider not in PROVIDER_OPTIONS:
            raise ValueError(f"Unsupported LLM provider: {value}")
        return provider


class AnalysisResult(BaseModel):
    decision: str
    final_trade_decision: str
    reports: dict[str, str] = Field(default_factory=dict)
    state_log_path: str | None = None


class AnalysisJob(BaseModel):
    id: str
    status: JobStatus
    request: AnalysisRequest
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: AnalysisResult | None = None


class OptionsResponse(BaseModel):
    analysts: tuple[str, ...]
    providers: tuple[str, ...]
    languages: tuple[str, ...]
    defaults: dict[str, Any]
    ticker_aliases: dict[str, str] = Field(default_factory=dict)
