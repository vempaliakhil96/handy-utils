"""Generate a commit message for the changes."""
import subprocess

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from handy_utils.configuration import load_configuration, load_llm
from handy_utils.generate_commit.prompts import CONVENTIONAL_COMMIT_SPEC, PROMPT

class ConventionalCommitMessage(BaseModel):
    type: str = Field(description="The type of the commit message")
    description: str = Field(description="The description of the commit message", default="")
    body: str = Field(description="The body of the commit message", default="")
    footer: str = Field(description="The footer of the commit message", default="")

def get_changes():
    """Get the changes to be committed."""
    return subprocess.check_output(["git", "diff", "--cached"]).decode("utf-8")


def generate_llm_commit_message(jira_ticket: str|None = None) -> str:
    """Generate a commit message for the changes."""
    config = load_configuration()
    llm = load_llm(config)
    changes = get_changes()
    prompt = PROMPT if jira_ticket is None else PROMPT
    output_parser = JsonOutputParser(pydantic_object=ConventionalCommitMessage)
    prompt_tpl = PromptTemplate.from_template(template=prompt, partial_variables={"format_instructions": output_parser.get_format_instructions()})
    chain = prompt_tpl | llm | output_parser
    assert changes, "No changes to commit"
    commit_message = chain.invoke({"changes": changes, "jira_ticket": jira_ticket, "conventional_commit_spec": CONVENTIONAL_COMMIT_SPEC}).content
    assert isinstance(commit_message, dict), "Commit message is not a dictionary"
    commit_message_object = ConventionalCommitMessage(**commit_message)
    return build_commit_message(commit_message_object, jira_ticket)

def perform_commit(commit_message):
    """Perform the commit."""
    subprocess.run(["git", "commit", "-m", commit_message])

def build_commit_message(commit_message_object: ConventionalCommitMessage, jira_ticket: str|None = None) -> str:
    """Build the commit message."""
    scope = f"[{jira_ticket}]" if jira_ticket else ""
    commit_message_tpl = ("{type} {scope}: {description}"
                          "{body}"
                          "{footer}")
    return commit_message_tpl.format(type=commit_message_object.type, scope=scope, description=commit_message_object.description, body=commit_message_object.body, footer=commit_message_object.footer)
