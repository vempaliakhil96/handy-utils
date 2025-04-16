"""Generate a commit message for the changes."""
import subprocess

from langchain_core.prompts import PromptTemplate

from handy_utils.configuration import load_configuration, load_llm
from handy_utils.generate_commit.prompts import CONVENTIONAL_COMMIT_SPEC, PROMPT, ADDITIONAL_JIRA_TICKET_PROMPT

def get_changes():
    """Get the changes to be committed."""
    return subprocess.check_output(["git", "diff", "--cached"]).decode("utf-8")


def generate_llm_commit_message(jira_ticket: str|None = None) -> str:
    """Generate a commit message for the changes."""
    config = load_configuration()
    llm = load_llm(config)
    changes = get_changes()
    prompt = PROMPT if jira_ticket is None else PROMPT + ADDITIONAL_JIRA_TICKET_PROMPT
    prompt_tpl = PromptTemplate.from_template(template=prompt)
    chain = prompt_tpl | llm
    assert changes, "No changes to commit"
    commit_message = chain.invoke({"changes": changes, "jira_ticket": jira_ticket, "conventional_commit_spec": CONVENTIONAL_COMMIT_SPEC}).content
    assert isinstance(commit_message, str), "Commit message is not a string"
    return commit_message

def perform_commit(commit_message):
    """Perform the commit."""
    subprocess.run(["git", "commit", "-m", commit_message])
