"""Integration module for Anthropic AI models through AI Gateway."""

import abc
from copy import deepcopy
from typing import Any, Literal

from anthropic import AsyncAnthropic
from anthropic._streaming import ServerSentEvent, SSEBytesDecoder, SSEDecoder
from httpx import Request
from pydantic_ai.providers.anthropic import AnthropicProvider

from handy_utils.utils.ai_gateway import format_proxy_url, get_ai_gateway_headers, get_base_url

PromptCachingStrategy = Literal["last_4", "first_4", "last_4_exclude_last"] | None


class SSEDecoderAIGateway(SSEDecoder):
    """SSE decoder for Anthropic AIGateway.

    AI Gateway removes the "event" line from the SSE stream, so we need a custom decoder to handle this.
    """

    def decode(self, line: str) -> ServerSentEvent | None:
        """Decode a line from the SSE stream."""
        sse = super().decode(line)
        if sse and sse.event is None:
            sse._event = sse.json().get("type")
        return sse


class AsyncAnthropicAIGateway(AsyncAnthropic, abc.ABC):
    """Base Anthropic AI-Gateway client."""

    streaming_path_template: str
    non_streaming_path_template: str
    anthropic_version: str

    def __init__(
        self,
        *args: Any,
        base_url: str,
        prompt_caching_strategy: PromptCachingStrategy = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Anthropic AI-Gateway client."""
        self.prompt_caching_strategy = prompt_caching_strategy
        super().__init__(
            *args,
            base_url=base_url,
            default_headers=get_ai_gateway_headers(),
            api_key="NA",
            max_retries=0,
            **kwargs,
        )

    async def _prepare_options(self, options):
        """Prepare the options for the AI Gateway request."""
        options = deepcopy(options)
        options.url = self._adapt_url_path(options.url, options.json_data)
        options.json_data = self._adapt_request_body(options.json_data)
        return options

    def _adapt_url_path(self, url: str, request_body: Any) -> str:
        """Adapt the URL path for the AI Gateway request."""
        if request_body.get("stream", False):
            return self.streaming_path_template.format(model=request_body["model"])
        else:
            return self.non_streaming_path_template.format(model=request_body["model"])

    async def _prepare_request(self, request: Request) -> None:
        """Prepare the request for AI Gateway."""
        request = format_proxy_url(request)
        request.headers["anthropic_version"] = self.anthropic_version

    def _adapt_request_body(self, request_body: Any) -> Any:
        request_body.pop("stream", None)
        request_body.pop("model", None)
        for message in request_body["messages"]:
            if isinstance(message["content"], str):
                message["content"] = [{"type": "text", "text": message["content"]}]
        if self.prompt_caching_strategy:
            request_body["messages"] = self._add_prompt_caching_breakpoints(request_body["messages"])
        request_body["anthropic_version"] = self.anthropic_version
        return request_body

    def _add_prompt_caching_breakpoints(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add prompt caching breakpoints to the messages."""
        user_msgs = [msg for msg in messages if msg["role"] == "user"]
        if self.prompt_caching_strategy == "last_4":
            messages_iter = user_msgs[::-1]
        elif self.prompt_caching_strategy == "last_4_exclude_last":
            messages_iter = user_msgs[:-1][::-1]
        elif self.prompt_caching_strategy == "first_4":
            messages_iter = user_msgs
        else:
            raise ValueError(f"Unsupported prompt caching strategy: {self.prompt_caching_strategy}.")
        breakpoints_added = 0
        for msg in messages_iter:
            if msg["role"] == "user" and msg["content"]:
                msg["content"][-1]["cache_control"] = {"type": "ephemeral"}
                breakpoints_added += 1
                if breakpoints_added == 4:
                    break
        return messages

    def _make_sse_decoder(self) -> SSEDecoder | SSEBytesDecoder:
        return SSEDecoderAIGateway()


class AsyncAnthropicVertexAIGateway(AsyncAnthropicAIGateway):
    """Anthropic VertexAI AI-Gateway client."""

    streaming_path_template = "/publishers/anthropic/models/{model}:streamRawPredict"
    non_streaming_path_template = "/publishers/anthropic/models/{model}:rawPredict"
    anthropic_version = "vertex-2023-10-16"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Anthropic Vertex AI-Gateway client."""
        super().__init__(*args, base_url=get_base_url() + "/v1/google/v1", **kwargs)


class AsyncAnthropicBedrockAIGateway(AsyncAnthropicAIGateway):
    """Anthropic Bedrock AI-Gateway client."""

    streaming_path_template = "/model/{model}/invoke-with-response-stream"
    non_streaming_path_template = "/model/{model}/invoke"
    anthropic_version = "bedrock-2023-05-31"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Anthropic Vertex AI-Gateway client."""
        super().__init__(*args, base_url=get_base_url() + "/v1/bedrock", **kwargs)


class AnthropicAIGatewayProvider(AnthropicProvider):
    """Anthropic AIGateway provider."""

    def __init__(self, prompt_caching_strategy: PromptCachingStrategy = None) -> None:
        """Create a new Anthropic AI Gateway provider."""
        self._client = AsyncAnthropicVertexAIGateway(prompt_caching_strategy=prompt_caching_strategy)


class AnthropicAIGatewayBedrockProvider(AnthropicProvider):
    """Anthropic AIGateway provider."""

    def __init__(self, prompt_caching_strategy: PromptCachingStrategy = None) -> None:
        """Create a new Anthropic AI Gateway provider."""
        self._client = AsyncAnthropicBedrockAIGateway(prompt_caching_strategy=prompt_caching_strategy)
