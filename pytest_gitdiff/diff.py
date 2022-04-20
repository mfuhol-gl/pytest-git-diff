import dataclasses
import datetime
import os
import subprocess
import tempfile
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import TypeVar

from git import GitCommandError
from git import Repo

from pytest_gitdiff.errors import InvalidGitRevision
from pytest_gitdiff.report import TestOutcome
from pytest_gitdiff.report import TestReport

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d")
REPO = Repo(os.getcwd())
GIT = REPO.git


T = TypeVar("T")


@dataclasses.dataclass
class DiffSummary:
    succeeded: Sequence[TestOutcome]
    failed: Sequence[TestOutcome]
    new: Sequence[TestOutcome]
    deleted: Sequence[TestOutcome]

    @classmethod
    def from_reports(cls, init: TestReport, cmp: TestReport):
        init_set = {test for test in init}
        cmp_set = {test for test in cmp}

        return cls(
            succeeded=[test for test in init.tests if test.passed],
            failed=[test for test in init.tests if not test.passed],
            new=list(cmp_set.difference(init_set)),
            deleted=list(init_set.difference(cmp_set)),
        )

    @property
    def degradated(self) -> bool:
        return len(self.failed) > 0


def run_pytest(*args: str, **opts: Any) -> TestReport:
    with tempfile.TemporaryDirectory(f"pytest-git-diff-{TIMESTAMP}") as tmp:
        json_file = os.path.join(tmp, "dump.json")
        subprocess.run(
            [
                "pytest",
                *args,
                "--json-report-file",
                json_file,
            ],
            **opts,
        )
        return TestReport.parse_file(json_file)


def checkout_rev(rev: str, force: bool = False) -> None:
    GIT.checkout(rev, force=force)


def run_at_rev(rev: str, callback: Callable[[], T]) -> T:
    old_rev = REPO.active_branch.name
    checkout_rev(rev)
    callback()
    checkout_rev(old_rev)


def ensure_rev_exists(revision: str) -> None:
    initial = REPO.active_branch.name
    try:
        checkout_rev(revision)
    except GitCommandError as err:
        raise InvalidGitRevision.from_revision(revision) from err
    finally:
        checkout_rev(initial)


def diff_revisions(
    pytest_args: List[str],
    init_rev: str,
    cmp_rev: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> DiffSummary:
    options = options or {}
    cmp_rev = cmp_rev or REPO.active_branch.name

    ensure_rev_exists(init_rev)
    if cmp_rev != REPO.active_branch.name:
        ensure_rev_exists(cmp_rev)

    init_report = run_at_rev(init_rev, lambda: run_pytest(*pytest_args, **options))
    cmp_report = run_at_rev(cmp_rev, lambda: run_pytest(*pytest_args, **options))
    diff = DiffSummary.from_reports(init_report, cmp_report)

    return diff
