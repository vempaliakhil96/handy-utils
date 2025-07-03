import json
import time

from httpx import AsyncClient, Request, Response
from pydantic_ai.providers.openai import OpenAIProvider

from handy_utils.utils.ai_gateway import get_ai_gateway_headers, get_base_url


class UnifiedProviderHttpClient(AsyncClient):
    """
    Unified AI Gateway HTTP Client,
    refer: https://developer.atlassian.com/platform/ai-gateway/rest/v2/api-group-v-/#api-v2-beta-chat-post
    """

    def __init__(self, *args, **kwargs):
        super().__init__(headers=get_ai_gateway_headers(), base_url=get_base_url(), *args, **kwargs)
        self.model = None

    def _prep_request(self, req: Request) -> Request:
        """Prepare modified request with unified gateway format"""
        payload = json.loads(req.content)
        self.model = payload.pop("model", None)
        headers = get_ai_gateway_headers() | {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        assert self.model is not None, "Model is required"
        self.platform_attrs = {
            "model": self.model,
        }

        return Request(
            method=req.method,
            url=get_base_url() + "/v2/beta/chat",
            headers=headers,
            json={"request_payload": payload, "platform_attributes": self.platform_attrs},
        )

    def _process_content(self, content: list) -> str | list:
        """Process response content list into string if it contains text type content"""
        if not content or not isinstance(content[0], dict):
            return content
        if content[0].get("type") != "text":
            raise ValueError(f"Unsupported content type: {content[0].get('type')}")
        return "\n\n".join(c["text"] for c in content)

    def _process_usage(self, platform_attrs: dict) -> dict:
        """Gets usage and returns as an OpenAI response compatible dict"""
        usage_dict = platform_attrs.get("metrics", {}).get("usage", {})
        return dict(
            usage=dict(
                total_tokens=usage_dict.get("total_tokens", 0),
                prompt_tokens=usage_dict.get("input_tokens", 0),
                completion_tokens=usage_dict.get("output_tokens", 0),
            )
        )

    def _prep_response(self, resp: Response, mod_req: Request) -> Response:
        """Prepare modified response in OpenAI format"""
        resp_data = json.loads(resp.content)
        payload = resp_data["response_payload"]

        # Process message content for each choice
        for choice in payload["choices"]:
            content = choice["message"].get("content", None)
            if content and isinstance(content, list):
                choice["message"]["content"] = self._process_content(content)

        return Response(
            status_code=resp.status_code,
            json={
                "created": int(time.time()),
                "model": self.model,
                **payload,
                **self._process_usage(resp_data.get("platform_attributes", {})),
            },
            headers=resp.headers,
            extensions=resp.extensions,
            request=mod_req,
        )

    async def send(self, request: Request, *args, **kwargs) -> Response:
        """Send request through unified gateway and process response"""
        mod_req = self._prep_request(request)
        resp = await super().send(mod_req, *args, **kwargs)
        assert resp.status_code == 200, (
            f"Unified AI Gateway Error, with status code {resp.status_code}, and content {resp.content!r}"
        )
        return self._prep_response(resp, mod_req)


class UnifiedProvider(OpenAIProvider):
    """Unified AI Gateway Provider"""

    @property
    def name(self) -> str:
        return "unified"

    def __init__(self, *args, **kwargs):
        super().__init__(
            api_key="NA",
            base_url="NA",
            http_client=UnifiedProviderHttpClient(timeout=900),
            *args,
            **kwargs,
        )
