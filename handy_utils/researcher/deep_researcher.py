from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.anthropic import AnthropicModel

from handy_utils.configuration import load_configuration
from handy_utils.researcher.prompts import JUNIOR_RESEARCHER_SYSTEM_PROMPT, LEAD_RESARCHER_SYSTEM_PROMPT
from handy_utils.utils.anthropic_provider import AnthropicAIGatewayProvider

provider = AnthropicAIGatewayProvider()
lg_model = AnthropicModel(provider=provider, model_name="claude-sonnet-4@20250514")
sm_model = AnthropicModel(provider=provider, model_name="claude-3-7-sonnet@20250219")
config = load_configuration()


lead_researcher = Agent(
    name="Lead Researcher",
    model=lg_model,
    system_prompt=LEAD_RESARCHER_SYSTEM_PROMPT,
)

junior_researcher = Agent(
    name="Junior Researcher",
    model=sm_model,
    system_prompt=JUNIOR_RESEARCHER_SYSTEM_PROMPT,
    mcp_servers=[
        MCPServerStdio(
            "uvx",
            args=[
                "--from",
                "atlassian-code-navigator-mcp",
                "code-navigator-mcp",
                "--email",
                "avempali@atlassian.com",
                "--api-key",
                config.confluence_api_key,
            ],
        ),
        MCPServerStdio(
            "uvx",
            args=[
                "--from",
                "atlassian-mcp-scout",
                "scout",
            ],
        ),
    ],
)


@lead_researcher.tool
async def delegate_research_task(ctx: RunContext[None], task: str) -> str:
    """Delegate a research task to a junior researcher."""
    response = await junior_researcher.run(task)
    return response.output


async def run_lead_researcher(query: str) -> str:
    """Run the lead researcher agent with the given query."""
    async with lead_researcher.run_mcp_servers(), junior_researcher.run_mcp_servers():
        response = await lead_researcher.run(query)
    return response.output
