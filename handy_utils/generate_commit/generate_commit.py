"""Generate a commit message for the changes."""

import subprocess
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from handy_utils.configuration import load_configuration
from handy_utils.generate_commit.prompts import CONVENTIONAL_COMMIT_SPEC, PROMPT
from handy_utils.utils.unified_provider import UnifiedProvider

config = load_configuration()
model = OpenAIModel("gemini-2.5-flash", provider=UnifiedProvider())


class ConventionalCommitMessage(BaseModel):
    type: str = Field(description="The type of the commit message")
    description: str = Field(description="The description of the commit message", default="")
    body: str = Field(description="The body of the commit message", default="")
    footer: str = Field(description="The footer of the commit message", default="")
    jira_ticket: str | None = Field(
        default=None, description="The Jira ticket number to be included in the commit message"
    )

    @field_validator("type")
    def commit_type_validator(cls, value: str) -> str:
        """Validate the commit type."""
        valid_types = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore"]
        if value not in valid_types:
            raise ValueError(f"Invalid commit type: {value}. Must be one of {valid_types}.")
        return value

    @field_validator("description")
    def description_validator(cls, value: str) -> str:
        """Validate the description length."""
        if len(value) > 100:
            raise ValueError("Description too long, must be less than 100 characters.")
        return value

    def __str__(self) -> str:
        scope = f"({self.jira_ticket})" if self.jira_ticket else ""
        commit_message_tpl = "{type}{scope}: {description}\n{body}\n\n{footer}"
        return commit_message_tpl.format(
            type=self.type,
            scope=scope,
            description=self.description,
            body=self.body,
            footer=self.footer,
        )


class CommitMessageInput(BaseModel):
    changes: str = Field(description="The changes to be committed")
    jira_ticket: str | None = Field(
        default=None, description="The Jira ticket number to be included in the commit message"
    )
    additional_message: str | None = Field(
        default=None, description="An additional message to be included in the commit message"
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to set changes if not provided."""
        if self.additional_message is not None:
            self.additional_message = (
                "<additional_message>\n" + (self.additional_message or "") + "\n</additional_message>"
            )

    @field_validator("changes")
    def changes_validator(cls, value: str) -> str:
        """Validate the changes."""
        if not value.strip():
            raise ValueError("Changes cannot be empty.")
        return value


commit_message_gen_agent = Agent(
    model=model,
    deps_type=CommitMessageInput,
    output_type=ConventionalCommitMessage,
)


@commit_message_gen_agent.instructions
def system_prompt(ctx: RunContext[CommitMessageInput]) -> str:
    return PROMPT.format(
        changes=ctx.deps.changes,
        additional_message=ctx.deps.additional_message or "",
        conventional_commit_spec=CONVENTIONAL_COMMIT_SPEC,
    )


def get_changes() -> str:
    """Get the changes to be committed."""
    return subprocess.check_output(["git", "diff", "--cached"]).decode("utf-8")


def generate_llm_commit_message(jira_ticket: str | None = None, additional_message: str | None = None) -> str:
    """Generate a commit message for the changes."""
    response = commit_message_gen_agent.run_sync(
        "begin!",
        deps=CommitMessageInput(
            changes=get_changes(),
            jira_ticket=jira_ticket,
            additional_message=additional_message,
        ),
    ).output
    if jira_ticket:
        response.jira_ticket = jira_ticket
    return str(response)


def perform_commit(commit_message):
    """Perform the commit."""
    subprocess.run(["git", "commit", "-m", commit_message])
