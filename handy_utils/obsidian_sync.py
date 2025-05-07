import os
import subprocess
from datetime import datetime

DEFAULT_COMMIT_MESSAGE = f"Sync: Auto-committed changes at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def sync_git_repo(repo_path: str, commit_msg: str | None = None):
    """
    Checks for unstaged changes in the git repository at `repo_path`,
    stages all changes, and commits them with `commit_msg`.
    """
    if commit_msg is None:
        commit_msg = DEFAULT_COMMIT_MESSAGE
    success = False
    print(f"Syncing git repo at {repo_path}")
    if not os.path.isdir(repo_path):
        print(f"Error: Repository path '{repo_path}' is not a valid directory.")
        return

    try:
        # Check for unstaged changes. Output is empty if no changes.
        # `git -C <path>` runs git as if it was started in <path>
        status_cmd = ["git", "-C", repo_path, "status", "--porcelain"]
        status_res = subprocess.run(status_cmd, capture_output=True, text=True, check=False)

        if status_res.returncode != 0:
            # This handles cases like not being a git repo
            err_output = status_res.stderr.strip() if status_res.stderr else status_res.stdout.strip()
            print(f"Git status command failed for '{repo_path}'. Error: {err_output}")
            if "not a git repository" in err_output.lower():
                print(f"Please ensure '{repo_path}' is a valid git repository and has at least one commit.")
            return

        if not status_res.stdout.strip():
            print(f"No changes to commit in '{repo_path}'.")
            return

        print(f"Changes detected in '{repo_path}'. Staging and committing...")

        add_cmd = ["git", "-C", repo_path, "add", "-A"]
        subprocess.run(add_cmd, check=True, capture_output=True)  # check=True will raise on error

        commit_cmd = ["git", "-C", repo_path, "commit", "-m", commit_msg]
        subprocess.run(commit_cmd, check=True, capture_output=True)  # check=True will raise on error

        print(f"Successfully committed changes in '{repo_path}' with message: '{commit_msg}'.")

        push_cmd = ["git", "-C", repo_path, "push"]
        subprocess.run(push_cmd, check=True, capture_output=True)  # check=True will raise on error

        print(f"Successfully pushed changes in '{repo_path}'.")
        success = True
    except FileNotFoundError:
        print("Error: Git command not found. Ensure git is installed and in your system's PATH.")
    except subprocess.CalledProcessError as e:
        # This catches errors from add or commit if check=True is used and they fail
        error_output = e.stderr.strip() if e.stderr else e.stdout.strip()
        print(f"Git command failed for '{repo_path}'. Command: `{' '.join(e.cmd)}`. Error: {error_output}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return success


if __name__ == "__main__":
    sync_git_repo("/Users/avempali/Documents/personal/akhils-obsidian")
