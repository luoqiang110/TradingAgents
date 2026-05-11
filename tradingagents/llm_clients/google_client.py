from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from .base_client import BaseLLMClient, normalize_content, with_rate_limit_retry
from .validators import validate_model


class NormalizedChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI with normalized content output.

    Gemini 3 models return content as list of typed blocks.
    This normalizes to string for consistent downstream handling.
    """

    def invoke(self, input, config=None, **kwargs):
        # Wrap provider call with retry on rate-limit errors
        response = with_rate_limit_retry(super().invoke, input, config, **kwargs)
        return normalize_content(response)

    def _get_request_payload(self, input_, *, stop=None, **kwargs):
        """Defensive payload preparation: remove `tool_calls` if no tool messages.

        Some Google provider integrations require tool messages to accompany
        any assistant `tool_calls`. If none are present in the serialized
        payload, remove `tool_calls` from assistant message dicts to avoid
        provider-side validation errors.
        """
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        outgoing = payload.get("messages", [])

        has_tool_messages = any(
            isinstance(m, dict) and (
                m.get("role") == "tool" or "tool_outputs" in m or m.get("type") == "tool"
            )
            for m in outgoing
        )

        if not has_tool_messages:
            for message_dict in outgoing:
                if isinstance(message_dict, dict) and message_dict.get("tool_calls"):
                    message_dict.pop("tool_calls", None)

        return payload


class GoogleClient(BaseLLMClient):
    """Client for Google Gemini models."""

    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(model, base_url, **kwargs)

    def get_llm(self) -> Any:
        """Return configured ChatGoogleGenerativeAI instance."""
        self.warn_if_unknown_model()
        llm_kwargs = {"model": self.model}

        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in ("timeout", "max_retries", "callbacks", "http_client", "http_async_client"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        # Unified api_key maps to provider-specific google_api_key
        google_api_key = self.kwargs.get("api_key") or self.kwargs.get("google_api_key")
        if google_api_key:
            llm_kwargs["google_api_key"] = google_api_key

        # Map thinking_level to appropriate API param based on model
        # Gemini 3 Pro: low, high
        # Gemini 3 Flash: minimal, low, medium, high
        # Gemini 2.5: thinking_budget (0=disable, -1=dynamic)
        thinking_level = self.kwargs.get("thinking_level")
        if thinking_level:
            model_lower = self.model.lower()
            if "gemini-3" in model_lower:
                # Gemini 3 Pro doesn't support "minimal", use "low" instead
                if "pro" in model_lower and thinking_level == "minimal":
                    thinking_level = "low"
                llm_kwargs["thinking_level"] = thinking_level
            else:
                # Gemini 2.5: map to thinking_budget
                llm_kwargs["thinking_budget"] = -1 if thinking_level == "high" else 0

        return NormalizedChatGoogleGenerativeAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for Google."""
        return validate_model("google", self.model)
