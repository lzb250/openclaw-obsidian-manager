import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts.config import load_config


def _run_git(vault_path: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(vault_path),
        capture_output=True,
        text=True,
    )


def init_repo(vault_path: Path, remote: str, branch: str) -> None:
    if not (vault_path / ".git").exists():
        _run_git(vault_path, ["init"])
        _run_git(vault_path, ["checkout", "-b", branch])
        _run_git(vault_path, ["remote", "add", "origin", remote])
        _run_git(vault_path, ["add", "-A"])
        _run_git(vault_path, ["commit", "-m", "init: initial vault commit"])
        print(f"Initialized git repo at {vault_path}")


def run_sync(config: dict) -> bool:
    vault_path = Path(config["vault"]["path"])
    remote = config["git"]["remote"]
    branch = config["git"]["branch"]

    if not vault_path.exists():
        print(f"Vault path not found: {vault_path}", file=sys.stderr)
        return False

    init_repo(vault_path, remote, branch)

    # Pull (conflicts keep local)
    pull_result = _run_git(vault_path, ["pull", "--rebase", "-X", "theirs", "origin", branch])
    if pull_result.returncode != 0:
        print(f"Pull failed: {pull_result.stderr.strip()}", file=sys.stderr)

    # Stage all changes
    _run_git(vault_path, ["add", "-A"])

    # Check if there are staged changes
    diff_result = _run_git(vault_path, ["diff", "--cached", "--quiet"])
    if diff_result.returncode == 0:
        print("No changes to sync.")
        return True

    # Commit
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"auto: sync {now}"
    commit_result = _run_git(vault_path, ["commit", "-m", commit_msg])
    if commit_result.returncode != 0:
        print(f"Commit failed: {commit_result.stderr.strip()}", file=sys.stderr)
        return False

    # Push
    push_result = _run_git(vault_path, ["push", "origin", branch])
    if push_result.returncode != 0:
        print(f"Push failed (network?): {push_result.stderr.strip()}", file=sys.stderr)
        return False

    print(f"Synced: {commit_msg}")
    return True
