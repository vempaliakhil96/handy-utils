"""Generate a commit message for the changes."""

import subprocess

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from handy_utils.configuration import load_configuration, load_langchain_llm
from handy_utils.generate_commit.prompts import CONVENTIONAL_COMMIT_SPEC, PROMPT

config = load_configuration()


class ConventionalCommitMessage(BaseModel):
    type: str = Field(description="The type of the commit message")
    description: str = Field(description="The description of the commit message", default="")
    body: str = Field(description="The body of the commit message", default="")
    footer: str = Field(description="The footer of the commit message", default="")


def get_changes() -> str:
    """Get the changes to be committed."""
    return subprocess.check_output(["git", "diff", "--cached"]).decode("utf-8")


def create_llm_chain() -> Runnable:
    llm = load_langchain_llm(config)
    output_parser = JsonOutputParser(pydantic_object=ConventionalCommitMessage)
    prompt_tpl = PromptTemplate.from_template(
        template=PROMPT,
        partial_variables={
            "format_instructions": output_parser.get_format_instructions(),
            "conventional_commit_spec": CONVENTIONAL_COMMIT_SPEC,
        },
    )
    chain = prompt_tpl | llm | output_parser
    return chain


def generate_llm_commit_message(jira_ticket: str | None = None, additional_message: str | None = None) -> str:
    """Generate a commit message for the changes."""
    changes = get_changes()
    additional_message = additional_message or ""
    chain = create_llm_chain()
    assert changes, "No changes to commit"
    if len(changes.splitlines()) > 500:
        print("Warning: Changes are too long to commit. trimming to 500 lines")
        changes = "\n".join(changes.splitlines()[:500])
    commit_message = chain.invoke(
        {
            "changes": changes,
            "additional_message": f"<additional_message>{additional_message}</additional_message>",
        }
    )
    assert isinstance(commit_message, dict), "Commit message is not a dictionary"
    commit_message_object = ConventionalCommitMessage(**commit_message)
    return build_commit_message(commit_message_object, jira_ticket)


def perform_commit(commit_message):
    """Perform the commit."""
    subprocess.run(["git", "commit", "-m", commit_message])


def build_commit_message(commit_message_object: ConventionalCommitMessage, jira_ticket: str | None = None) -> str:
    """Build the commit message."""
    scope = f"({jira_ticket})" if jira_ticket else ""
    commit_message_tpl = "{type}{scope}: {description}\n{body}\n\n{footer}"
    return commit_message_tpl.format(
        type=commit_message_object.type,
        scope=scope,
        description=commit_message_object.description,
        body=commit_message_object.body,
        footer=commit_message_object.footer,
    )
