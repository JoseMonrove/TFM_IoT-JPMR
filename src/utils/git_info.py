# utils/git_info.py
import subprocess
import os

def get_git_commit() -> str:
    """
    SHA corto (7) del commit en la raíz del proyecto.
    """
    try:
        # __file__ → .../src/utils/git_info.py
        repo_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return sha
    except Exception:
        return "unknown"
