"""Generate a commit message for the changes."""
import subprocess

from langchain_core.prompts import PromptTemplate

from handy_utils.configuration import load_configuration, load_llm


def get_changes():
    """Get the changes to be committed."""
    return subprocess.check_output(["git", "diff", "--cached"]).decode("utf-8")


def generate_llm_commit_message():
    """Generate a commit message for the changes."""
    config = load_configuration()
    llm = load_llm(config)
    changes = get_changes()
    prompt = PromptTemplate.from_template("Generate a commit message for the following changes: {changes}")
    chain = prompt | llm
    assert changes, "No changes to commit"
    commit_message = chain.invoke({"changes": changes}).content
    return commit_message


def perform_commit(commit_message):
    """Perform the commit."""
    subprocess.run(["git", "commit", "-m", commit_message])
