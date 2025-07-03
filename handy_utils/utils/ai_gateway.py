"""AI Gateway utilities."""

import base64
import os
import subprocess
from urllib.parse import unquote
import json

from diskcache import Cache
from httpx import URL, Request
from pathlib import Path

CACHE_DIR = Path.home() / ".handy_utils" / "cache"
cache = Cache(CACHE_DIR / "slauth_token")

# Load configuration environment variables
LLM_CACHING = os.getenv("LLM_CACHING", "false").lower() in ["true", "1", "yes"]
MANUAL_TOOL_USE = os.getenv("MANUAL_TOOL_USE", "false").lower() in ["true", "1", "yes"]
AUTH_METHOD = os.getenv("AUTH_METHOD", "slauth")
LANYARD_CONFIG_ID = os.getenv("LANYARD_CONFIG_ID")
USE_CASE_ID = os.getenv("USE_CASE_ID", "autofix-service-internal")
CLOUD_ID = os.getenv("CLOUD_ID", "autofix-test")
USER_EMAIL = os.getenv("USER_EMAIL", "")
USER_API_TOKEN = os.getenv("USER_API_TOKEN", "")
PIPELINES_JWT_TOKEN = os.getenv("PIPELINES_JWT_TOKEN", "")
MESH_DEPENDENCY_AI_GATEWAY_BASE_URL = os.getenv("MESH_DEPENDENCY_AI_GATEWAY_BASE_URL")
CI = os.getenv("CI", "false").lower() in ["true", "1", "yes"]
AI_GATEWAY_BASE_URL = "https://ai-gateway.us-east-1.staging.atl-paas.net"
AI_GATEWAY_BASE_URL_LANYARD = "http://localhost:3496/ai-gateway.us-east-1.staging.atl-paas.net"
AI_GATEWAY_HEADERS = None
if headers_str := os.getenv("AI_GATEWAY_HEADERS"):
    AI_GATEWAY_HEADERS = json.loads(headers_str)


@cache.memoize(expire=60 * 40)
def generate_ai_gateway_token() -> str:
    """Use the Atlas CLI to generate a new slauth token.

    Tokens are cached for 40 minutes before being refreshed

    Returns:
        str: The generated token for AI Gateway authentication.
    """
    token_result = subprocess.run(
        "atlas slauth token --aud=ai-gateway --env=staging --groups=atlassian-all --ttl 60m",
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    return token_result.stdout.strip()


def get_base_url() -> str:
    """Get the base URL for AI Gateway.

    Returns:
        str: The base URL for AI Gateway.
    """
    if MESH_DEPENDENCY_AI_GATEWAY_BASE_URL:
        return MESH_DEPENDENCY_AI_GATEWAY_BASE_URL

    if AUTH_METHOD == "slauth":
        return AI_GATEWAY_BASE_URL
    elif AUTH_METHOD == "pipelines" and PIPELINES_JWT_TOKEN:
        return AI_GATEWAY_BASE_URL
    elif AUTH_METHOD == "lanyard":
        return AI_GATEWAY_BASE_URL_LANYARD
    else:
        raise ValueError(
            f"Unsupported auth method: {AUTH_METHOD}. Supported methods are: slauth, pipelines, api_token, lanyard."
        )


def get_ai_gateway_headers() -> dict[str, str]:
    """Get the LLM client configuration for the given model ID.

    Returns:
        AI Gateway headers.
    """

    headers = {}
    if AI_GATEWAY_HEADERS:
        headers = AI_GATEWAY_HEADERS
    elif MESH_DEPENDENCY_AI_GATEWAY_BASE_URL:
        headers = {
            "X-Atlassian-CloudId": "a436116f-02ce-4520-8fbb-7301462a1674",
            "X-Atlassian-UserId": "autofix-bot",
            "X-Atlassian-UseCaseId": "autofix-service-evaluation",
            "X-Slauth-Egress": "true",
        }
    elif AUTH_METHOD == "pipelines" and PIPELINES_JWT_TOKEN:
        headers = {
            "X-Atlassian-CloudId": "a436116f-02ce-4520-8fbb-7301462a1674",
            "X-Atlassian-UserId": "autofix-bot",
            "X-Atlassian-UseCaseId": USE_CASE_ID,
            "Authorization": "Bearer " + PIPELINES_JWT_TOKEN,
        }
    elif AUTH_METHOD == "lanyard":
        headers = {
            "X-Atlassian-CloudId": CLOUD_ID,
            "X-Atlassian-UserId": os.environ["USER"],
            "X-Atlassian-UseCaseId": USE_CASE_ID,
            "Lanyard-Config": LANYARD_CONFIG_ID or "",
        }
    elif AUTH_METHOD == "slauth":
        headers = {
            "X-Atlassian-CloudId": CLOUD_ID,
            "X-Atlassian-UserId": os.environ["USER"],
            "X-Atlassian-UseCaseId": USE_CASE_ID,
            "Authorization": "SLAUTH " + generate_ai_gateway_token(),
        }
    elif AUTH_METHOD == "api_token":
        encoded_token = base64.b64encode(f"{USER_EMAIL}:{USER_API_TOKEN}".encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": "Basic " + encoded_token,
            "X-Atlassian-EncodedToken": encoded_token,
        }
    else:
        raise ValueError(
            f"Unsupported auth method: {AUTH_METHOD}. Supported methods are: slauth, pipelines, api_token, lanyard."
        )
    return headers


def format_proxy_url(request: Request) -> Request:
    """Format the proxy URL for our AI Gateway proxy.

    Args:
        url: URL to format.

    Returns:
        The request object with an updated URL.
    """
    url = unquote(str(request.url))
    request.url = URL(url.replace("projects/NA/locations/NA/", ""))
    return request
