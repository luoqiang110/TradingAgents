from typing import Any, Optional

from langchain_anthropic import ChatAnthropic

from .base_client import BaseLLMClient, normalize_content
from .validators import validate_model

_PASSTHROUGH_KWARGS = (
    "timeout", "max_retries", "api_key", "max_tokens",
    "callbacks", "http_client", "http_async_client", "effort",
)


class NormalizedChatAnthropic(ChatAnthropic):
    """ChatAnthropic with normalized content output.

    Claude models with extended thinking or tool use return content as a
    list of typed blocks. This normalizes to string for consistent
    downstream handling.
    """

    def invoke(self, input, config=None, **kwargs):
        return normalize_content(super().invoke(input, config, **kwargs))

    def _get_request_payload(self, input_, *, stop=None, **kwargs):
        """Defensive payload preparation: remove `tool_calls` if no tool messages.

        Some Anthropic integrations require that any assistant `tool_calls`
        are paired with corresponding tool messages in the serialized
        payload. If those tool messages are absent, providers can reject
        the request. Strip `tool_calls` from outgoing assistant message
        dicts when no tool messages are present.
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


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic Claude models."""

    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(model, base_url, **kwargs)

    def get_llm(self) -> Any:
        """Return configured ChatAnthropic instance."""
        self.warn_if_unknown_model()
        llm_kwargs = {"model": self.model}

        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return NormalizedChatAnthropic(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for Anthropic."""
        return validate_model("anthropic", self.model)
