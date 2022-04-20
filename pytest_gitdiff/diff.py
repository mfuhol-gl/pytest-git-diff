import datetime
import os
import subprocess
import tempfile
from typing import Dict
from typing import Optional

from git import GitCommandError
from git import Repo

from pytest_gitdiff.report import TestReport

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d")
REPO = Repo(os.getcwd())
GIT = REPO.git


def run_pytest(*args: str, options: Optional[Dict[str, str]] = None) -> TestReport:
    options = options or {}
    cmdline_opts = [item for k, v in options.items() for item in (f"--{k}", v)]
    with tempfile.TemporaryDirectory(f"pytest-git-diff-{TIMESTAMP}") as tmp:
        json_file = os.path.join(tmp, "dump.json")
        subprocess.run(
            ["pytest", *args, *cmdline_opts, "--json-report-file", json_file],
        )
        return TestReport.parse_file(json_file)


def verify_branch_exists(branch: str) -> None:
    initial = REPO.active_branch.name
    try:
        GIT.checkout(branch)
    except GitCommandError:
        pass
    finally:
        GIT.checkout(initial)
