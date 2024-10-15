from langchain_core.prompts import PromptTemplate
import subprocess
from handy_utils.configuration import load_configuration, load_llm


def get_changes():
    return subprocess.check_output(["git", "diff", "--cached"]).decode("utf-8")

def generate_commit(dry_run=False):
    config = load_configuration()
    llm = load_llm(config)
    changes = get_changes()
    prompt = PromptTemplate.from_template(
        "Generate a commit message for the following changes: {changes}"
    )
    chain = prompt | llm
    assert changes, "No changes to commit"
    commit_message = chain.invoke({"changes": changes})
    if dry_run:
        print(commit_message)
    else:
        perform_commit(commit_message)

def perform_commit(commit_message):
    subprocess.run(["git", "commit", "-m", commit_message])
