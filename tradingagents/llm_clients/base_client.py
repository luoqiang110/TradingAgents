from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
import warnings
import time
import random


def normalize_content(response):
    """Normalize LLM response content to a plain string.

    Multiple providers (OpenAI Responses API, Google Gemini 3) return content
    as a list of typed blocks, e.g. [{'type': 'reasoning', ...}, {'type': 'text', 'text': '...'}].
    Downstream agents expect response.content to be a string. This extracts
    and joins the text blocks, discarding reasoning/metadata blocks.
    """
    content = response.content
    if isinstance(content, list):
        texts = [
            item.get("text", "") if isinstance(item, dict) and item.get("type") == "text"
            else item if isinstance(item, str) else ""
            for item in content
        ]
        response.content = "\n".join(t for t in texts if t)
    return response


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        self.model = model
        self.base_url = base_url
        self.kwargs = kwargs

    def get_provider_name(self) -> str:
        """Return the provider name used in warning messages."""
        provider = getattr(self, "provider", None)
        if provider:
            return str(provider)
        return self.__class__.__name__.removesuffix("Client").lower()

    def warn_if_unknown_model(self) -> None:
        """Warn when the model is outside the known list for the provider."""
        if self.validate_model():
            return

        warnings.warn(
            (
                f"Model '{self.model}' is not in the known model list for "
                f"provider '{self.get_provider_name()}'. Continuing anyway."
            ),
            RuntimeWarning,
            stacklevel=2,
        )

    @abstractmethod
    def get_llm(self) -> Any:
        """Return the configured LLM instance."""
        pass

    @abstractmethod
    def validate_model(self) -> bool:
        """Validate that the model is supported by this client."""
        pass


def with_rate_limit_retry(
    func: Callable[..., Any],
    *args,
    retries: int = 5,
    base_backoff: float = 1.0,
    max_backoff: float = 60.0,
    **kwargs,
) -> Any:
    """Call `func` with exponential backoff retry on rate-limit errors.

    This is a lightweight, dependency-free retry helper that treats HTTP
    429 responses and common rate-limit messages as retriable. It adds a
    small jitter to avoid thundering-herd restarts.
    """
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            attempt += 1

            # Heuristics for retriable errors
            retriable = False
            msg = str(e).lower()
            status = getattr(e, "status_code", None) or getattr(e, "http_status", None)
            if status == 429:
                retriable = True
            if "too many requests" in msg or "rate limit" in msg or "rate_limit" in msg:
                retriable = True
            if e.__class__.__name__.lower().startswith("rate"):
                retriable = True

            if not retriable or attempt > retries:
                raise

            backoff = min(max_backoff, base_backoff * (2 ** (attempt - 1)))
            jitter = random.uniform(0, backoff * 0.1)
            sleep_time = backoff + jitter
            time.sleep(sleep_time)
